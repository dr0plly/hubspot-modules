import os
import json
import time
import logging
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# =========================
# CONFIGURATION
# =========================

URLS = [
    # "https://www.example.com/holiday-page-1",
]

DATA_DIR = "data"
WAIT_TIME = 10

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)


# =========================
# LOGGING SETUP
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# =========================
# UTILITY FUNCTIONS
# =========================

def get_slug_from_url(url: str) -> str:
    """
    Extract slug from URL path.
    """
    path = urlparse(url).path.rstrip("/")
    return path.split("/")[-1]


def sanitize_filename(text: str) -> str:
    """
    Convert text to lowercase and replace spaces with hyphens.
    """
    return text.strip().lower().replace(" ", "-")


def init_driver() -> webdriver.Chrome:
    """
    Initialize headless Selenium Chrome driver.
    """
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")

    return webdriver.Chrome(options=options)


# =========================
# SCRAPING FUNCTIONS
# =========================

def extract_h1_data(soup: BeautifulSoup) -> tuple[str, str]:
    """
    Extract:
    - state text (before <br>)
    - full H1 text (all text, <br> removed)
    """
    h1 = soup.find("h1")
    if not h1:
        return "", ""

    h1_texts = list(h1.stripped_strings)

    state_text = h1_texts[0] if h1_texts else ""
    full_text = " ".join(h1_texts)

    return state_text.strip(), full_text.strip()


def extract_table_data(soup: BeautifulSoup) -> list[dict]:
    """
    Extract holiday table rows.
    """
    holidays = []
    table = soup.find("table", class_="css-1uljcf2")

    if not table:
        return holidays

    rows = table.find_all("tr")

    for row in rows:
        cols = row.find_all("td")
        if len(cols) != 4:
            continue

        holidays.append({
            "date": cols[0].get_text(strip=True),
            "day": cols[1].get_text(strip=True),
            "name": cols[2].get_text(strip=True),
            "type": cols[3].get_text(strip=True),
        })

    return holidays


def extract_pdf_link(driver: webdriver.Chrome, url: str) -> str:
    """
    Click the PDF button and extract the final opened URL.
    """
    driver.get(url)

    try:
        button = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.ID, "btn"))
        )

        original_window = driver.current_window_handle
        existing_windows = driver.window_handles

        button.click()

        WebDriverWait(driver, WAIT_TIME).until(
            lambda d: len(d.window_handles) > len(existing_windows)
        )

        new_window = [w for w in driver.window_handles if w != original_window][0]
        driver.switch_to.window(new_window)

        pdf_url = driver.current_url

        driver.close()
        driver.switch_to.window(original_window)

        return pdf_url

    except Exception as e:
        logging.error(f"PDF extraction failed: {e}")
        return ""


# =========================
# MAIN PROCESSING FUNCTION
# =========================

def process_url(driver: webdriver.Chrome, url: str) -> None:
    logging.info(f"Processing started: {url}")

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to fetch page: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    state, full_h1_text = extract_h1_data(soup)
    holidays = extract_table_data(soup)
    pdf_link = extract_pdf_link(driver, url)
    slug = get_slug_from_url(url)

    filename = sanitize_filename(state) + ".json"
    file_path = os.path.join(DATA_DIR, filename)

    data = {
        "state": state,
        "slug": slug,
        "meta": {
            "title": full_h1_text
        },
        "holidays": holidays,
        "pdf": pdf_link
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logging.info(f"JSON created: {file_path}")
    logging.info(f"Processing completed: {url}")


# =========================
# ENTRY POINT
# =========================

def main():
    driver = init_driver()

    try:
        for url in URLS:
            process_url(driver, url)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
