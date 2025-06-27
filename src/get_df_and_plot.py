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
