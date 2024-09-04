# Terminal (gnuplot 4.4+); Swiss neutral Helvetica font
set terminal pdfcairo font "Helvetica, 27"  size 6, 4 linewidth 3 rounded dashed

# Line style for axes
set style line 80 lt rgb "#808080"

# Line style for grid
set style line 81 lt 0  # Dashed
set style line 81 lt rgb "#999999"  # Grey grid

# Grey grid and border
set grid back linestyle 81
set border 3 back linestyle 80
set xtics nomirror
set ytics nomirror

# Line styles
set style line 1 lt rgb "#1b9e77" lw 4 pt 1 ps 1.5  # Teal
set style line 2 lt rgb "#d95f02" lw 4 pt 2 ps 1.5 dt 2  # Orange
set style line 3 lt rgb "#7570b3" lw 4 pt 3 ps 1.5 dt 3  # Purple
set style line 4 lt rgb "#e7298a" lw 4 pt 4 ps 1.5 dt 4  # Pink
set style line 5 lt rgb "#66a61e" lw 4 pt 5 ps 1.5 dt 5  # Green

# Output
set output "/home/leo/hypatia/ECE227/pdf/ecdf_max_rtt_Kuiper_590.pdf"
#####################################
### AXES AND KEY

# Axes labels
set xlabel "Max. RTT (ms)" # Markup: e.g. 99^{th}, {/Symbol s}, {/Helvetica-Italic P}
set ylabel "ECDF (pairs)"

# Axes ranges
set xrange [0:]       # Explicitly set the x-range [lower:upper]
set yrange [0:]       # Explicitly set the y-range [lower:upper]
# set xtics (0, 100, 300, 500, 700, 900)
# set ytics <start>, <incr> {,<end>}
# set format x "%.2f%%"  # Set the x-tic format, e.g. in this case it takes 2 sign. decimals: "24.13%""

# For logarithmic axes
# set log x           # Set logarithmic x-axis
# set log y           # Set logarithmic y-axis
# set mxtics 3        # Set number of intermediate tics on x-axis (for log plots)
# set mytics 3        # Set number of intermediate tics on y-axis (for log plots)

# Font of the key (a.k.a. legend)
set key font ",22"
set key reverse
set key bottom right Right
set key spacing 1.5

# Start multiplot mode
set multiplot

# Adjust the plot layout
set size 1.0, 1.0    # Full size of the plot
set origin 0.0, 0.0  # Position the plot at the origin

#####################################
### PLOTS
set datafile separator ","
plot    "/home/leo/hypatia/ECE227/satgen_analysis/kuiper_590_isls_plus_grid_ground_stations_top_100_algorithm_free_one_only_over_isls/1000ms_for_200s/rtt/data/ecdf_pairs_max_rtt_ns.txt" using ($1/1000000.0):($2) title "K3" with steps ls 1, \
        "/home/leo/hypatia/ECE227/satgen_analysis/kuiper_590_isls_plus_grid_ground_stations_top_100_algorithm_free_one_only_over_isls/1000ms_for_200s/rtt_delete_50/data/ecdf_pairs_max_rtt_ns.txt" using ($1/1000000.0):($2) title "K3 - 50 Removed" with steps ls 2, \
        "/home/leo/hypatia/ECE227/satgen_analysis/kuiper_590_isls_plus_grid_ground_stations_top_100_algorithm_free_one_only_over_isls/1000ms_for_200s/rtt_delete_100/data/ecdf_pairs_max_rtt_ns.txt" using ($1/1000000.0):($2) title "K3 - 100 Removed" with steps ls 3, \
        "/home/leo/hypatia/ECE227/satgen_analysis/kuiper_590_isls_plus_grid_ground_stations_top_100_algorithm_free_one_only_over_isls/1000ms_for_200s/rtt_delete_150/data/ecdf_pairs_max_rtt_ns.txt" using ($1/1000000.0):($2) title "K3 - 150 Removed" with steps ls 4
