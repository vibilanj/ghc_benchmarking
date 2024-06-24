import textwrap
import os
import fnmatch
import json5
import pandas as pd

SAVE_PATH = "timing_data/"
SOURCES_PATH = "sources/"
   

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
    combined_df.to_csv("combined_stats.csv", index = False)

    txt_files = search_files_with_pattern(SAVE_PATH, "*_stats.txt")
    txt_files.sort()
    with open("combined_stats.txt", "w") as out_f:
        for file in txt_files:
            with open(file) as in_f:
                out_f.write(in_f.read())


if __name__ == "__main__":
    # timings_df = read_and_clean_timings("aeson-2.2.2.0.json")
    # stats = calculate_totals_and_stats(timings_df)
    combine_stats_files()