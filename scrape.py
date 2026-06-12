import os
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# ==========================================
# CONFIG
# ==========================================

BASE_URL = "YOUR_COMPANY_WEBSITE_URL_HERE"

urls = [
    BASE_URL,
    urljoin(BASE_URL, "/about"),
    urljoin(BASE_URL, "/services"),
    urljoin(BASE_URL, "/products"),
    urljoin(BASE_URL, "/careers"),
    urljoin(BASE_URL, "/contact"),
]

# ==========================================
# CREATE KNOWLEDGE FOLDER
# ==========================================

os.makedirs(
    "knowledge",
    exist_ok=True
)

# ==========================================
# SCRAPE PAGES
# ==========================================

for url in urls:

    print(f"Scraping: {url}")

    try:

        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent":
                "Mozilla/5.0"
            }
        )

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        for tag in soup.find_all(
            ["form", "input", "button", "select", "textarea"]
        ):
            tag.decompose()

        for tag in soup([
            "script",
            "style",
            "nav",
            "header",
            "footer"
        ]):
            tag.decompose()

        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find("body")
        )

        text = main_content.get_text(
            separator="\n",
            strip=True
        )

        # ----------------------------------
        # CREATE FILE NAME
        # ----------------------------------

        path = urlparse(url).path

        if path == "" or path == "/":
            filename = "home.txt"

        else:
            filename = (
                path.strip("/")
                .replace("/", "_")
                + ".txt"
            )

        file_path = os.path.join(
            "knowledge",
            filename
        )

        print(
            f"{filename}: {len(text)} chars"
        )
        
        # ----------------------------------
        # SAVE FILE
        # ----------------------------------

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(text)

        print(
            f"Saved: {file_path}"
        )

    except Exception as e:

        print(
            f"Failed: {url}"
        )

        print(e)

print("\nScraping Complete!")