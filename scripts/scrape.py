import os
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from chatbot.database.database import SessionLocal
from chatbot.database.models import Document
from pathlib import Path
from chatbot.config import URLS_FILE
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

MAX_PAGES = 200

BASE_URL = "https://www.adcountymedia.com"

SKIP_PAGES = [
    "terms-and-conditions",
    "privacy-policy",
    "cookie-policy",
    "investors",
    "/v1/PDFFile/"
]

ALLOWED_PATHS = [
    "/products/",
    "/about-us",
    "/careers",
    "/contact",
]


SCRAPE_TARGETS = [
    {
        "mode": "adcounty",
        "urls": {BASE_URL},
    },
    {
        "mode": "gitbook",
        "urls": {
            line.strip()
            for line in URLS_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        } if URLS_FILE.exists() else set(),
    },
]

with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.set_default_timeout(60000)

    for target in SCRAPE_TARGETS:

        SCRAPE_MODE = target["mode"]
        to_visit = target["urls"]
        visited = set()

        if not to_visit:
            print(f"\nSkipping {SCRAPE_MODE} — no URLs to scrape.")
            continue

        print(f"\n{'='*50}")
        print(f"STARTING SCRAPE: {SCRAPE_MODE.upper()}")
        print(f"{'='*50}\n")

        while to_visit:

            url = to_visit.pop()

            if any(skip_page in url for skip_page in SKIP_PAGES):
                continue

            if url in visited:
                continue

            visited.add(url)

            if len(visited) > MAX_PAGES:
                break

            print(f"Scraping: {url}")

            try:

                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=60000
                )

                page.evaluate("""
                if (document.body) {
                    window.scrollTo(0, document.body.scrollHeight);
                }
                """)

                for _ in range(5):
                    page.evaluate("window.scrollBy(0, 2000)")
                    page.wait_for_timeout(1000)

                page.wait_for_timeout(2000)

                if SCRAPE_MODE == "adcounty" and "/products/" in url:

                    buttons = page.locator("[aria-expanded]")

                    count = buttons.count()

                    print(f"Found {count} accordions")

                    for i in range(count):
                        try:
                            button = buttons.nth(i)

                            expanded = button.get_attribute("aria-expanded")

                            if expanded == "false":
                                button.click(force=True)

                            page.wait_for_timeout(1000)

                        except Exception as e:
                            print(f"Accordion {i} failed: {e}")

                        page.wait_for_timeout(1000)

                page.wait_for_timeout(3000)

                tab_count = 0

                if SCRAPE_MODE == "adcounty" and "/products/" in url:

                    tab_elements = page.locator("[role='tab']")
                    tab_count = tab_elements.count()
                    print(f"Found {tab_count} tabs")

                all_tab_text = ""

                if tab_count > 0:

                    for i in range(tab_count):

                        try:

                            tab = tab_elements.nth(i)
                            tab_name = tab.inner_text()
                            print(f"Opening tab: {tab_name}")

                            tab.click(force=True)
                            page.wait_for_timeout(3000)

                            panel = page.locator("[role='tabpanel']")
                            panel.wait_for()
                            content = panel.inner_text()
                            all_tab_text += content

                        except Exception as e:
                            print(f"Failed tab {i}: {e}")

                html = page.content()
                soup = BeautifulSoup(html, "html.parser")

                if SCRAPE_MODE == "adcounty":

                    for link in soup.find_all("a", href=True):

                        href = link["href"]

                        if href.lower().endswith(".pdf"):
                            continue

                        full_url = urljoin(BASE_URL, href)
                        parsed = urlparse(full_url)

                        if parsed.netloc == urlparse(BASE_URL).netloc:

                            clean_url = (
                                parsed.scheme
                                + "://"
                                + parsed.netloc
                                + parsed.path.rstrip("/")
                            )

                            if not any(path in clean_url for path in ALLOWED_PATHS):
                                continue

                            if clean_url not in visited:
                                to_visit.add(clean_url)

                for tag in soup.find_all(
                    ["form", "input", "button", "select", "textarea"]
                ):
                    tag.decompose()

                for tag in soup(["script", "style"]):
                    tag.decompose()

                main_content = (
                    soup.find("main")
                    or soup.find("article")
                    or soup.find("body")
                )

                if not main_content:
                    continue

                if SCRAPE_MODE == "gitbook":
                    page_text = page.locator("main").inner_text()
                else:
                    page_text = main_content.get_text(separator="\n", strip=True)

                text = page_text

                if all_tab_text.strip():
                    text += "\n\n" + all_tab_text

                print(f"Extracted {len(text)} characters")

                if "bidcounty" in url.lower():
                    print(text[:3000])
                if "genwin" in url.lower():
                    print(text[:3000])
                if "isearchads" in url.lower():
                    print(text[:3000])
                if "gam360" in url.lower():
                    print(text[:3000])
                if "opsis" in url.lower():
                    print(text[:3000])
                if "seetv" in url.lower():
                    print(text[:3000])

                path = urlparse(url).path

                if SCRAPE_MODE == "gitbook":

                    filename = (
                        path.strip("/")
                        .replace("/", "_")
                        .replace("docs_", "")
                        + ".txt"
                    )

                else:

                    if path == "" or path == "/":
                        filename = "home.txt"
                    else:
                        filename = (
                            path.strip("/").replace("/", "_") + ".txt"
                        )

                print(f"Extracted {len(text)} characters")

                if any(
                    x in url.lower()
                    for x in [".jpg", ".jpeg", ".png", ".svg", ".pdf", ".zip", "#"]
                ):
                    continue

                page_title = soup.title.string.strip() if soup.title else url

                db = SessionLocal()

                source_type = (
                    "website"
                    if SCRAPE_MODE == "adcounty"
                    else "gitbook"
                )

                try :
                    existing = (
                        db.query(Document)
                        .filter(Document.url == url)
                        .first()
                    )

                    if existing:

                        existing.title = page_title
                        existing.content = text
                        existing.source = source_type

                        db.commit()

                    else:

                        doc = Document(
                            source=source_type,
                            title=page_title,
                            url=url,
                            content=text
                        )

                        db.add(doc)
                        db.commit()

                finally:
                    db.close()

                text = text.replace(
                    "Your browser does not support the video tag.",
                    ""
                )

                print(
                    f"Saved document → "
                    f"{page_title} "
                    f"({source_type})"
                )

            except Exception as e:
                print(f"Failed: {url}")
                print(e)

        print(f"\nFinished {SCRAPE_MODE.upper()} — {len(visited)} pages scraped.")

    browser.close()

print("\nAll scraping complete!")