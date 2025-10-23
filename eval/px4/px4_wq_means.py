# Evaluate scheduling overhead: Bao vs baremetal

import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import numpy as np

# Configuration
BENCHMARK_ORDER = [
    'control_allocator',
    'mc_rate_control',
    'pca9685_pwm_out',
    'flight_mode_manager',
    'mc_pos_control',
    'sensors'
]

def parse_workqueue_file(file_path):
    # Regular expression patterns
    run_pattern = re.compile(r'^>> Run (\d+)')
    wq_pattern = re.compile(r'^\|__ \d+\) (wq:\w+)')
    child_pattern = re.compile(
        r'^\|   [|\\]__ \d+\) (\w+)'          # Child name
        r'\s+\d+\.\d+ Hz'                     # Rate (ignored)
        r'\s+(\d+) us'                        # Interval
        r'(?:\s+\((\d+) us\))?'               # Expected interval (optional)
    )

    results = defaultdict(list)
    current_run = None
    current_block = None
    in_work_queue = False

    with open(file_path, 'r') as f:
        for line in f:
            line = line.rstrip()
            
            # Detect new runs
            run_match = run_pattern.match(line)
            if run_match:
                current_run = int(run_match.group(1))
                continue
                
            if not current_run:
                continue

            # Start new work queue block
            if line.startswith('Work Queue: 8  threads'):
                in_work_queue = True
                current_block = {
                    'work_queues': [],
                    'run_number': current_run
                }
                continue
                
            if not in_work_queue:
                continue

            # Match work queue lines
            wq_match = wq_pattern.match(line)
            if wq_match:
                current_wq = {
                    'name': wq_match.group(1),
                    'children': []
                }
                current_block['work_queues'].append(current_wq)
                continue

            # Match child entries
            if current_block and current_block['work_queues']:
                child_match = child_pattern.match(line)
                if child_match:
                    name = child_match.group(1)
                    interval = int(child_match.group(2))
                    expected = int(child_match.group(3)) if child_match.group(3) else interval
                    
                    current_block['work_queues'][-1]['children'].append({
                        'name': name,
                        'interval': interval,
                        'expected_interval': expected
                    })
                elif line.startswith('pxh>') or not line:
                    # End of work queue block
                    results[current_run].append(current_block)
                    current_block = None
                    in_work_queue = False

        # Add the last block if file doesn't end cleanly
        if current_block:
            results[current_run].append(current_block)

    return dict(results)

def process_case_data(parsed_data, case_name):
    """Process parsed data for a single case"""
    results = []
    
    for run_number, blocks in parsed_data.items():
        for block in blocks:
            for wq in block['work_queues']:
                for child in wq['children']:
                    if child['name'] in BENCHMARK_ORDER:
                        results.append({
                            'case': case_name,
                            'benchmark': child['name'],
                            'interval': child['interval'],
                            'expected': child['expected_interval']
                        })
    
    return pd.DataFrame(results)

# Process both cases
baremetal_df = process_case_data(
    parse_workqueue_file('px4-bare-wq-run.txt'),
    'Baremetal'
)

bao_df = process_case_data(
    parse_workqueue_file('px4-bao-wq-run.txt'),
    'Bao'
)

# Combine data
combined_df = pd.concat([baremetal_df, bao_df])

# Calculate statistics (version-safe approach)
stats = (combined_df.groupby(['case', 'benchmark'])['interval']
         .agg(['mean', 'sem'])
         .reset_index()
         .rename(columns={
             'mean': 'mean',
             'sem': 'sem'
         }))

# Convert to categorical for ordering
stats['benchmark'] = pd.Categorical(
    stats['benchmark'],
    categories=BENCHMARK_ORDER,
    ordered=True
)

# Modified plotting code with explicit case tracking
cases = ['Baremetal', 'Bao']
colors = sns.color_palette("pastel", n_colors=len(cases))

# Calculate x positions
N_BENCHMARKS = len(BENCHMARK_ORDER)
#SPACE_BETWEEN_GROUPS = 1.5
#SPACE_BETWEEN_GROUPS = 1
SPACE_BETWEEN_GROUPS = 0.8
BAR_WIDTH = 0.3

x = np.arange(N_BENCHMARKS) * SPACE_BETWEEN_GROUPS
baremetal_x = x - BAR_WIDTH/2
bao_x = x + BAR_WIDTH/2

# Create figure
plt.figure(figsize=(16, 8))
sns.set(style="whitegrid")
ax = plt.gca()

# Plot data with explicit case handling
for idx, case in enumerate(cases):
    case_stats = stats[stats['case'] == case].set_index('benchmark').reindex(BENCHMARK_ORDER)
    x_pos = baremetal_x if case == 'Baremetal' else bao_x
    
    bars = ax.bar(
        x_pos,
        case_stats['mean'],
        width=BAR_WIDTH,
        label=case,
        color=colors[idx],
        yerr=case_stats['sem'],
        capsize=5,
        error_kw={'elinewidth': 1.5, 'capthick': 1.5}
    )
    
    # Add annotations
    for i, (bench, (mean, sem)) in enumerate(zip(BENCHMARK_ORDER, case_stats[['mean', 'sem']].values)):
        if not pd.isna(mean):
            ax.text(
                x_pos[i], 
                mean + sem + (0.02 * mean),
                f'{mean:.0f} ± {sem:.1f}',
                ha='center', 
                va='bottom',
                fontsize=10
            )

# Configure plot
ax.set_title('Task Update Interval Comparison: Baremetal vs Bao', fontsize=14)
ax.set_xlabel('N=20; Q=18; 1Q @ 10sec', fontsize=12)
ax.set_ylabel('Mean Interval (μs)', fontsize=12)
ax.set_xticks(x)
ax.set_xticklabels(BENCHMARK_ORDER, rotation=0, ha='center', fontsize=11)
ax.legend()
ax.grid(True, axis='y', linestyle='--')

plt.tight_layout()
plt.show()

# 1. Prepare data with proper index handling
baremetal_stats = stats[stats['case'] == 'Baremetal'].set_index('benchmark').reindex(BENCHMARK_ORDER)
bao_stats = stats[stats['case'] == 'Bao'].set_index('benchmark').reindex(BENCHMARK_ORDER)

# 2. Calculate percentage overhead with proper indexing
overhead = pd.DataFrame({
    'benchmark': BENCHMARK_ORDER,
    'mean_pct': ((bao_stats['mean'].values - baremetal_stats['mean'].values) / 
                baremetal_stats['mean'].values * 100),
    'std_pct': np.sqrt(
        (bao_stats['sem'].values/bao_stats['mean'].values)**2 + 
        (baremetal_stats['sem'].values/baremetal_stats['mean'].values)**2
    ) * 100
}).set_index('benchmark')

# 3. Create plot with proper tick handling
plt.figure(figsize=(14, 7))
sns.set(style="whitegrid")
ax = plt.gca()

# Plot bars
bars = ax.bar(
    BENCHMARK_ORDER,
    overhead['mean_pct'],
    yerr=overhead['std_pct'],
    capsize=5,
    color='salmon'
)

# Set ticks and labels correctly
ax.set_xticks(range(len(BENCHMARK_ORDER)))
ax.set_xticklabels(
    [f"{bench}\n({baremetal_stats.loc[bench, 'mean']:.0f}μs)" 
     if not pd.isna(baremetal_stats.loc[bench, 'mean']) 
     else f"{bench}\n(N/A)" 
     for bench in BENCHMARK_ORDER],
    rotation=0, 
    ha='center'
)

# Add labels and styling
ax.set_title('Scheduling Performance Overhead: Bao vs Baremetal', fontsize=14)
ax.set_xlabel('N=20; Q=18; 1Q @ 10sec', fontsize=12)
ax.set_xlabel(None)
ax.set_ylabel('Scheduling Overhead (%)', fontsize=12)
ax.axhline(0, color='black', linewidth=0.5)

# Add value labels using position index
for i, (bench, row) in enumerate(overhead.iterrows()):
    if not pd.isna(row['mean_pct']):
        ax.text(
            i,
            # row['mean_pct'] + 1 if row['mean_pct'] > 0 else row['mean_pct'] - 2,
            -2.1,
            f"{row['mean_pct']:.1f}% ± {row['std_pct']:.1f}%",
            ha='center',
            # va='bottom' if row['mean_pct'] > 0 else 'top',
            va='center',
            fontsize=10
        )

plt.tight_layout()
plt.show()
