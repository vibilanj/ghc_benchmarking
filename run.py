from collect_sources import fetch_top_package_links, download_sources, extract_sources, build_sources
from timing_analysis import calculate_statistics_for_packages, make_plots


if __name__ == "__main__":
    links = fetch_top_package_links(20)
    links = links[1:] # Omitting the `base` package
    files = download_sources(links)
    extract_sources(files)
    dirs = list(map(lambda f: f.replace(".tar.gz", ""), files))
    json_files = build_sources(dirs)
    calculate_statistics_for_packages(json_files)
    make_plots()