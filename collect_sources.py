"""
This file contains the functions that deal with fetching the sources from Hackage,
downloading them, extracting them, building them, generating timing reports and
copying the timing data to the corresponding directory.
"""

import os
import shutil
import subprocess
import urllib.request
from typing import List, Tuple

import requests
from bs4 import BeautifulSoup

from constants import SOURCES_DIR, TIMINGS_DIR

BASE_URL = "https://hackage.haskell.org"


def fetch_top_package_links(n: int) -> List[Tuple[str, str]]:
    """
    Fetches the top n packages from Hackage based on the number of reverse
    dependencies. The packages are listed in descending order of reverse
    dependencies.

    Args:
        n: The number of packages to fetch

    Returns:
        A list of tuples containing the package name and the link to the
        package on Hackage
    """

    # Fetch the reverse dependencies page
    url = f"{BASE_URL}/packages/reverse"
    response = requests.get(url, timeout = 120)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find the table containing the packages
    table = soup.find("table")
    rows = table.find_all("tr")
    links = []

    # Packages are listed in ascending order of reverse dependencies
    # We want the last n packages
    for row in rows[-n:]:
        package = row.find("td")
        name = package.text
        link = package.find("a")["href"]
        links.append((name, link))

    # Reverse the list so that the package with the most reverse dependencies
    # is first
    links.reverse()
    return links


def download_sources(links: List[Tuple[str, str]]) -> List[str]:
    """
    Downloads the source code tarballs from the given package links.

    Args:
        links: A list of tuples containing the package name and the link to the
               package on Hackage

    Returns:
        A list of the names of the downloaded files
    """

    # Create the sources directory if it doesn't exist
    os.makedirs(SOURCES_DIR, exist_ok = True)

    files = []
    for _, link in links:
        # Fetch the package page
        url = f"{BASE_URL}{link}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the download link
        downloads = soup.find("div", id = "downloads")
        filename = downloads.find("a").text
        source_url = downloads.find("a")["href"]
        
        # Download the tarball to the sources directory
        urllib.request.urlretrieve(f"{BASE_URL}{source_url}", os.path.join(SOURCES_DIR, filename))
        files.append(filename)

    # Return the list of downloaded files
    return files


def extract_sources(files: List[str]) -> None:
    """
    Extracts the source code from the downloaded tarballs.

    Args:
        files: A list of the names of the downloaded files

    Returns:
        None
    """

    for filename in files:
        # Extract the tarball to the sources directory
        file_path = os.path.join(SOURCES_DIR, filename)
        subprocess.run(["tar", "-xvzf", file_path, "-C", SOURCES_DIR], check = True)


def build_sources(dirs: List[str]) -> List[str]:
    """
    Builds the sources using cabal, generates the timing data and copies it to
    the timing data directory.

    Args:
        dirs: A list of directories containing the source code

    Returns:
        A list of the names of the generated JSON files
    """

    # Create the timings directory if it doesn't exist
    os.makedirs(TIMINGS_DIR, exist_ok = True)

    json_files = []
    failed = []
    for dir in dirs:
        source_dir = os.path.join(SOURCES_DIR, dir)

        # Clean the directory
        clean_cmd = ['cabal', 'clean']
        subprocess.run(clean_cmd, cwd = source_dir)

        # Build the sources with ddump-timings and ddump-to-file flags
        build_cmd = ['cabal', 'build', 'all', '--ghc-options', '-ddump-to-file -ddump-timings']
        build_result = subprocess.run(build_cmd, cwd = source_dir)
        if build_result.returncode != 0:
            failed.append((dir, "failed to build"))
            continue

        # Generate the timing report using the time-ghc-modules tool
        report_cmd = ["../../time-ghc-modules/time-ghc-modules"]
        result = subprocess.run(report_cmd, cwd = source_dir, capture_output = True)
        if result.returncode != 0:
            failed.append((dir, "failed to generate report"))
            continue
        report_loc = result.stdout.decode().strip()
        
        # Copy the JSON timing report to the timings directory
        json_loc = report_loc.replace("/report.html", "/data.json")
        json_dest = os.path.join(TIMINGS_DIR, f"{dir}.json")
        shutil.copy(json_loc, json_dest)
        json_files.append(f"{dir}.json")
        
    # Print the failed packages and return the list of JSON files
    print("\nFAILED PACKAGES: ", failed)
    return json_files
