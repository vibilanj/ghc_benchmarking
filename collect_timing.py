import textwrap
import os
import fnmatch
import json5
import pandas as pd
import matplotlib.pyplot as plt

SAVE_PATH = "timing_data/"
SOURCES_PATH = "sources/"
COMBINED_CSV = "combined_stats.csv"

# Colorblind-friendly colors
CF_red = (204/255, 121/255, 167/255)
CF_vermillion = (213/255, 94/255, 0)
CF_orange = (230/255, 159/255, 0)
CF_yellow = (240/255, 228/255, 66/255)
CF_green = (0, 158/255, 115/255)
CF_sky = (86/255, 180/255, 233/255)
CF_blue = (0, 114/255, 178/255)
CF_black = (0, 0, 0)


def read_json_file(file):
    with open(file) as f:
        # json does not handle trailing comma
        return json5.load(f)


def read_and_clean_timings(file):
    data = read_json_file(f"{SAVE_PATH}{file}")
    timings = []
    for timing in data["data"]:
        module = timing["module"]
        # disregard if "systool" or module ending in .hi or .dyn_hi
        if module == "systool" or module.endswith(".hi") or module.endswith(".dyn_hi"):
            continue
        timings.append(timing)

    package_name = file.replace(".json", "")
    timings_df = pd.DataFrame(timings)
    timings_df.insert(0, "package", package_name)
    timings_df.drop(["alloc"], axis = 1, inplace = True)

    timings_df.to_csv(f"{SAVE_PATH}{package_name}_timings.csv", index = False)
    return timings_df


def get_size_and_extension(package, module):
    package_path = f"{SOURCES_PATH}{package}/"
    src_dir = ""
    if os.path.isdir(f"{package_path}/src"):
        src_dir = "src/"
    elif os.path.isdir(f"{package_path}/lib"):
        # for packages like time
        src_dir = "lib/"

    module_path_list = module.split(".")
    module_path = "/".join(module_path_list[:-1])
    search_pattern = f"{module_path_list[-1]}.*"

    file_path = None
    search_path = f"{package_path}{src_dir}{module_path}"
    for root, _dirs, files in os.walk(search_path):
        for name in files:
            if fnmatch.fnmatch(name, search_pattern):
                file_path = os.path.join(root, name)
                break

    if file_path is None:
        print(f"Could not find file for module {module} in package {package}.")
        return 0, 0

    size = os.path.getsize(file_path)
    extension = os.path.splitext(file_path)[1]
    return size, extension


def calculate_totals_and_stats(df):
    totals = []
    modules = df["module"].unique()
    package_name = df["package"].iloc[0]

    for module in modules:
        total_time = df[df["module"] == module]["time"].sum()
        parser_time = df[(df["module"] == module) & (df["phase"] == "Parser")]["time"].sum()
        parser_percentage = (parser_time / total_time) * 100
        module_size, module_extension = get_size_and_extension(package_name, module)
        
        module_stats = {
            "module": module,
            "total_time": total_time,
            "parser_time": parser_time,
            "parser_percentage": parser_percentage,
            "size": module_size,
            "extension": module_extension
        }
        totals.append(module_stats)

    totals_df = pd.DataFrame(totals)
    totals_df.insert(0, "package", package_name)

    package_total = totals_df["total_time"].sum()
    package_parser = totals_df["parser_time"].sum()
    package_parser_percentage = (package_parser / package_total) * 100
    average_parser_percentage = totals_df["parser_percentage"].mean()
    geomean_parser_percentage = totals_df["parser_percentage"].prod() ** (1 / len(totals_df))
    package_size = totals_df["size"].sum()
    
    stats = f"""
        Package: {package_name}
        Total time for package: {package_total}
        Total parser time for package: {package_parser}
        Percentage of total time spent in parser: {package_parser_percentage}
        Arithmetic mean of parser percentage: {average_parser_percentage}
        Geometric mean of parser percentage: {geomean_parser_percentage}
        Size of package in bytes: {package_size}
        """
    
    totals_df.to_csv(f"{SAVE_PATH}{package_name}_stats.csv", index = False)
    with open(f"{SAVE_PATH}{package_name}_stats.txt", "w") as f:
        f.write(textwrap.dedent(stats))
    
    return totals_df


def calculate_for_packages(files):
    for file in files:
        timings_df = read_and_clean_timings(file)
        calculate_totals_and_stats(timings_df)


def search_files_with_pattern(path, pattern):
    res = []
    for root, _dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                res.append(os.path.join(root, name))
    return res
    

def combine_stats_files():
    csv_files = search_files_with_pattern(SAVE_PATH, "*_stats.csv")
    csv_files.sort()    
    combined_df = pd.concat([pd.read_csv(file) for file in csv_files], ignore_index = True)
    combined_df.to_csv(COMBINED_CSV, index = False)

    # TODO: need combined stats?
    txt_files = search_files_with_pattern(SAVE_PATH, "*_stats.txt")
    txt_files.sort()
    with open("combined_stats.txt", "w") as out_f:
        for file in txt_files:
            with open(file) as in_f:
                out_f.write(in_f.read())


def clean_combined_file():
    combined_df = pd.read_csv("combined_stats.csv")
    clean_df = combined_df[(combined_df["size"] != 0) & (combined_df["extension"] != 0)]
    clean_df.to_csv("cleaned_stats.csv", index = False)
    # TODO: optionally remove non .hs files
    # only_hs_df = clean_df[clean_df["extension"] == ".hs"]
    # only_hs_df.to_csv("cleaned_stats.csv", index = False)


def make_plots():
    df = pd.read_csv("cleaned_stats.csv")

    # Simple version 
    # df["color"] = df["extension"].apply(lambda x: "C0" if x == ".hs" else "C1")
    # plot_1 = df.plot.scatter(
    #     x = "total_time", y = "parser_time",
    #     c = "color", alpha = 0.5,
    #     xlabel = "log Total time (ms)",
    #     ylabel = "log Parser time (ms)",
    #     title = "Parser time vs Total time")
    # plot_1.set(xscale = "log", yscale = "log")
    # plot_1.get_figure().savefig("plot_parser_vs_total.png")

    # plot_2 = df.plot.scatter(
    #     x = "total_time", y = "parser_percentage",
    #     c = "color", alpha = 0.5,
    #     xlabel = "log Total time (ms)",
    #     ylabel = "log Parser percentage (%)",
    #     title = "Parser percentage vs Total time")
    # plot_2.set(xscale = "log", yscale = "log")
    # plot_2.get_figure().savefig("plot_parser_pct_vs_total.png")

    # plot_3 = df.plot.scatter(
    #     x = "size", y = "parser_time",
    #     c = "color", alpha = 0.5,
    #     xlabel = "log Size (bytes)",
    #     ylabel = "log Parser time (ms)",
    #     title = "Parser time vs Size")
    # plot_3.set(xscale = "log", yscale = "log")
    # plot_3.get_figure().savefig("plot_parser_vs_size.png")

    # plot_4 = df.plot.scatter(
    #     x = "size", y = "parser_percentage",
    #     c = "color", alpha = 0.5,
    #     xlabel = "log Size (bytes)",
    #     ylabel = "log Parser percentage (%)",
    #     title = "Parser percentage vs Size")
    # plot_4.set(xscale = "log", yscale = "log")
    # plot_4.get_figure().savefig("plot_parser_pct_vs_size.png")

    # Complex version with different groups
    hs_df = df[df["extension"] == ".hs"]
    other_df = df[df["extension"] != ".hs"]

    fig1, ax1 = plt.subplots()
    ax1.scatter(hs_df["total_time"], hs_df["parser_time"],
                color = CF_blue, marker = "o", alpha = 0.5, label = ".hs")
    ax1.scatter(other_df["total_time"], other_df["parser_time"],
                color = CF_vermillion, marker = "X", alpha = 0.5, label = "other")
    ax1.set(xscale = "log", yscale = "log")
    ax1.grid(linestyle = "--", linewidth = 0.5)
    ax1.set(xlabel = "Total time (ms)", ylabel = "Parser time (ms)",
            title = "Parser time vs Total time")
    ax1.legend()
    fig1.savefig("plot_parser_vs_total.png")

    fig2, ax2 = plt.subplots()
    ax2.scatter(hs_df["total_time"], hs_df["parser_percentage"],
                color = CF_blue, marker = "o", alpha = 0.5, label = ".hs")
    ax2.scatter(other_df["total_time"], other_df["parser_percentage"],
                color = CF_vermillion, marker = "X", alpha = 0.5, label = "other")
    ax2.set(xscale = "log", yscale = "log")
    ax2.grid(linestyle = "--", linewidth = 0.5)
    ax2.set(xlabel = "Total time (ms)", ylabel = "Percentage of time spent on parsing (%)",
            title = "Percentage of time spent on parsing vs Total time")
    ax2.legend()
    fig2.savefig("plot_parser_pct_vs_total.png")

    fig3, ax3 = plt.subplots()
    ax3.scatter(hs_df["size"], hs_df["parser_time"],
                color = CF_blue, marker = "o", alpha = 0.5, label = ".hs")
    ax3.scatter(other_df["size"], other_df["parser_time"],
                color = CF_vermillion, marker = "X", alpha = 0.5, label = "other")
    ax3.set(xscale = "log", yscale = "log")
    ax3.grid(linestyle = "--", linewidth = 0.5)
    ax3.set(xlabel = "Size (bytes)", ylabel = "Parser time (ms)",
            title = "Parser time vs Size")
    ax3.legend()
    fig3.savefig("plot_parser_vs_size.png")

    fig4, ax4 = plt.subplots()
    ax4.scatter(hs_df["size"], hs_df["parser_percentage"],
                color = CF_blue, marker = "o", alpha = 0.5, label = ".hs")
    ax4.scatter(other_df["size"], other_df["parser_percentage"],
                color = CF_vermillion, marker = "X", alpha = 0.5, label = "other")
    ax4.set(xscale = "log", yscale = "log")
    ax4.grid(linestyle = "--", linewidth = 0.5)
    ax4.set(xlabel = "Size (bytes)", ylabel = "Percentage of time spent on parsing (%)",
            title = "Percentage of time spent on parsing vs Size")
    ax4.legend()
    fig4.savefig("plot_parser_pct_vs_size.png")


if __name__ == "__main__":
    timings_df = read_and_clean_timings("aeson-2.2.2.0.json")
    stats = calculate_totals_and_stats(timings_df)