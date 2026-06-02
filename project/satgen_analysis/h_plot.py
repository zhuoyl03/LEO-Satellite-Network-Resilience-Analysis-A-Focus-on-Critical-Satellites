import os
import csv
import matplotlib.pyplot as plt
import numpy as np
import sys
from pathlib import Path
PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))
from config import PROJECT_PLOTS_DIR, STARLINK_DATA_NAME, analysis_window_dir

# Define the input directories for the CSV files
analysis_dir = analysis_window_dir(STARLINK_DATA_NAME)
input_dirs = [
    analysis_dir / "rtt" / "hplot",
    analysis_dir / "rtt_delete_50" / "hplot",
    analysis_dir / "rtt_delete_100" / "hplot",
    analysis_dir / "rtt_delete_200" / "hplot",
]

# Define the names for the datasets
names = [
    'Baseline',
    '50 satellites removed',
    '100 satellites removed',
    '200 satellites removed'
]

def plot_rtt_histograms():
    # Define the output directory for the histograms
    pdf_dir = PROJECT_PLOTS_DIR
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)

    # Function to read a list from a CSV file
    def read_list_from_csv(filename):
        data = []
        with open(filename, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(float(row['Value']))
        return data

    # Read the lists from the CSV files in the input directories
    lists = []
    for input_dir in input_dirs:
        lists.append({
            "Minimum RTT (ns)": read_list_from_csv(os.path.join(input_dir, 'ecdf_pairs_min_rtt_ns.csv')),
            "Maximum RTT (ns)": read_list_from_csv(os.path.join(input_dir, 'ecdf_pairs_max_rtt_ns.csv')),
            "Max - Min RTT (ns)": read_list_from_csv(os.path.join(input_dir, 'ecdf_pairs_max_minus_min_rtt_ns.csv')),
            "Max RTT to Min RTT Slowdown": read_list_from_csv(os.path.join(input_dir, 'ecdf_pairs_max_rtt_to_min_rtt_slowdown.csv')),
            "Max RTT to Geodesic Slowdown": read_list_from_csv(os.path.join(input_dir, 'ecdf_pairs_max_rtt_to_geodesic_slowdown.csv'))
        })

    # Define the colors for the histograms
    colors = ['blue', 'green', 'red', 'purple']

    # Calculate the global min and max for each key
    global_min_max = {}
    for key in lists[0].keys():
        all_data = [value for data_dict in lists for value in data_dict[key]]
        global_min_max[key] = (min(all_data), max(all_data))

    # Plotting the histograms
    for key in lists[0].keys():
        plt.figure()
        bins = np.linspace(global_min_max[key][0], global_min_max[key][1], 50)  # Define consistent bins
        for i, data_dict in enumerate(lists):
            data = data_dict[key]
            plt.hist(data, bins=bins, edgecolor='k', alpha=0.5, color=colors[i], label=names[i])
        plt.xlabel(key)
        plt.ylabel('Frequency')
        plt.title(f'Histogram of {key}')
        plt.xlim(global_min_max[key])  # Set the x-axis limits to be the same for all histograms of the same key
        plt.legend()

        # Add inset for "Max RTT to Geodesic Slowdown" if applicable
        if key == "Max RTT to Geodesic Slowdown":
            ax_inset = plt.gca().inset_axes([0.5, 0.5, 0.45, 0.45])  # Position and size of the inset
            for i, data_dict in enumerate(lists):
                filtered_data = [d for d in data_dict[key] if d > 15]
                ax_inset.hist(filtered_data, bins=bins, edgecolor='k', alpha=0.5, color=colors[i])
            ax_inset.set_xlim(15, global_min_max[key][1])
            ax_inset.legend(fontsize='small')

        histogram_pdf_file_path = os.path.join(pdf_dir, f"{key.replace(' ', '_')}_histogram.pdf")
        plt.savefig(histogram_pdf_file_path)
        plt.close()

    print("Histograms saved successfully.")
