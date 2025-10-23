import pyulog
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import os
import pandas as pd
from scipy import stats
import glob

# Configuration
UNSUPERVISED_LOGS = glob.glob('uspfs/*.ulg')
SUPERVISED_LOGS = glob.glob('sspfs/*.ulg')
print(f"Found {len(UNSUPERVISED_LOGS)} unsupervised logs")
print(f"Found {len(SUPERVISED_LOGS)} supervised logs")

# Battery parameters for HoverGames 3S1P battery
TOTAL_ENERGY_WH = 55.5  # 55.5 Wh total capacity
NOMINAL_VOLTAGE = 11.1   # 11.1V nominal voltage

# Battery validation thresholds
MIN_ENERGY_THRESHOLD = 0.1  # Minimum valid energy consumption (Wh)
BATTERY_CHANGE_THRESHOLD = 0.01  # Minimum battery percentage change (1%)

# We want to highlight different flight phases and normalize data with N points
N_POINTS = 1000
PHASES = {'Takeoff': (0, 15), 'Cruise': (15, 85), 'Landing': (85, 100)}
COLORS = {'USPFS': '#1f77b4', 'SSPFS': '#ff7f0e'}

# Statistical parameters
CONFIDENCE_LEVEL = 0.95
ALPHA = 0.05

def process_group(log_files, group_name):
    """Process a group of logs and return normalized data"""
    common_time = np.linspace(0, 100, N_POINTS)
    data = {
        'x_actual': [], 'x_setpoint': [],
        'y_actual': [], 'y_setpoint': [],
        'z_actual': [], 'z_setpoint': [],
        'cpu': [], 'ram': [],
        'energy_wh': []  # Energy consumed in Watt-hours
    }
    
    print(f"\nProcessing {group_name} logs:")
    for i, log_file in enumerate(log_files):
        try:
            print(f"  [{i+1}/{len(log_files)}] Processing {os.path.basename(log_file)}")
            ulog = pyulog.ULog(log_file)
            
            # Get position data
            pos_data = ulog.get_dataset('vehicle_local_position').data
            t_raw = (pos_data['timestamp'] - pos_data['timestamp'][0]) / 1e6
            if len(t_raw) == 0:
                print("    - Skipping: No position data")
                continue
                
            t_norm = t_raw / t_raw[-1] * 100
            
            # Get setpoints
            try:
                sp_data = ulog.get_dataset('vehicle_local_position_setpoint').data
                t_sp = (sp_data['timestamp'] - pos_data['timestamp'][0]) / 1e6
                t_sp_norm = t_sp / t_raw[-1] * 100
            except:
                sp_data = None
                print("    - Warning: No setpoint data")
                
            # Get CPU/RAM data
            try:
                cpu_data = ulog.get_dataset('cpuload').data
                t_cpu = (cpu_data['timestamp'] - pos_data['timestamp'][0]) / 1e6
                t_cpu_norm = t_cpu / t_raw[-1] * 100
            except:
                cpu_data = None
                print("    - Warning: No CPU/RAM data")
            
            # Energy analysis using battery percentage
            energy_wh = None
            try:
                battery_data = ulog.get_dataset('battery_status').data
                t_bat = (battery_data['timestamp'] - pos_data['timestamp'][0]) / 1e6
                t_bat_norm = t_bat / t_raw[-1] * 100
                
                if 'remaining' not in battery_data or len(t_bat) < 2:
                    print("    - Warning: Insufficient battery data")
                    energy_wh = None
                else:
                    remaining = battery_data['remaining']
                    
                    # Check if battery percentage actually changes
                    battery_range = np.max(remaining) - np.min(remaining)
                    if battery_range < BATTERY_CHANGE_THRESHOLD:
                        print("    - Warning: Battery percentage unchanged (delta: {:.3f})".format(battery_range))
                        energy_wh = None
                    else:
                        # Calculate energy consumed
                        energy_wh = (1 - remaining) * TOTAL_ENERGY_WH
                        
                        # Validate minimum energy consumption
                        if energy_wh[-1] < MIN_ENERGY_THRESHOLD:
                            print(f"    - Warning: Low energy consumption ({energy_wh[-1]:.4f}Wh)")
                            energy_wh = None
                        else:
                            print(f"    - Energy consumed: {energy_wh[-1]:.2f} Wh")
            except Exception as e:
                print(f"    - Battery processing error: {str(e)}")
                energy_wh = None
            
            # Interpolate to common time base
            for axis in ['x', 'y', 'z']:
                # Actual position
                if len(t_norm) > 1:
                    f_actual = interp1d(t_norm, pos_data[axis], bounds_error=False, fill_value="extrapolate")
                    data[f'{axis}_actual'].append(f_actual(common_time))
                else:
                    data[f'{axis}_actual'].append(np.full(N_POINTS, np.nan))
                
                # Setpoints
                if sp_data is not None and len(t_sp) > 1:
                    f_setpoint = interp1d(t_sp_norm, sp_data[axis], bounds_error=False, fill_value="extrapolate")
                    data[f'{axis}_setpoint'].append(f_setpoint(common_time))
                else:
                    data[f'{axis}_setpoint'].append(np.full(N_POINTS, np.nan))
            
            # CPU and RAM
            if cpu_data is not None and len(t_cpu) > 1:
                f_cpu = interp1d(t_cpu_norm, cpu_data['load'] * 100, bounds_error=False, fill_value="extrapolate")
                f_ram = interp1d(t_cpu_norm, cpu_data['ram_usage'], bounds_error=False, fill_value="extrapolate")
                data['cpu'].append(f_cpu(common_time))
                data['ram'].append(f_ram(common_time))
            else:
                data['cpu'].append(np.full(N_POINTS, np.nan))
                data['ram'].append(np.full(N_POINTS, np.nan))
                
            # Energy
            if energy_wh is not None and len(t_bat) > 1:
                # Only interpolate if we have valid data
                f_energy = interp1d(t_bat_norm, energy_wh, bounds_error=False, fill_value="extrapolate")
                data['energy_wh'].append(f_energy(common_time))
            else:
                data['energy_wh'].append(np.full(N_POINTS, np.nan))
            
        except Exception as e:
            print(f"    - Error processing: {str(e)}")
    
    # Check data availability
    valid_energy_logs = sum(1 for e in data['energy_wh'] if not np.all(np.isnan(e)))
    print(f"  Valid energy data in {valid_energy_logs}/{len(log_files)} logs")
    
    return common_time, data

def calculate_statistics(data):
    """Calculate mean and confidence intervals"""
    results = {}
    for key, values in data.items():
        arr = np.array(values)
        mean = np.nanmean(arr, axis=0)
        std = np.nanstd(arr, axis=0)
        n = np.sum(~np.isnan(arr), axis=0)
        
        # Calculate 95% confidence intervals
        ci = np.zeros_like(mean)
        for i in range(len(mean)):
            if n[i] > 1:
                # Use t-distribution for CI
                t_value = stats.t.ppf(1 - (1 - CONFIDENCE_LEVEL)/2, n[i]-1)
                ci[i] = t_value * std[i] / np.sqrt(n[i])
            else:
                ci[i] = np.nan
                
        results[key] = {'mean': mean, 'ci': ci}
    
    return results

def plot_comparison(common_time, unsupervised_stats, supervised_stats, significance_results):
    """Create comparison plots for position tracking, resources, and energy"""
    # Create figure for position tracking
    fig_pos, axs_pos = plt.subplots(3, 1, figsize=(14, 12))
    axes = ['x', 'y', 'z']
    
    for i, axis in enumerate(axes):
        ax = axs_pos[i]

        ax.set_xlim(0, 100)  # Fix x-axis range
        # Remove x-ticks from upper subplots
        if i < len(axes) - 1:  # For x and y axes (first two subplots)
            ax.tick_params(axis='x', which='both', bottom=False, labelbottom=False)
        else:  # For z axis (bottom subplot)
            ax.set_xlabel('Mission Progress [%]')
        
        # USPFS actual position
        ax.plot(common_time, unsupervised_stats[f'{axis}_actual']['mean'], 
                color=COLORS['USPFS'], label='USPFS Actual')
        ax.fill_between(common_time, 
                       unsupervised_stats[f'{axis}_actual']['mean'] - unsupervised_stats[f'{axis}_actual']['ci'],
                       unsupervised_stats[f'{axis}_actual']['mean'] + unsupervised_stats[f'{axis}_actual']['ci'],
                       color=COLORS['USPFS'], alpha=0.2)
        
        # SSPFS actual position
        ax.plot(common_time, supervised_stats[f'{axis}_actual']['mean'], 
                color=COLORS['SSPFS'], label='SSPFS Actual')
        ax.fill_between(common_time, 
                       supervised_stats[f'{axis}_actual']['mean'] - supervised_stats[f'{axis}_actual']['ci'],
                       supervised_stats[f'{axis}_actual']['mean'] + supervised_stats[f'{axis}_actual']['ci'],
                       color=COLORS['SSPFS'], alpha=0.2)
        
        # Setpoints
        ax.plot(common_time, unsupervised_stats[f'{axis}_setpoint']['mean'], 
                color=COLORS['USPFS'], linestyle='--', alpha=0.7, label='USPFS Setpoint')
        ax.plot(common_time, supervised_stats[f'{axis}_setpoint']['mean'], 
                color=COLORS['SSPFS'], linestyle='--', alpha=0.7, label='SSPFS Setpoint')
        
        # Add phase markers
        for phase, (start, end) in PHASES.items():
            ax.axvspan(start, end, alpha=0.1, color='gray')
        
        ax.set_ylabel(f'{axis.upper()} Position [m]')
        ax.grid(True)
        if i == 0:
            ax.legend(loc='upper right', ncol=2, fontsize=9)
    
    axs_pos[0].set_title('Position Tracking Comparison')
    axs_pos[-1].set_xlabel('Mission Progress [%]')
    
    # Create figure for system resources (CPU and RAM)
    fig_res, axs_res = plt.subplots(2, 1, figsize=(14, 8))
    
    # CPU plot
    ax = axs_res[0]
    ax.set_xlim(0, 100)
    ax.tick_params(axis='x', which='both', bottom=False, labelbottom=False)  # Hide x-ticks
    ax.plot(common_time, unsupervised_stats['cpu']['mean'], 
            color=COLORS['USPFS'], label='USPFS CPU')
    ax.fill_between(common_time, 
                   unsupervised_stats['cpu']['mean'] - unsupervised_stats['cpu']['ci'],
                   unsupervised_stats['cpu']['mean'] + unsupervised_stats['cpu']['ci'],
                   color=COLORS['USPFS'], alpha=0.2)
    
    ax.plot(common_time, supervised_stats['cpu']['mean'], 
            color=COLORS['SSPFS'], label='SSPFS CPU')
    ax.fill_between(common_time, 
                   supervised_stats['cpu']['mean'] - supervised_stats['cpu']['ci'],
                   supervised_stats['cpu']['mean'] + supervised_stats['cpu']['ci'],
                   color=COLORS['SSPFS'], alpha=0.2)
    
    ax.set_ylabel('CPU Load [%]')
    ax.set_ylim(0, 100)
    ax.grid(True)
    ax.legend()
    
    # RAM plot
    ax = axs_res[1]
    ax.set_xlim(0, 100)
    ax.plot(common_time, unsupervised_stats['ram']['mean'], 
            color=COLORS['USPFS'], label='USPFS RAM')
    ax.fill_between(common_time, 
                   unsupervised_stats['ram']['mean'] - unsupervised_stats['ram']['ci'],
                   unsupervised_stats['ram']['mean'] + unsupervised_stats['ram']['ci'],
                   color=COLORS['USPFS'], alpha=0.2)
    
    ax.plot(common_time, supervised_stats['ram']['mean'], 
            color=COLORS['SSPFS'], label='SSPFS RAM')
    ax.fill_between(common_time, 
                   supervised_stats['ram']['mean'] - supervised_stats['ram']['ci'],
                   supervised_stats['ram']['mean'] + supervised_stats['ram']['ci'],
                   color=COLORS['SSPFS'], alpha=0.2)
    
    ax.set_ylabel('RAM Usage [MB]')
    ax.set_xlabel('Mission Progress [%]')
    ax.grid(True)
    ax.legend()
    
    axs_res[0].set_title('System Resource Usage Comparison')
    
    # Create figure for energy consumption only
    fig_energy, ax_energy = plt.subplots(figsize=(14, 5))
    
    # Energy consumption plot
    ax_energy.plot(common_time, unsupervised_stats['energy_wh']['mean'], 
            color=COLORS['USPFS'], label='USPFS Energy')
    ax_energy.fill_between(common_time, 
                   unsupervised_stats['energy_wh']['mean'] - unsupervised_stats['energy_wh']['ci'],
                   unsupervised_stats['energy_wh']['mean'] + unsupervised_stats['energy_wh']['ci'],
                   color=COLORS['USPFS'], alpha=0.2)
    
    ax_energy.plot(common_time, supervised_stats['energy_wh']['mean'], 
            color=COLORS['SSPFS'], label='SSPFS Energy')
    ax_energy.fill_between(common_time, 
                   supervised_stats['energy_wh']['mean'] - supervised_stats['energy_wh']['ci'],
                   supervised_stats['energy_wh']['mean'] + supervised_stats['energy_wh']['ci'],
                   color=COLORS['SSPFS'], alpha=0.2)
    
    ax_energy.set_ylabel('Energy Consumed (Wh)')
    ax_energy.set_xlabel('Mission Progress [%]')
    ax_energy.set_xlim(0, 100)
    ax_energy.grid(True)
    ax_energy.legend()
    ax_energy.set_title('Energy Consumption Comparison')
    
    plt.tight_layout()
    
    return fig_pos, fig_res, fig_energy

def calculate_significance(unsupervised_data, supervised_data):
    """Calculate statistical significance between groups"""
    results = {}
    
    # Metrics list (power_w removed)
    metrics = ['x_actual', 'y_actual', 'z_actual', 'cpu', 'ram', 'energy_wh']
    
    for metric in metrics:
        # Extract metric data
        unsup = np.array(unsupervised_data[metric])
        sup = np.array(supervised_data[metric])
        
        # Initialize result storage
        metric_results = {
            'mean_diff': [],
            'p_value': [],
            'significant': []
        }
        
        # Calculate for each time point
        for t in range(unsup.shape[1]):
            unsup_vals = unsup[:, t]
            sup_vals = sup[:, t]
            
            # Remove NaN values
            unsup_vals = unsup_vals[~np.isnan(unsup_vals)]
            sup_vals = sup_vals[~np.isnan(sup_vals)]
            
            if len(unsup_vals) > 1 and len(sup_vals) > 1:
                # Independent t-test
                t_stat, p_value = stats.ttest_ind(unsup_vals, sup_vals, 
                                                 equal_var=False,
                                                 nan_policy='omit')
                
                mean_diff = np.mean(unsup_vals) - np.mean(sup_vals)
                significant = p_value < ALPHA
                
                metric_results['mean_diff'].append(mean_diff)
                metric_results['p_value'].append(p_value)
                metric_results['significant'].append(significant)
            else:
                metric_results['mean_diff'].append(np.nan)
                metric_results['p_value'].append(np.nan)
                metric_results['significant'].append(False)
        
        results[metric] = metric_results
    
    return results

# Main execution
if __name__ == "__main__":
    print("\n" + "="*50)
    print("Starting comparative analysis")
    print("="*50)
    
    # Process both groups
    common_time, unsupervised_data = process_group(UNSUPERVISED_LOGS, "USPFS")
    _, supervised_data = process_group(SUPERVISED_LOGS, "SSPFS")
    
    # Calculate statistics
    print("\nCalculating statistics...")
    unsupervised_stats = calculate_statistics(unsupervised_data)
    supervised_stats = calculate_statistics(supervised_data)
    
    # Print energy statistics for debugging
    print("\nEnergy statistics:")
    print(f"USPFS Energy - Min: {np.nanmin(unsupervised_stats['energy_wh']['mean']):.2f}Wh, " +
          f"Max: {np.nanmax(unsupervised_stats['energy_wh']['mean']):.2f}Wh, " +
          f"Mean: {np.nanmean(unsupervised_stats['energy_wh']['mean']):.2f}Wh")
    print(f"SSPFS Energy - Min: {np.nanmin(supervised_stats['energy_wh']['mean']):.2f}Wh, " +
          f"Max: {np.nanmax(supervised_stats['energy_wh']['mean']):.2f}Wh, " +
          f"Mean: {np.nanmean(supervised_stats['energy_wh']['mean']):.2f}Wh")
    
    # Significance testing
    print("Performing significance testing...")
    significance_results = calculate_significance(unsupervised_data, supervised_data)
    
    # Generate plots
    print("Generating comparison plots...")
    fig_pos, fig_res, fig_energy = plot_comparison(common_time, unsupervised_stats, supervised_stats, significance_results)
    
    # Save results
    print("\nSaving results...")
    results_df = pd.DataFrame({
        'time': common_time,
        **{f"{metric}_{stat}": vals 
           for metric, stats_dict in significance_results.items()
           for stat, vals in stats_dict.items()}
    })
    results_df.to_csv('significance_results.csv', index=False)
    print("Significance results saved to significance_results.csv")
    
    # Save plots
    fig_pos.savefig('position_comparison.png', dpi=300, bbox_inches='tight')
    fig_res.savefig('resource_comparison.png', dpi=300, bbox_inches='tight')
    fig_energy.savefig('energy_consumption_comparison.png', dpi=300, bbox_inches='tight')
    print("Plots saved as position_comparison.png, resource_comparison.png, and energy_consumption_comparison.png")
    
    print("\nAnalysis complete. Showing plots...")
    plt.show()
