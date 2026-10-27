#!/usr/bin/env python3
"""Download the latest SPIMEX oil PDF directly to the server."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

BASE_URL = "https://spimex.com/files/trades/result/pdf/oil"
DEFAULT_SUFFIX = "162000"
DEFAULT_LOOKBACK_DAYS = 5
DEFAULT_RETRIES = 3
DEFAULT_RETRY_DELAY = 60

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Referer": "https://spimex.com/markets/oil_products/trades/results/",
}


def build_url(report_date: date, suffix: str = DEFAULT_SUFFIX) -> tuple[str, str]:
    stamp = report_date.strftime("%Y%m%d")
    filename = f"oil_{stamp}{suffix}.pdf"
    return filename, f"{BASE_URL}/{filename}"


def is_valid_pdf(path: Path) -> bool:
    try:
        return path.is_file() and path.read_bytes().startswith(b"%PDF")
    except OSError:
        return False


def candidate_dates(lookback_days: int) -> list[date]:
    today = datetime.now().date()
    return [today - timedelta(days=offset) for offset in range(lookback_days + 1)]


def download_file(
    target_path: Path,
    url: str,
    retries: int,
    retry_delay: int,
    timeout: int,
    logger: logging.Logger,
) -> bool:
    for attempt in range(1, retries + 1):
        try:
            logger.info("Download attempt %s/%s: %s", attempt, retries, url)
            response = requests.get(url, headers=HEADERS, timeout=timeout)
            if response.status_code == 200 and response.content.startswith(b"%PDF"):
                target_path.write_bytes(response.content)
                logger.info("Saved %s (%s bytes)", target_path.name, len(response.content))
                return True
            logger.warning(
                "Unexpected response for %s: HTTP %s, first bytes=%r",
                target_path.name,
                response.status_code,
                response.content[:60],
            )
        except Exception as exc:
            logger.warning("Download error for %s: %s", target_path.name, exc)

        if attempt < retries:
            logger.info("Waiting %s seconds before retry", retry_delay)
            time.sleep(retry_delay)

    return False


def ensure_latest_pdf(
    save_dir: Path,
    lookback_days: int,
    retries: int,
    retry_delay: int,
    timeout: int,
    suffix: str,
    logger: logging.Logger,
) -> Path:
    save_dir.mkdir(parents=True, exist_ok=True)

    for report_date in candidate_dates(lookback_days):
        filename, url = build_url(report_date, suffix=suffix)
        target_path = save_dir / filename

        if is_valid_pdf(target_path):
            logger.info("Using existing PDF: %s", target_path)
            return target_path

        logger.info("Trying report date %s", report_date.strftime("%d.%m.%Y"))
        if download_file(target_path, url, retries, retry_delay, timeout, logger):
            return target_path

    raise RuntimeError("Could not download a valid SPIMEX PDF for any candidate date")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--save-dir", default="pdf_data")
    parser.add_argument("--lookback-days", type=int, default=DEFAULT_LOOKBACK_DAYS)
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES)
    parser.add_argument("--retry-delay", type=int, default=DEFAULT_RETRY_DELAY)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--suffix", default=DEFAULT_SUFFIX)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger = logging.getLogger("download_spimex")

    try:
        path = ensure_latest_pdf(
            save_dir=Path(args.save_dir),
            lookback_days=args.lookback_days,
            retries=args.retries,
            retry_delay=args.retry_delay,
            timeout=args.timeout,
            suffix=args.suffix,
            logger=logger,
        )
    except Exception as exc:
        logger.error("SPIMEX download failed: %s", exc)
        return 1

    logger.info("Ready PDF: %s", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
