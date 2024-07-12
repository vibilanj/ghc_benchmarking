import os
import fnmatch
import json5
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from constants import (
    SOURCES_DIR, TIMINGS_DIR, PLOTS_DIR,
    MODULE_STATS_FILE, PACKAGE_STATS_FILE,
    CB_COLORS, PLOT_STYLES, DEFAULT_PLOT_STYLE
)


def read_json_file(file):
    with open(file) as f:
        # json does not handle trailing commas in JSON files
        return json5.load(f)


def read_and_clean_timings(filename):
    file_path = os.path.join(TIMINGS_DIR, filename)
    data = read_json_file(file_path)
    timings_df = pd.DataFrame(data["data"])

    # Remove systool and hi/dyn_hi modules
    timings_df = timings_df[~timings_df["module"].isin(["systool"]) & ~timings_df["module"].str.endswith(("hi", "dyn_hi"))]

    package_name = filename.replace(".json", "")
    timings_df.insert(0, "package", package_name)
    timings_df.drop(["alloc"], axis = 1, inplace = True)

    output_file = os.path.join(TIMINGS_DIR, f"{package_name}_timings.csv")
    timings_df.to_csv(output_file, index = False)
    return timings_df


def get_size_and_extension(package, module):
    package_path = os.path.join(SOURCES_DIR, package)
    src_dirs = ["", "src", "lib"]

    module_path_list = module.split(".")
    module_path = os.path.join(*module_path_list[:-1]) if len(module_path_list) > 1 else ""
    search_pattern = f"{module_path_list[-1]}.*"

    for src_dir in src_dirs:
        # Construct the search path for the module
        search_path = os.path.join(package_path, src_dir, module_path)
        if not os.path.isdir(search_path):
            continue
    
        for root, _dirs, files in os.walk(search_path):
            for name in files:
                if fnmatch.fnmatch(name, search_pattern):
                    file_path = os.path.join(root, name)
                    size = os.path.getsize(file_path)
                    extension = os.path.splitext(file_path)[1]
                    return size, extension

    print(f"Could not find file for module {module} in package {package}.")
    return 0, ""


def compute_statistics(df):
    if df.empty:
        raise ValueError("Dataframe is empty.")

    module_stats = []
    modules = df["module"].unique()
    package_name = df["package"].iloc[0]

    # Module stats
    for module in modules:
        module_size, module_extension = get_size_and_extension(package_name, module)
        if module_size == 0 and module_extension == "":
            continue

        total_time = df[df["module"] == module]["time"].sum()
        parser_time = df[(df["module"] == module) & (df["phase"] == "Parser")]["time"].sum()
        parser_percentage = (parser_time / total_time) * 100
        
        stats = {
            "module": module,
            "total_time": total_time,
            "parser_time": parser_time,
            "parser_percentage": parser_percentage,
            "size": module_size,
            "extension": module_extension
        }
        module_stats.append(stats)

    module_stats_df = pd.DataFrame(module_stats)
    module_stats_df.insert(0, "package", package_name)

    # Package stats
    package_total_time = module_stats_df["total_time"].sum()
    package_parser_time = module_stats_df["parser_time"].sum()
    package_parser_percentage = (package_parser_time / package_total_time) * 100
    average_parser_percentage = module_stats_df["parser_percentage"].mean()
    geomean_parser_percentage = module_stats_df["parser_percentage"].prod() ** (1 / len(module_stats_df))
    package_size = module_stats_df["size"].sum()
    
    package_stats = {
        "package": [package_name],
        "total_time": [package_total_time],
        "parser_time": [package_parser_time],
        "parser_percentage": [package_parser_percentage],
        "average_parser_percentage": [average_parser_percentage],
        "geomean_parser_percentage": [geomean_parser_percentage],
        "size": [package_size]
    }
    package_stats_df = pd.DataFrame(package_stats)

    return module_stats_df, package_stats_df


def calculate_statistics_for_packages(files):
    all_module_stats = []
    all_package_stats = []

    for file in files:
        timings_df = read_and_clean_timings(file)
        module_stats_df, package_stats_df = compute_statistics(timings_df)
        all_module_stats.append(module_stats_df)
        all_package_stats.append(package_stats_df)

    all_module_stats_df = pd.concat(all_module_stats, ignore_index = True)
    all_module_stats_df.to_csv(MODULE_STATS_FILE, index = False)

    all_package_stats_df = pd.concat(all_package_stats, ignore_index = True)
    all_package_stats_df.to_csv(PACKAGE_STATS_FILE, index = False)


def plot_metric_vs_metric(df, x, y, xlabel, ylabel, title, filename, guide_pcts, guide_label, log = True):
    fig, ax = plt.subplots()
    for ext, ext_df in df.groupby("extension"):
        style = PLOT_STYLES.get(ext, DEFAULT_PLOT_STYLE)
        ax.scatter(ext_df[x], ext_df[y], alpha = 0.5, label = ext, **style)

    if log is True:
        ax.set(xscale = "log", yscale = "log")

    ax.grid(linestyle = "--", linewidth = 0.5)
    ax.set(xlabel = xlabel, ylabel = ylabel, title = title)

    # Clamping axes to the data
    ax.set_xlim(ax.get_xlim())
    ax.set_ylim(ax.get_ylim())

    # Percentage guide lines
    x_vals = np.linspace(df[x].min(), df[x].max(), 100)
    for idx, pct in enumerate(guide_pcts):
        pct_vals = (pct / 100) * x_vals
        linestyle = "-." if idx % 2 == 0 else ":"
        ax.plot(x_vals, pct_vals, linestyle, color = CB_COLORS["black"], label = f"{pct}{guide_label}")
        # TODO: different colors or weights for different lines: used alternating line styles for now

    # Add horizontal lines for average and median for percentage plots
    if y == "parser_percentage":
        avg = df[y].mean()
        median = df[y].median()
        ax.axhline(y = avg, linestyle = "--", color = CB_COLORS["blue"], label = f"average ({avg:.3g})")
        ax.axhline(y = median, linestyle = "--", color = CB_COLORS["green"], label = f"median ({median:.3g})")

    # Fits a power-law relationship and plot it
    log_x = np.log(df[x])
    log_y = np.log(df[y])
    b, a = np.polyfit(log_x, log_y, 1)  # Fit log(y) = b * log(x) + a
    a_exp = np.exp(a)

    x_vals = np.linspace(df[x].min(), df[x].max(), 100)
    y_vals = a_exp * x_vals**b
    ax.plot(x_vals, y_vals, "--", color = CB_COLORS["red"],
            label=f"best-fit line $y = {a_exp:.3g}x^{{{b:.3g}}}$")

    # Adding legend and saving the plot as a PDF
    ax.legend(fontsize = "small")
    if log is True:
        filename = filename.replace(".", "_log.")
    fig.savefig(os.path.join(PLOTS_DIR, filename), format = "pdf")


def make_module_plots():
    os.makedirs(PLOTS_DIR, exist_ok = True)

    df = pd.read_csv(MODULE_STATS_FILE)
    # NOTE: comment/uncomment to show all / hide other extensions
    df["extension"] = df["extension"].apply(lambda x: x if x in PLOT_STYLES else "other")

    # NOTE: Rescaling times from milliseconds to seconds
    df["total_time"] = df["total_time"] / 1000
    df["parser_time"] = df["parser_time"] / 1000

    metrics = [
        ("total_time", "parser_time", "Total time (s)", "Parser time (s)",
         "plot_parser_vs_total.pdf", [0.1, 1, 10], "%"),
        ("total_time", "parser_percentage", "Total time (s)", "Percentage of time spent on parsing (%)",
         "plot_parser_pct_vs_total.pdf", [], ""),
        ("size", "parser_time", "Size (bytes)", "Parser time (s)",
         "plot_parser_vs_size.pdf", [1e-5, 1e-4, 1e-3], " seconds/byte"),
        ("size", "parser_percentage", "Size (bytes)", "Percentage of time spent on parsing (%)",
         "plot_parser_pct_vs_size.pdf", [], ""),
    ]

    for x, y, xlabel, ylabel, filename, guide_pcts, guide_label in metrics:
        plot_metric_vs_metric(df, x, y, xlabel, ylabel, f"{ylabel} vs {xlabel}",
                              filename, guide_pcts, guide_label)
        plot_metric_vs_metric(df, x, y, xlabel, ylabel, f"{ylabel} vs {xlabel}",
                              filename, guide_pcts, guide_label, log = False)


def make_package_plots():
    os.makedirs(PLOTS_DIR, exist_ok = True)


    # TODO: Make four plots: x-axis as total time / size, y-axis as parser time / parser percentage (not average or geomean)
    # TODO: Add average and median of the y-axis as a horizontal line for percentage plots
    # TODO: Make final plot with final aggregated data point with total parser time / total time for all packages
    pass


if __name__ == "__main__":
    pass