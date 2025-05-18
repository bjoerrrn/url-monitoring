#!/usr/bin/env python3

# v1.2.0
# url-monitoring - pushover version
# based on: https://github.com/bjoerrrn/url-monitoring
# Modified to use Pushover instead of Discord
# Licensed under GNU GPL version 3.0 or later

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import json
import requests
import shlex
import urllib3
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configurations
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "url-monitor.credo")
FAILURE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "failures.json")
FAILURE_THRESHOLD = 5
TIMEOUT = 10
RETRY_COUNT = 2
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "url-monitor.log")

# Pushover credentials
PUSHOVER_TOKEN = "xxx"
PUSHOVER_USER = "xxx"

# Set up logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True
)

def load_failures():
    if os.path.exists(FAILURE_FILE):
        try:
            with open(FAILURE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            logging.error("Failed to parse failures.json, resetting...")
            print("[ERROR] Corrupted failures.json, resetting failure tracking.")
            return {}
    return {}

def save_failures(failures):
    try:
        with open(FAILURE_FILE, "w") as f:
            json.dump(failures, f, indent=2)
    except IOError as e:
        logging.error(f"Failed to save failures.json: {e}")
        print(f"[ERROR] Unable to save failure data: {e}")

def is_internal_ip(url):
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname
    return hostname and hostname.startswith("192.168.178.")

def load_urls():
    urls = []
    if not os.path.exists(CONFIG_FILE):
        logging.error(f"Config file {CONFIG_FILE} not found.")
        print(f"[ERROR] Config file {CONFIG_FILE} not found.")
        return urls
    try:
        with open(CONFIG_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = shlex.split(line)
                    if len(parts) < 2:
                        logging.warning(f"Invalid line in config: {line}")
                        print(f"[WARNING] Skipping invalid config line: {line}")
                        continue
                    description, url = parts[:2]
                    keyword = parts[2] if len(parts) > 2 else None
                    urls.append({"description": description, "url": url, "keyword": keyword})
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        print(f"[ERROR] Could not load config file: {e}")
    return urls

def check_url(url):
    verify_ssl = not is_internal_ip(url)
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            logging.info(f"Checking {url} (Attempt {attempt}/{RETRY_COUNT})")
            print(f"[INFO] Checking {url} (Attempt {attempt}/{RETRY_COUNT})")
            response = requests.get(url, timeout=TIMEOUT, verify=verify_ssl)
            if response.status_code in [200, 401]:
                return True, response.text
        except requests.RequestException as e:
            logging.warning(f"Failed attempt {attempt} for {url}: {e}")
            print(f"[WARNING] {url} failed (Attempt {attempt})")
    return False, None

def keyword_found(content, keyword):
    if not content or not keyword:
        return False
    keyword = keyword.lower()
    soup = BeautifulSoup(content, "html.parser")
    text_only = soup.get_text().lower()
    return keyword in text_only

def notify_pushover(message):
    logging.info(f"NOTIFY: {message}")
    print(f"[NOTIFY] {message}")
    try:
        requests.post("https://api.pushover.net/1/messages.json", data={
            "token": PUSHOVER_TOKEN,
            "user": PUSHOVER_USER,
            "message": message
        })
    except requests.RequestException as e:
        logging.error(f"Pushover notification failed: {e}")
        print(f"[ERROR] Failed to send Pushover notification: {e}")

def monitor():
    failures = load_failures()
    urls = load_urls()

    for entry in urls:
        description = entry["description"]
        url = entry["url"]
        keyword = entry["keyword"]

        print(f"\n[INFO] Checking {description} ({url})...")
        reachable, content = check_url(url)
        keyword_missing = keyword and reachable and not keyword_found(content, keyword)

        if url not in failures:
            failures[url] = {"failures": 0, "notified_down": False, "notified_up": False}

        failure_count = failures[url]["failures"]
        notified_down = failures[url]["notified_down"]
        notified_up = failures[url]["notified_up"]

        if not reachable or keyword_missing:
            failure_count += 1
            logging.warning(f"{description} ({url}) failure count: {failure_count}/{FAILURE_THRESHOLD}")
            print(f"[WARNING] {description} ({url}) failure count: {failure_count}/{FAILURE_THRESHOLD}")

            if failure_count >= FAILURE_THRESHOLD and not notified_down:
                msg = f"❌ {description} ({url})" if not reachable else f"⚠️ {description} ({url}) MISSING '{keyword}'"
                notify_pushover(msg)
                failures[url]["notified_down"] = True
                failures[url]["notified_up"] = False

            failures[url]["failures"] = failure_count

        else:
            if failure_count >= FAILURE_THRESHOLD and not notified_up:
                logging.info(f"{description} ({url}) RECOVERED! Sending ✅ notification.")
                print(f"[INFO] {description} ({url}) RECOVERED! Sending ✅ notification.")
                notify_pushover(f"✅ {description} ({url})")
                failures[url]["notified_up"] = True
                failures[url]["notified_down"] = False

            logging.info(f"{description} ({url}) is UP (Failures Reset).")
            print(f"[INFO] {description} ({url}) is UP (Failures Reset).")
            failures[url]["failures"] = 0

    save_failures(failures)

if __name__ == "__main__":
    print("\n[INFO] Starting URL monitor...\n")
    monitor()
    print("\n[INFO] Monitoring completed.\n")
