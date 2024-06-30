from collect_sources import get_top_packages, download_sources, extract_sources, build_sources
from collect_timing import calculate_for_packages, combine_stats_files, clean_combined_file, make_plots


if __name__ == "__main__":
    # links = get_top_packages(20)
    # # links = links[1:] # Omitting the `base` package
    # files = download_sources(links)
    # extract_sources(files)
    # dirs = list(map(lambda f: f.replace(".tar.gz", ""), files))
    # json_files = build_sources(dirs)
    # calculate_for_packages(json_files)
    # combine_stats_files()
    # clean_combined_file()
    make_plots()