import os
import requests
import subprocess
import shutil
import urllib.request
from bs4 import BeautifulSoup

from constants import SOURCES_DIR, TIMINGS_DIR 

BASE_URL = "https://hackage.haskell.org"

# Get the top n packages (by reverse dependencies) from Hackage
def fetch_top_package_links(n):
    url = f"{BASE_URL}/packages/reverse"
    response = requests.get(url, timeout = 120)
    soup = BeautifulSoup(response.text, "html.parser")
    
    table = soup.find("table")
    rows = table.find_all("tr")
    links = []
    # Packages are listed in ascneding order of reverse dependencies
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


# Download the source code tarballs from the given package links
def download_sources(links):
    os.makedirs(SOURCES_DIR, exist_ok = True)

    files = []
    for _, link in links:
        url = f"{BASE_URL}{link}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        downloads = soup.find("div", id = "downloads")
        filename = downloads.find("a").text
        source_url = downloads.find("a")["href"]
        
        urllib.request.urlretrieve(f"{BASE_URL}{source_url}", os.path.join(SOURCES_DIR, filename))
        files.append(filename)

    # Return the list of downloaded files
    return files


# Extract the source code from the downloaded tarballs
def extract_sources(files):
    for filename in files:
        file_path = os.path.join(SOURCES_DIR, filename)
        subprocess.run(["tar", "-xvzf", file_path, "-C", SOURCES_DIR], check = True)


# Builds the sources using cabal, generates the timing data and copies it to 
# the timing_data directory
def build_sources(dirs):
    os.makedirs(TIMINGS_DIR, exist_ok = True)
    json_files = []
    failed = []
    for dir in dirs:
        source_dir = os.path.join(SOURCES_DIR, dir)

        clean_cmd = ['cabal', 'clean']
        build_cmd = ['cabal', 'build', 'all', '--ghc-options', '-ddump-to-file -ddump-timings']
        subprocess.run(clean_cmd, cwd = source_dir)
        build_result = subprocess.run(build_cmd, cwd = source_dir)
        if build_result.returncode != 0:
            failed.append((dir, "failed to build"))
            continue

        report_cmd = ["../../time-ghc-modules/time-ghc-modules"]
        result = subprocess.run(report_cmd, cwd = source_dir, capture_output = True)
        if result.returncode != 0:
            failed.append((dir, "failed to generate report"))
            continue
        report_loc = result.stdout.decode().strip()
        
        json_loc = report_loc.replace("/report.html", "/data.json")
        json_dest = os.path.join(TIMINGS_DIR, f"{dir}.json")
        shutil.copy(json_loc, json_dest)
        json_files.append(f"{dir}.json")
        
    print("\nFAILED PACKAGES: ", failed)
    return json_files


if __name__ == "__main__":
    pass
