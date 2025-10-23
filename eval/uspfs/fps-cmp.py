import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

def parse_file(filename):
    """Parse log file and return list of all FPS values per run"""
    runs = []
    current_run = []
    
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith(">> TEST ->"):
                if current_run:
                    runs.append(current_run)
                    current_run = []
                continue
                
            if 'current: ' in line:
                fps = float(line.split('current: ')[1].split(',')[0])
                current_run.append(fps)
    
    if current_run:
        runs.append(current_run)
    
    return runs

# Load raw FPS data for all configurations
uspfs_runs = parse_file("cam-uspfs.log")    # Baseline
sspfs_runs = parse_file("cam-sspfs.log")
sspfs_col_runs = parse_file("cam-sspfs-col.log")

# Verify equal number of runs
print(f"Runs: USPFS = {len(uspfs_runs)} | SSPFS = {len(sspfs_runs)} | SSPFS+COL = {len(sspfs_col_runs)}")
n_runs = len(uspfs_runs)
assert len(sspfs_runs) == n_runs, "Mismatched number of runs between USPFS and SSPFS"
assert len(sspfs_col_runs) == n_runs, "Mismatched number of runs between USPFS and SSPFS+col"

# Collect results for plotting
run_numbers = []
degradations_sspfs = []
degradations_col = []
cis_sspfs = []
cis_col = []

for i in range(n_runs):
    uspfs_data = uspfs_runs[i]
    sspfs_data = sspfs_runs[i]
    sspfs_col_data = sspfs_col_runs[i]
    
    # Calculate baseline mean
    uspfs_mean = np.mean(uspfs_data)
    
    # SSPFS vs USPFS
    sspfs_mean = np.mean(sspfs_data)
    degradation_sspfs = ((uspfs_mean - sspfs_mean) / uspfs_mean) * 100
    ci_sspfs = 1.96 * np.sqrt(
        (np.std(uspfs_data, ddof=1)**2/len(uspfs_data)) + 
        (np.std(sspfs_data, ddof=1)**2/len(sspfs_data))
    ) * 100 / uspfs_mean
    
    # SSPFS+col vs USPFS
    sspfs_col_mean = np.mean(sspfs_col_data)
    degradation_col = ((uspfs_mean - sspfs_col_mean) / uspfs_mean) * 100
    ci_col = 1.96 * np.sqrt(
        (np.std(uspfs_data, ddof=1)**2/len(uspfs_data)) + 
        (np.std(sspfs_col_data, ddof=1)**2/len(sspfs_col_data))
    ) * 100 / uspfs_mean
    
    run_numbers.append(i+1)
    degradations_sspfs.append(degradation_sspfs)
    degradations_col.append(degradation_col)
    cis_sspfs.append(ci_sspfs)
    cis_col.append(ci_col)

# Plot parameters
BAR_WIDTH = 0.35
x = np.arange(n_runs)

# Create the plot
plt.figure(figsize=(14, 7))
ax = plt.gca()

# Plot bars for both configurations
bars_sspfs = ax.bar(x - BAR_WIDTH/2, degradations_sspfs, BAR_WIDTH,
                   yerr=cis_sspfs, capsize=5, color='tab:blue',
                   label='SSPFS', edgecolor='black')

bars_col = ax.bar(x + BAR_WIDTH/2, degradations_col, BAR_WIDTH,
                 yerr=cis_col, capsize=5, color='tab:orange',
                 label='SSPFS+col', edgecolor='black')

# Formatting
ax.set_title('FPS Performance Degradation: SSPFS Configurations vs USPFS Baseline', fontsize=14)
ax.set_xlabel('Run Number', fontsize=12)
ax.set_ylabel('Performance Degradation (%)', fontsize=12)
ax.set_xticks(x)
ax.set_xticklabels(run_numbers)
ax.set_yticks(np.arange(-44,2,2))
# ax.grid(axis='y', linestyle='--', alpha=0.7)
ax.axhline(0, color='black', linewidth=0.8)
ax.legend()

# Add value labels
for i, (deg_sspfs, ci_sspfs, deg_col, ci_col) in enumerate(zip(degradations_sspfs, cis_sspfs,
                                                              degradations_col, cis_col)):
    y = -42.2
    # SSPFS labels
    ax.text(x[i] - BAR_WIDTH/2,
            y, 
           f'{deg_sspfs:.1f} ± {ci_sspfs:.1f}',
           ha='center', va='bottom', fontsize=9, rotation=90)
    
    # SSPFS+col labels
    ax.text(x[i] + BAR_WIDTH/2,
           y, 
           f'{deg_col:.1f} ± {ci_col:.1f}',
           ha='center', va='bottom', fontsize=9, rotation=90)

plt.tight_layout()
plt.show()
