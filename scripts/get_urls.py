import requests
import xml.etree.ElementTree as ET

urls = [
    "https://isearch.gitbook.io/docs/sitemap-pages.xml",
    "https://opsis-pro.gitbook.io/docs/sitemap-pages.xml"
]

xml = requests.get(urls[0]).text + requests.get(urls[1]).text

root = ET.fromstring(xml)

urls = []

for loc in root.iter():
    if loc.tag.endswith("loc"):
        urls.append(loc.text)

print(f"Found {len(urls)} URLs\n")

for url in urls:
    print(url)