# Evaluate FPS performance degradation (Bao vs native)

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

# Load raw FPS data
bare_runs = parse_file("cam-fps-bare.txt") 
bao_runs = parse_file("cam-fps-bao.txt")

# Collect results for plotting
run_numbers = []
degradations = []
cis = []

for i, (bare_run, bao_run) in enumerate(zip(bare_runs, bao_runs), 1):
    bare_mean = np.mean(bare_run)
    bao_mean = np.mean(bao_run)
    degradation = ((bare_mean - bao_mean) / bare_mean) * 100
    
    # Calculate 95% confidence interval
    ci = 1.96 * np.sqrt(
        (np.std(bare_run, ddof=1)**2/len(bare_run)) + 
        (np.std(bao_run, ddof=1)**2/len(bao_run))
    ) * 100 / bare_mean
    
    run_numbers.append(i)
    degradations.append(degradation)
    cis.append(ci)

# Create the plot
plt.figure(figsize=(12, 6))
plt.bar(run_numbers, degradations, yerr=cis, capsize=10, color='orange', edgecolor='black')
# plt.axhline(0, color='red', linestyle='--')

# Add labels and title
plt.title('FPS Performance Degradation: Bao vs Native execution', fontsize=12)
plt.xlabel('Run', fontsize=12)
plt.ylabel('FPS Performance Degradation (%)', fontsize=12)
plt.xticks(run_numbers)
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Add value labels
for i, (deg, ci_val) in enumerate(zip(degradations, cis)):
    y = - 1.65
    if i % 2:
        y = 1.9
    plt.text(i+1, y , f'{deg:.1f}% ± {ci_val:.1f}%', 
             ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.show()
