from pathlib import Path
import requests

base_url = "https://filings.xbrl.org"  # FXO
# First 5000 files uploaded in June 2023
url = "https://filings.xbrl.org/api/filings?page[size]=5000&filter=[{%22name%22:%22date_added%22,%22op%22:%22ge%22,%22val%22:%222023-06-01%22},{%22name%22:%22date_added%22,%22op%22:%22lt%22,%22val%22:%222023-07-01%22}]"
response = requests.get(url)
datafxo = response.json()
for report in datafxo["data"]:
    json_url = report["attributes"]["json_url"]
    if json_url:
        url = base_url + json_url
        filename = url.split("/")[-1]
        try:
            response = requests.get(url)
        except Exception as e:
            print(f"ERROR: {filename}: {e}")
            continue

        filepath = Path("data") / filename
        with open(filepath, "wb") as f:
            f.write(response.content)
