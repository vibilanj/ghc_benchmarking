"""
This file contains the functions that deal with reading, cleaning and computing
statistics from the timing data files. The statistics are computed for each module
and package and are written to CSV files.
"""

import fnmatch
import os
from typing import Any, Dict, List, Tuple

import json5
import pandas as pd

from constants import (MODULE_STATS_FILE, PACKAGE_STATS_FILE, SOURCES_DIR,
                       TIMINGS_DIR)


def read_json_file(file: str) -> Dict[str, Any]:
    """
    Read a JSON file using the json5 library. This is used to handle JSON files
    with comments and trailing commas as the standard json library does not
    support these features.

    Args:
        file: The path to the JSON file

    Returns:
        The contents of the JSON file as a dictionary
    """

    with open(file) as f:
        return json5.load(f)


def read_and_clean_timings(filename: str) -> pd.DataFrame:
    """
    Read the timings from a JSON file and clean them by removing the systool and
    hi/dyn_hi modules. Package names are added to the dataframe and the alloc
    column is removed. The cleaned timings are then written to a CSV file and
    returned as a dataframe.

    Args:
        filename: The name of the JSON file containing the timings

    Returns:
        A dataframe containing the cleaned timings data
    """

    # Read the timings from the JSON file
    file_path = os.path.join(TIMINGS_DIR, filename)
    data = read_json_file(file_path)
    timings_df = pd.DataFrame(data["data"])

    # Remove systool and hi/dyn_hi modules
    timings_df = timings_df[~timings_df["module"].isin(["systool"]) & ~timings_df["module"].str.endswith(("hi", "dyn_hi"))]

    # Add the package name to the dataframe and remove the alloc column
    package_name = filename.replace(".json", "")
    timings_df.insert(0, "package", package_name)
    timings_df.drop(["alloc"], axis = 1, inplace = True)

    # Write the cleaned timings to a CSV file and return the dataframe
    output_file = os.path.join(TIMINGS_DIR, f"{package_name}_timings.csv")
    timings_df.to_csv(output_file, index = False)
    return timings_df


def get_size_and_extension(package: str, module : str) -> Tuple[int, str]:
    """
    Get the size and extension of the file for a given module in a package. The
    function searches for the file in the package's source directory and its
    subdirectories. If the file is found, its size and extension are returned.

    Args:
        package: The name of the package
        module: The name of the module

    Returns:
        A tuple containing the size of the file in bytes and its extension
    """

    # Get the possible source directories for the package
    package_path = os.path.join(SOURCES_DIR, package)
    src_dirs = ["", "src", "lib"]

    # Split the module name into a list of path components and construct the search pattern
    module_path_list = module.split(".")
    module_path = os.path.join(*module_path_list[:-1]) if len(module_path_list) > 1 else ""
    search_pattern = f"{module_path_list[-1]}.*"

    # Search for the file in the package's possible source directories
    for src_dir in src_dirs:
        # Construct the search path and check if it exists
        search_path = os.path.join(package_path, src_dir, module_path)
        if not os.path.isdir(search_path):
            continue
    
        # Walk the directory and search for the file using the pattern
        for root, _dirs, files in os.walk(search_path):
            for name in files:
                # Check if the file matches the search pattern
                if fnmatch.fnmatch(name, search_pattern):
                    # Get the size and extension of the file and return them
                    file_path = os.path.join(root, name)
                    size = os.path.getsize(file_path)
                    extension = os.path.splitext(file_path)[1]
                    return size, extension

    # Print a message and return 0 and an empty string if the file was not found
    print(f"Could not find file for module {module} in package {package}.")
    return 0, ""


def compute_statistics(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute the statistics for a given dataframe corresponding to a package. The
    function calculates the total time, parser time, parser percentage, size and
    extension of the files for each module in the package. The statistics are then
    aggregated for each module and package and returned as dataframes.

    Args:
        df: The dataframe containing the timings data for a package

    Returns:
        Two dataframes containing the module and package statistics respectively
    """

    # Check if the dataframe is empty
    if df.empty:
        raise ValueError("Dataframe is empty.")

    module_stats = []
    modules = df["module"].unique()
    package_name = df["package"].iloc[0]

    # Module statistics
    for module in modules:
        # Get the size and extension of the file for the module
        module_size, module_extension = get_size_and_extension(package_name, module)
        if module_size == 0 and module_extension == "":
            continue

        # Calculate the total time, parser time and parser percentage for the module
        total_time = df[df["module"] == module]["time"].sum()
        parser_time = df[(df["module"] == module) & (df["phase"] == "Parser")]["time"].sum()
        parser_percentage = (parser_time / total_time) * 100
        
        # Create a dictionary with the module statistics and append it to the list
        stats = {
            "module": module,
            "total_time": total_time,
            "parser_time": parser_time,
            "parser_percentage": parser_percentage,
            "size": module_size,
            "extension": module_extension
        }
        module_stats.append(stats)

    # Create a dataframe from the list of module statistics and add the package name
    module_stats_df = pd.DataFrame(module_stats)
    module_stats_df.insert(0, "package", package_name)

    # Package statistics
    # Calculate the total time, parser time, parser percentage, average parser percentage,
    # geomean parser percentage and size for the package
    package_total_time = module_stats_df["total_time"].sum()
    package_parser_time = module_stats_df["parser_time"].sum()
    package_parser_percentage = (package_parser_time / package_total_time) * 100
    average_parser_percentage = module_stats_df["parser_percentage"].mean()
    geomean_parser_percentage = module_stats_df["parser_percentage"].prod() ** (1 / len(module_stats_df))
    package_size = module_stats_df["size"].sum()
    
    # Create a dictionary with the package statistics and convert it to a dataframe
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

    # Return the dataframes containing the module and package statistics
    return module_stats_df, package_stats_df


def calculate_statistics_for_packages(files: List[str]) -> None:
    """
    Calculate the statistics for the given list of timing data files. The function
    reads the timings from the files, cleans them, computes the statistics for each
    module and package, aggregates the statistics and writes them to CSV files.

    Args:
        files: A list of the names of the timing data files

    Returns:
        None
    """

    all_module_stats = []
    all_package_stats = []

    for file in files:
        # Read and clean the timings, compute the statistics and append them to the lists
        timings_df = read_and_clean_timings(file)
        module_stats_df, package_stats_df = compute_statistics(timings_df)
        all_module_stats.append(module_stats_df)
        all_package_stats.append(package_stats_df)

    # Concatenates the list of module statistics dataframes and writes them to a CSV file
    all_module_stats_df = pd.concat(all_module_stats, ignore_index = True)
    all_module_stats_df.to_csv(MODULE_STATS_FILE, index = False)

    # Concatenates the list of package statistics dataframes and writes them to a CSV file
    all_package_stats_df = pd.concat(all_package_stats, ignore_index = True)
    all_package_stats_df.to_csv(PACKAGE_STATS_FILE, index = False)
