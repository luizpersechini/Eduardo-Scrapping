"""
CVM Open Data Downloader
Downloads and caches monthly inf_diario_fi fund-quota files from
dados.cvm.gov.br — CVM open data, no scraping or anti-bot evasion needed,
just a government-published bulk CSV per month covering every fund.
"""

import logging
import re
import zipfile
from datetime import date
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import config

logger = logging.getLogger(__name__)

_MONTH_RE = re.compile(r"inf_diario_fi_(\d{6})\.zip")


def list_available_months() -> list:
    """Return sorted YYYYMM strings for every month CVM currently publishes."""
    with urlopen(f"{config.CVM_BASE_URL}/") as resp:
        html = resp.read().decode("utf-8", errors="replace")
    months = sorted(set(_MONTH_RE.findall(html)))
    if not months:
        raise RuntimeError(
            "No inf_diario_fi_*.zip files found in CVM directory listing"
        )
    return months


def resolve_month(month: str = None) -> str:
    """Pick the target month. An explicit `month` (YYYYMM) wins; otherwise
    default to the LATEST published month. The current month's file is
    partial (CVM appends to it daily), but that's what the user expects:
    "no month given" = the most recent data available."""
    if month:
        if not re.fullmatch(r"\d{6}", month):
            raise ValueError(f"month must be YYYYMM, got {month!r}")
        return month
    return list_available_months()[-1]


def _cache_dir() -> Path:
    d = Path(config.CVM_CACHE_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cache_is_fresh(dest: Path, month: str) -> bool:
    """Whether the cached zip for `month` can be reused.

    CVM appends rows to the current month's file every business day (and
    the previous month's can still receive late restatements), so those
    two are only "fresh" if downloaded today. Older months never change —
    cache them forever."""
    today = date.today()
    current = today.year * 100 + today.month
    previous = current - 1 if current % 100 > 1 else (current // 100 - 1) * 100 + 12
    if int(month) < previous:
        return True
    return date.fromtimestamp(dest.stat().st_mtime) == today


def download_month(month: str) -> Path:
    """Download (or reuse the cached copy of) the zip for `month` (YYYYMM).
    Returns the zip path. Recent months (current + previous) are re-downloaded
    once per day — CVM updates them daily, and a stale cache silently freezes
    the data at whatever day it was first fetched."""
    fname = config.CVM_FILENAME_PATTERN.format(yyyymm=month)
    dest = _cache_dir() / fname
    if dest.exists() and dest.stat().st_size > 0 and _cache_is_fresh(dest, month):
        logger.info("CVM zip already cached: %s", dest)
        return dest

    url = f"{config.CVM_BASE_URL}/{fname}"
    logger.info("Downloading %s", url)
    try:
        with urlopen(url) as resp:
            data = resp.read()
    except URLError as e:
        raise RuntimeError(f"Failed to download {url}: {e}") from e

    # Write-then-replace so a crash mid-download can't leave a truncated file
    # that a later run mistakes for a valid cache hit. replace() (not rename())
    # because the daily refresh overwrites an existing zip, and on Windows
    # rename() refuses to clobber (WinError 183).
    tmp = dest.with_suffix(".zip.part")
    tmp.write_bytes(data)
    tmp.replace(dest)
    logger.info("Saved %s (%d bytes)", dest, len(data))
    return dest


def extract_csv(zip_path: Path) -> Path:
    """Extract the CSV inside `zip_path` into the cache dir. Skipped only if
    the extracted CSV is at least as new as the zip — a re-downloaded zip
    must overwrite the old CSV, or the fresh download would be ignored.
    Returns the CSV path."""
    with zipfile.ZipFile(zip_path) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not names:
            raise RuntimeError(f"No CSV found inside {zip_path}")
        name = names[0]
        dest = _cache_dir() / name
        if not dest.exists() or dest.stat().st_mtime < zip_path.stat().st_mtime:
            zf.extract(name, path=_cache_dir())
    return dest


def get_month_csv(month: str = None) -> Path:
    """End-to-end: resolve the target month, download its zip (cached),
    extract the CSV (cached). Returns the CSV path."""
    resolved = resolve_month(month)
    zip_path = download_month(resolved)
    return extract_csv(zip_path)
