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

# Process all cases
uspfs_df = process_case_data(
    parse_workqueue_file('px4-uspfs.log'),
    'USPFS'
)

sspfs_df = process_case_data(
    parse_workqueue_file('px4-sspfs.log'),
    'SSPFS'
)

sspfs_col_df = process_case_data(
    parse_workqueue_file('px4-sspfs-col.log'),
    'SSPFS+col'
)

# Combine data
combined_df = pd.concat([uspfs_df, sspfs_df, sspfs_col_df])

# Calculate statistics
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

# Modified plotting code for 3 cases
cases = ['USPFS', 'SSPFS', 'SSPFS+col']
colors = sns.color_palette("pastel", n_colors=len(cases))

# Calculate x positions dynamically
N_BENCHMARKS = len(BENCHMARK_ORDER)
BAR_WIDTH = 0.2
SPACE_BETWEEN_GROUPS = 0.8

x = np.arange(N_BENCHMARKS) * SPACE_BETWEEN_GROUPS
offsets = np.linspace(-BAR_WIDTH*(len(cases)-1)/2, BAR_WIDTH*(len(cases)-1)/2, len(cases))

# Create figure
plt.figure(figsize=(16, 8))
sns.set(style="whitegrid")
ax = plt.gca()

# Plot data with dynamic positioning
for idx, case in enumerate(cases):
    case_stats = stats[stats['case'] == case].set_index('benchmark').reindex(BENCHMARK_ORDER)
    x_pos = x + offsets[idx]
    
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
ax.set_title('Task Update Interval Comparison', fontsize=14)
ax.set_xlabel('N=20; Q=18; 1Q @ 10sec', fontsize=12)
ax.set_ylabel('Mean Interval (μs)', fontsize=12)
ax.set_xticks(x)
ax.set_xticklabels(BENCHMARK_ORDER, rotation=0, ha='center', fontsize=11)
ax.legend()
ax.grid(True, axis='y', linestyle='--')

plt.tight_layout()
plt.show()

# Overhead calculation and plotting
uspfs_stats = stats[stats['case'] == 'USPFS'].set_index('benchmark').reindex(BENCHMARK_ORDER)
sspfs_stats = stats[stats['case'] == 'SSPFS'].set_index('benchmark').reindex(BENCHMARK_ORDER)
sspfs_col_stats = stats[stats['case'] == 'SSPFS+col'].set_index('benchmark').reindex(BENCHMARK_ORDER)

# Calculate overhead for both comparisons
overhead_data = []
for bench in BENCHMARK_ORDER:
    # SSPFS vs USPFS
    if not pd.isna(uspfs_stats.loc[bench, 'mean']) and not pd.isna(sspfs_stats.loc[bench, 'mean']):
        mean_pct = ((sspfs_stats.loc[bench, 'mean'] - uspfs_stats.loc[bench, 'mean']) / 
                    uspfs_stats.loc[bench, 'mean'] * 100)
        sem_pct = np.sqrt(
            (sspfs_stats.loc[bench, 'sem']/sspfs_stats.loc[bench, 'mean'])**2 + 
            (uspfs_stats.loc[bench, 'sem']/uspfs_stats.loc[bench, 'mean'])**2
        ) * 100
        overhead_data.append({
            'benchmark': bench,
            'case': 'SSPFS',
            'mean_pct': mean_pct,
            'sem_pct': sem_pct
        })
    
    # SSPFS+col vs USPFS
    if not pd.isna(uspfs_stats.loc[bench, 'mean']) and not pd.isna(sspfs_col_stats.loc[bench, 'mean']):
        mean_pct_col = ((sspfs_col_stats.loc[bench, 'mean'] - uspfs_stats.loc[bench, 'mean']) / 
                       uspfs_stats.loc[bench, 'mean'] * 100)
        sem_pct_col = np.sqrt(
            (sspfs_col_stats.loc[bench, 'sem']/sspfs_col_stats.loc[bench, 'mean'])**2 + 
            (uspfs_stats.loc[bench, 'sem']/uspfs_stats.loc[bench, 'mean'])**2
        ) * 100
        overhead_data.append({
            'benchmark': bench,
            'case': 'SSPFS+col',
            'mean_pct': mean_pct_col,
            'sem_pct': sem_pct_col
        })

overhead = pd.DataFrame(overhead_data)

# Create overhead plot
plt.figure(figsize=(14, 7))
sns.set(style="whitegrid")
ax = plt.gca()

BAR_WIDTH_OVERHEAD = 0.35
x = np.arange(len(BENCHMARK_ORDER)) * 1.5  # Increased spacing for clarity

# Plot each comparison
for i, bench in enumerate(BENCHMARK_ORDER):
    bench_data = overhead[overhead['benchmark'] == bench]
    
    # Plot SSPFS overhead
    sspfs_data = bench_data[bench_data['case'] == 'SSPFS']
    if not sspfs_data.empty:
        ax.bar(x[i] - BAR_WIDTH_OVERHEAD/2, 
              sspfs_data['mean_pct'].values[0], 
              BAR_WIDTH_OVERHEAD,
              yerr=sspfs_data['sem_pct'].values[0],
              color='tab:blue',
              capsize=5,
              label='SSPFS' if i == 0 else "")
    
    # Plot SSPFS+col overhead
    sspfs_col_data = bench_data[bench_data['case'] == 'SSPFS+col']
    if not sspfs_col_data.empty:
        ax.bar(x[i] + BAR_WIDTH_OVERHEAD/2, 
              sspfs_col_data['mean_pct'].values[0], 
              BAR_WIDTH_OVERHEAD,
              yerr=sspfs_col_data['sem_pct'].values[0],
              color='tab:orange',
              capsize=5,
              label='SSPFS+col' if i == 0 else "")

# Configure plot
ax.set_title('Scheduling Overhead Comparison', fontsize=14)
ax.set_ylabel('Relative Scheduling Overhead (%)', fontsize=12)
ax.set_xticks(x)
ax.set_xticklabels(
    [f"{bench}\n({uspfs_stats.loc[bench, 'mean']:.0f}μs)" 
     for bench in BENCHMARK_ORDER],
    rotation=0,
    ha='center'
)
ax.axhline(0, color='black', linewidth=0.8)
ax.set_yticks(np.arange(-16,2,2))
ax.legend()

# Add value labels
for i, bench in enumerate(BENCHMARK_ORDER):
    bench_data = overhead[overhead['benchmark'] == bench]
    for case in ['SSPFS', 'SSPFS+col']:
        case_data = bench_data[bench_data['case'] == case]
        if not case_data.empty:
            y_pos = -15.9
            if case == 'SSPFS':
                y_pos += 0.4
            # if case_data['mean_pct'].values[0] < 0:
            #     y_pos = -15.5
            # else:
            #     y_pos = 0.9
            x_pos = x[i] - BAR_WIDTH_OVERHEAD/2 if case == 'SSPFS' else x[i] + BAR_WIDTH_OVERHEAD/2
            # y_pos = case_data['mean_pct'].values[0] + case_data['sem_pct'].values[0] + 1
            ax.text(x_pos, y_pos, 
                   f"{case_data['mean_pct'].values[0]:.1f}% ± {case_data['sem_pct'].values[0]:.1f}%",
                   ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.show()
