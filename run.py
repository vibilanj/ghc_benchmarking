"""
This script is used to run the entire pipeline. It fetches the top 20 packages
by reverse dependencies from Hackage, downloads the sources, extracts them,
builds them, generates timing reports and plots the results.
"""

from collect_sources import (build_sources, download_sources, extract_sources,
                             fetch_top_package_links)
from plot_generation import (make_aggregated_plot, make_module_plots,
                             make_package_plots)
from timing_analysis import calculate_statistics_for_packages

if __name__ == "__main__":
    # Fetching sources, building them and generating timing reports
    links = fetch_top_package_links(50)
    # links = links[1:] # NOTE: Uncomment to omit the `base` package
    files = download_sources(links)
    extract_sources(files)
    dirs = list(map(lambda f: f.replace(".tar.gz", ""), files))
    json_files = build_sources(dirs)

    # Calculating statistics
    calculate_statistics_for_packages(json_files)

    # Generating Plots
    make_module_plots()
    make_package_plots()
    make_aggregated_plot()