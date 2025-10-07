import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

SRC_ROOT = os.path.dirname(os.path.abspath(__file__))

def extract_pickup_dataframe(json_data, plot=True, save_dir="plot"):
    print(f"[DEBUG] extract_pickup_dataframe called with plot={plot}, save_dir={save_dir}")
    rows = []
    for parent in json_data.values():
        for child in parent.get("children", {}).values():
            hex_id = child.get("hex_id")
            for date, count in child.get("pickups_by_date", {}).items():
                rows.append({
                    "child_hex": hex_id,
                    "pickup_date": date,
                    "pickup_count": count
                })
    print(f"[DEBUG] Extracted {len(rows)} rows from JSON data.")
    df = pd.DataFrame(rows)
    print(f"[DEBUG] Created DataFrame with shape {df.shape}.")
    pivot_df = df.pivot(index='child_hex', columns='pickup_date', values='pickup_count')
    pivot_df = pivot_df.fillna(0).astype(int)
    print(f"[DEBUG] Created pivot DataFrame with shape {pivot_df.shape}.")
    if plot:
        plots_subdir = os.path.join(save_dir, "plots")
        os.makedirs(plots_subdir, exist_ok=True)
        print(f"[DEBUG] Plots subdirectory: {os.path.relpath(plots_subdir, SRC_ROOT)}")
        top_hexes = pivot_df.sum(axis=1).sort_values(ascending=False).head(3).index
        print(f"[DEBUG] Top 3 busiest hexes: {list(top_hexes)}")
        plt.figure(figsize=(12, 6))
        for hex_id in top_hexes:
            pivot_df.loc[hex_id].plot(label=hex_id)
        plt.title("Pickup Trend Over Time (Top 3 Hexes)")
        plt.ylabel("Pickup Count")
        plt.xlabel("Date")
        plt.xticks(rotation=45)
        plt.legend(title="Child Hex")
        plt.tight_layout()
        plot1_path = f"{plots_subdir}/pickup_trend_top3_hexes.png"
        plt.savefig(plot1_path, dpi=300)
        print(f"[DEBUG] Saved plot: {os.path.relpath(plot1_path, SRC_ROOT)}")
        plt.close()
        plt.figure(figsize=(20, 12))
        sns.heatmap(pivot_df, cmap="YlGnBu", cbar_kws={'label': 'Pickup Count'})
        plt.title("Heatmap of Pickups by Child Hex and Date")
        plt.ylabel("Child Hex")
        plt.xlabel("Pickup Date")
        plt.tight_layout()
        plot2_path = f"{plots_subdir}/heatmap_all_hexes.png"
        plt.savefig(plot2_path, dpi=300)
        print(f"[DEBUG] Saved plot: {os.path.relpath(plot2_path, SRC_ROOT)}")
        plt.close()
    return pivot_df

def extract_forecast_comparison_data(forecasted_json_data, plot=True, save_dir="plot"):
    """
    Extract forecast comparison data and create visualization plots.
    
    Args:
        forecasted_json_data: JSON data with forecast information
        plot: Whether to generate plots
        save_dir: Directory to save plots
    
    Returns:
        DataFrame with comparison metrics
    """
    print(f"[DEBUG] extract_forecast_comparison_data called with plot={plot}, save_dir={save_dir}")
    
    comparison_data = []
    
    for parent in forecasted_json_data.values():
        for child in parent.get("children", {}).values():
            hex_id = child.get("hex_id")
            actual = child.get("last_week_actual")
            forecast = child.get("last_week_forecast") 
            missed = child.get("last_week_missed_rides")
            extra = child.get("last_week_extra_rides")
            confidence = child.get("forecast_confidence_percent")
            date = child.get("last_week_date")
            
            # Only include entries that have valid comparison data
            if actual is not None and forecast is not None:
                comparison_data.append({
                    "hex_id": hex_id,
                    "date": date,
                    "actual_rides": actual,
                    "forecasted_rides": forecast,
                    "missed_rides": missed if missed is not None else 0,
                    "extra_rides": extra if extra is not None else 0,
                    "confidence_percent": confidence if confidence is not None else 0,
                    "total_demand": actual + (extra if extra is not None else 0),
                    "forecast_accuracy": "Perfect" if missed == 0 and extra == 0 else "Over-forecast" if missed > 0 else "Under-forecast"
                })
    
    df_comparison = pd.DataFrame(comparison_data)
    print(f"[DEBUG] Created comparison DataFrame with {len(df_comparison)} rows.")
    
    if plot and len(df_comparison) > 0:
        plots_subdir = os.path.join(save_dir, "plots")
        os.makedirs(plots_subdir, exist_ok=True)
        print(f"[DEBUG] Plots subdirectory: {os.path.relpath(plots_subdir, SRC_ROOT)}")
        
        # Create multiple subplots for comprehensive comparison
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Forecast vs Actual Rides Comparison Analysis', fontsize=16, fontweight='bold')
        
        # 1. Actual vs Forecasted scatter plot
        ax1 = axes[0, 0]
        scatter = ax1.scatter(df_comparison['actual_rides'], df_comparison['forecasted_rides'], 
                             c=df_comparison['confidence_percent'], cmap='RdYlGn', alpha=0.7, s=60)
        ax1.plot([0, df_comparison['actual_rides'].max()], [0, df_comparison['actual_rides'].max()], 
                'r--', alpha=0.8, label='Perfect Forecast Line')
        ax1.set_xlabel('Actual Rides')
        ax1.set_ylabel('Forecasted Rides')
        ax1.set_title('Actual vs Forecasted Rides')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Add colorbar for confidence
        cbar1 = plt.colorbar(scatter, ax=ax1)
        cbar1.set_label('Confidence %')
        
        # 2. Actual vs Missed vs Extra rides comparison
        ax2 = axes[0, 1]
        x_pos = range(len(df_comparison))
        width = 0.25
        
        bars1 = ax2.bar([x - width for x in x_pos], df_comparison['actual_rides'], width, 
                       label='Actual Rides', color='green', alpha=0.7)
        bars2 = ax2.bar(x_pos, df_comparison['missed_rides'], width, 
                       label='Missed Rides', color='red', alpha=0.7)
        bars3 = ax2.bar([x + width for x in x_pos], df_comparison['extra_rides'], width, 
                       label='Extra Rides', color='blue', alpha=0.7)
        
        ax2.set_xlabel('Hex ID (Index)')
        ax2.set_ylabel('Number of Rides')
        ax2.set_title('Actual vs Missed vs Extra Rides by Hex')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Show only every 5th tick to avoid overcrowding
        ax2.set_xticks(x_pos[::5])
        ax2.set_xticklabels([f"{df_comparison.iloc[i]['hex_id'][-4:]}" for i in range(0, len(df_comparison), 5)], rotation=45)
        
        # 3. Forecast accuracy distribution
        ax3 = axes[1, 0]
        accuracy_counts = df_comparison['forecast_accuracy'].value_counts()
        colors = ['green' if x == 'Perfect' else 'orange' if x == 'Over-forecast' else 'red' for x in accuracy_counts.index]
        wedges, texts, autotexts = ax3.pie(accuracy_counts.values, labels=accuracy_counts.index, autopct='%1.1f%%', 
                                          colors=colors, startangle=90)
        ax3.set_title('Forecast Accuracy Distribution')
        
        # 4. Confidence vs Error correlation
        ax4 = axes[1, 1]
        error = abs(df_comparison['actual_rides'] - df_comparison['forecasted_rides'])
        scatter2 = ax4.scatter(df_comparison['confidence_percent'], error, 
                              c=df_comparison['total_demand'], cmap='viridis', alpha=0.7, s=60)
        ax4.set_xlabel('Confidence %')
        ax4.set_ylabel('Absolute Error (|Actual - Forecast|)')
        ax4.set_title('Confidence vs Forecast Error')
        ax4.grid(True, alpha=0.3)
        
        # Add colorbar for total demand
        cbar2 = plt.colorbar(scatter2, ax=ax4)
        cbar2.set_label('Total Demand')
        
        plt.tight_layout()
        
        # Save the plot
        plot_path = f"{plots_subdir}/forecast_actual_comparison.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        print(f"[DEBUG] Saved comparison plot: {os.path.relpath(plot_path, SRC_ROOT)}")
        plt.close()
        
        # Create a summary statistics plot
        fig2, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        # Summary statistics
        total_actual = df_comparison['actual_rides'].sum()
        total_forecasted = df_comparison['forecasted_rides'].sum()
        total_missed = df_comparison['missed_rides'].sum()
        total_extra = df_comparison['extra_rides'].sum()
        
        categories = ['Actual Rides', 'Forecasted Rides', 'Missed Rides', 'Extra Rides']
        values = [total_actual, total_forecasted, total_missed, total_extra]
        colors = ['blue', 'orange', 'red', 'purple']
        
        bars = ax.bar(categories, values, color=colors, alpha=0.7)
        ax.set_ylabel('Total Number of Rides')
        ax.set_title('Summary: Total Rides Comparison')
        ax.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                   f'{int(value)}', ha='center', va='bottom', fontweight='bold')
        
        # Add summary text
        accuracy_rate = ((total_actual - abs(total_actual - total_forecasted)) / total_actual * 100) if total_actual > 0 else 0
        summary_text = f"""Summary Statistics:
        • Forecast Accuracy: {accuracy_rate:.1f}%
        • Total Missed Opportunities: {total_missed} rides
        • Total Extra Capacity: {total_extra} rides
        • Hexes Analyzed: {len(df_comparison)}"""
        
        ax.text(0.98, 0.98, summary_text, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', horizontalalignment='right', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
        # Save the summary plot
        summary_plot_path = f"{plots_subdir}/forecast_summary_statistics.png"
        plt.savefig(summary_plot_path, dpi=300, bbox_inches='tight')
        print(f"[DEBUG] Saved summary plot: {os.path.relpath(summary_plot_path, SRC_ROOT)}")
        plt.close()
    
    return df_comparison
