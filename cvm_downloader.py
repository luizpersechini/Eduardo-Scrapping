"""
CVM Open Data Downloader
Downloads and caches monthly inf_diario_fi fund-quota files from
dados.cvm.gov.br — CVM open data, no scraping or anti-bot evasion needed,
just a government-published bulk CSV per month covering every fund.
"""

import logging
import re
import zipfile
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
        raise RuntimeError("No inf_diario_fi_*.zip files found in CVM directory listing")
    return months


def resolve_month(month: str = None) -> str:
    """Pick the target month. An explicit `month` (YYYYMM) wins; otherwise
    default to the second-to-last published month — CVM's current month is
    usually incomplete (published on the 3rd business day), matching how
    Eduardo picks it by hand."""
    if month:
        if not re.fullmatch(r"\d{6}", month):
            raise ValueError(f"month must be YYYYMM, got {month!r}")
        return month
    available = list_available_months()
    return available[-2] if len(available) >= 2 else available[-1]


def _cache_dir() -> Path:
    d = Path(config.CVM_CACHE_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return d


def download_month(month: str) -> Path:
    """Download (or reuse the cached copy of) the zip for `month` (YYYYMM).
    Returns the zip path."""
    fname = config.CVM_FILENAME_PATTERN.format(yyyymm=month)
    dest = _cache_dir() / fname
    if dest.exists() and dest.stat().st_size > 0:
        logger.info("CVM zip already cached: %s", dest)
        return dest

    url = f"{config.CVM_BASE_URL}/{fname}"
    logger.info("Downloading %s", url)
    try:
        with urlopen(url) as resp:
            data = resp.read()
    except URLError as e:
        raise RuntimeError(f"Failed to download {url}: {e}") from e

    # Write-then-rename so a crash mid-download can't leave a truncated file
    # that a later run mistakes for a valid cache hit.
    tmp = dest.with_suffix(".zip.part")
    tmp.write_bytes(data)
    tmp.rename(dest)
    logger.info("Saved %s (%d bytes)", dest, len(data))
    return dest


def extract_csv(zip_path: Path) -> Path:
    """Extract the CSV inside `zip_path` into the cache dir (no-op if already
    extracted). Returns the CSV path."""
    with zipfile.ZipFile(zip_path) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not names:
            raise RuntimeError(f"No CSV found inside {zip_path}")
        name = names[0]
        dest = _cache_dir() / name
        if not dest.exists():
            zf.extract(name, path=_cache_dir())
    return dest


def get_month_csv(month: str = None) -> Path:
    """End-to-end: resolve the target month, download its zip (cached),
    extract the CSV (cached). Returns the CSV path."""
    resolved = resolve_month(month)
    zip_path = download_month(resolved)
    return extract_csv(zip_path)
