SOURCES_DIR = "sources"
TIMINGS_DIR = "timing_data"
PLOTS_DIR = "plots"

MODULE_STATS_FILE = "module_stats.csv"
PACKAGE_STATS_FILE = "package_stats.csv"

# Colorblind-friendly colors
# SOURCE: https://gist.github.com/thriveth/8560036
CB_COLORS = {
    'blue':    '#377eb8', 
    'orange':  '#ff7f00',
    'green':   '#4daf4a',
    'pink':    '#f781bf',
    'brown':   '#a65628',
    'purple':  '#984ea3',
    'gray':    '#999999',
    'red':     '#e41a1c',
    'yellow':  '#dede00',
    'black':   '#000000' # added this
}

# Plotting styles
PLOT_STYLES = {
    ".hs": {"color": CB_COLORS["blue"], "marker": "o"},
    ".hsc": {"color": CB_COLORS["green"], "marker": "s"}
}
DEFAULT_PLOT_STYLE = {"color": CB_COLORS["red"], "marker": "X"}

PACKAGE_STYLE = {"alpha": 0.5, "color": CB_COLORS["blue"], "marker": "o"}