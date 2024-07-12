from collect_sources import fetch_top_package_links, download_sources, extract_sources, build_sources
from timing_analysis import calculate_statistics_for_packages
from plot_generation import make_module_plots, make_package_plots, make_aggregated_plot


if __name__ == "__main__":
    # Fetching sources, building them and generating timing reports
    # links = fetch_top_package_links(20)
    # links = links[1:] # Omitting the `base` package
    # files = download_sources(links)
    # extract_sources(files)
    # dirs = list(map(lambda f: f.replace(".tar.gz", ""), files))
    # json_files = build_sources(dirs)

    # Calculating statistics
    # calculate_statistics_for_packages(json_files)

    # Generating Plots
    # make_module_plots()
    # make_package_plots()
    make_aggregated_plot()