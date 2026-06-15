import os
import requests
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
MAX_PAGES = 50


BASE_URL = "https://www.adcountymedia.com"

visited = set()
to_visit = {BASE_URL}


os.makedirs(
    "knowledge",
    exist_ok=True
)


while to_visit:

    url = to_visit.pop()

    if url in visited:
        continue

    visited.add(url)

    if len(visited) > MAX_PAGES:
        break

    print(f"Scraping: {url}")

    try:

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True
            )

            page = browser.new_page()

            page.goto(
                url,
                wait_until="networkidle"
            )

            page.wait_for_timeout(3000)

            html = page.content()

            browser.close()

        soup = BeautifulSoup(
            html,
            "html.parser"
        )
        
        for link in soup.find_all("a", href=True):

            href = link["href"]

            full_url = urljoin(
                BASE_URL,
                href
            )

            parsed = urlparse(full_url)

            if (
                parsed.netloc ==
                urlparse(BASE_URL).netloc
            ):

                clean_url = (
                    parsed.scheme
                    + "://"
                    + parsed.netloc
                    + parsed.path
                )

                if clean_url not in visited:
                    to_visit.add(clean_url)
                
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
        
        if any(
            x in url.lower()
            for x in [
                ".jpg",
                ".jpeg",
                ".png",
                ".svg",
                ".pdf",
                ".zip",
                "#"
            ]
        ):
            continue
        

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