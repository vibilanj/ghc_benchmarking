import textwrap
import os
import fnmatch
import json5
import pandas as pd
import matplotlib.pyplot as plt

from constants import (
    SOURCES_DIR, TIMINGS_DIR, MODULE_STATS_FILE, PACKAGE_STATS_FILE,
    CF_blue, CF_vermillion, CF_green
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


# TODO: move to constants later
PLOT_STYLES = {
    ".hs": {"color": CF_blue, "marker": "o"},
    ".hsc": {"color": CF_green, "marker": "s"}
    # "other": {"color": CF_vermillion, "marker": "X"}
}
DEFAULT_PLOT_STYLE = {"color": CF_vermillion, "marker": "X"}


def plot_metric_vs_metric(df, x, y, xlabel, ylabel, title, filename):
    fig, ax = plt.subplots()
    for ext, ext_df in df.groupby("extension"):
        style = PLOT_STYLES.get(ext, DEFAULT_PLOT_STYLE)
        ax.scatter(ext_df[x], ext_df[y], alpha = 0.5, label = ext, **style)

    ax.set(xscale = "log", yscale = "log")
    ax.grid(linestyle = "--", linewidth = 0.5)
    ax.set(xlabel = xlabel, ylabel = ylabel, title = title)
    ax.legend()
    fig.savefig(filename)


def make_module_plots():
    df = pd.read_csv(MODULE_STATS_FILE)
    # TODO: uncomment to show all extensions but defaults to 'other' style
    # df["extension"] = df["extension"].apply(lambda x: x if x in PLOT_STYLES else "other")

    metrics = [
        ("total_time", "parser_time", "Total time (ms)", "Parser time (ms)", "plot_parser_vs_total.png"),
        ("total_time", "parser_percentage", "Total time (ms)", "Percentage of time spent on parsing (%)", "plot_parser_pct_vs_total.png"),
        ("size", "parser_time", "Size (bytes)", "Parser time (ms)", "plot_parser_vs_size.png"),
        ("size", "parser_percentage", "Size (bytes)", "Percentage of time spent on parsing (%)", "plot_parser_pct_vs_size.png")
    ]

    for x, y, xlabel, ylabel, filename in metrics:
        plot_metric_vs_metric(df, x, y, xlabel, ylabel, f"{ylabel} vs {xlabel}", filename)


def make_package_plots():
    # TODO: implement
    pass


if __name__ == "__main__":
    pass