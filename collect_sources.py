import requests
import subprocess
import urllib.request
from bs4 import BeautifulSoup


BASE_URL = "https://hackage.haskell.org"


def get_top_packages(n):
    # Get the top n packages (by reverse dependencies) from Hackage
    url = f"{BASE_URL}/packages/reverse"
    response = requests.get(url, timeout = 120)
    soup = BeautifulSoup(response.text, "html.parser")
    
    table = soup.find("table")
    rows = table.find_all("tr")
    links = []
    for row in rows[-n:]:
        package = row.find("td")
        name = package.text
        link = package.find("a")["href"]
        links.append((name, link))

    links.reverse()
    return links


def download_sources(links):
    # Download the sources of the top n packages
    files = []
    for _, link in links:
        url = f"{BASE_URL}{link}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        downloads = soup.find("div", id = "downloads")
        filename = downloads.find("a").text
        source_url = downloads.find("a")["href"]
        
        urllib.request.urlretrieve(f"{BASE_URL}{source_url}", f"sources/{filename}")
        # download_cmd = f"wget {BASE_URL}{source_url} -P sources/"
        # subprocess.run(download_cmd, shell = True)

        files.append(filename)

    return files


def extract_sources(files):
    for file in files:
        command = f"tar -xvzf sources/{file} -C sources/"
        subprocess.run(command, shell = True)


def build_sources(dirs):
    json_files = []
    failed = []
    for dir in dirs:
        build_cmd = 'cabal clean && cabal build all --ghc-options "-ddump-to-file -ddump-timings"'
        result = subprocess.run(build_cmd, shell = True, cwd = f"sources/{dir}")
        if result.returncode != 0:
            failed.append((dir, "failed to build"))
            continue

        report_cmd = "../../time-ghc-modules/time-ghc-modules"
        result = subprocess.run(report_cmd, shell = True, cwd = f"sources/{dir}", capture_output = True)
        if result.returncode != 0:
            failed.append((dir, "failed to generate report"))
            continue
        report_loc = result.stdout.decode().strip()
        
        # copy_cmd = f"cp {report_loc} reports/{dir}.html"
        # subprocess.run(copy_cmd, shell = True)

        json_loc = report_loc.replace("/report.html", "/data.json")
        copy_cmd = f"cp {json_loc} timing_data/{dir}.json"
        json_files.append(f"{dir}.json")
        subprocess.run(copy_cmd, shell = True)
        
    print("\nFAILED PACKAGES: ", failed)
    return json_files


if __name__ == "__main__":
    pass
