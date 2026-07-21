"""CVM ingest smoke test (no network — pure parsing/logic checks).

Covers:
  - cvm_processor.load_quotas: CNPJ filtering, subclass disambiguation,
    VL_QUOTA precision (no rescaling — see cvm_downloader's docstring on
    why the raw file needs no /1e12 normalization)
  - cvm_processor.missing_cnpjs
  - cvm_downloader.resolve_month: explicit month, validation, and the
    default-to-latest logic and cache freshness (network call swapped out, no live
    request needed)

Run:  python tests/cvm_ingest_test.py   (exits non-zero on failure)
"""

import os
import sys
import tempfile

# Allow running from the repo root or the tests/ dir.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cvm_downloader  # noqa: E402
import cvm_processor  # noqa: E402

# Mirrors the real inf_diario_fi column layout (verified against a live
# June/2026 CVM file): one single-class fund, one fund with two subclasses
# sharing a CNPJ+date, and one fund that won't be in the requested list.
_SAMPLE_CSV = """TP_FUNDO_CLASSE;CNPJ_FUNDO_CLASSE;ID_SUBCLASSE;DT_COMPTC;VL_TOTAL;VL_QUOTA;VL_PATRIM_LIQ;CAPTC_DIA;RESG_DIA;NR_COTST
CLASSES - FIF;00.017.024/0001-53;;2026-06-01;1127873.60;43.453590600000;1191031.59;0.00;0.00;1
CLASSES - FIF;00.888.897/0001-31;RBMFN1747320951;2026-06-01;30987654.85;71.165937944006;30973968.70;37400.00;20000.00;1
CLASSES - FIF;00.888.897/0001-31;MZMRC1747322915;2026-06-01;615489950.68;70.905126633904;615405398.18;1915360.08;557207.04;10993
CLASSES - FIF;11.111.111/0001-11;;2026-06-01;100.00;10.000000000000;100.00;0.00;0.00;1
"""

_REQUESTED = ["00.017.024/0001-53", "00.888.897/0001-31", "99.999.999/9999-99"]


def _load_sample(requested):
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(_SAMPLE_CSV)
        return cvm_processor.load_quotas(path, requested)
    finally:
        os.remove(path)


def test_load_quotas_filters_and_disambiguates_subclasses():
    df = _load_sample(_REQUESTED)

    assert list(df.columns) == cvm_processor.OUTPUT_COLUMNS, list(df.columns)
    # 1 row (single-class fund) + 2 rows (two subclasses) = 3.
    # 11.111.111/0001-11 isn't requested -> excluded. 99.999.999/9999-99
    # is requested but absent from the CSV -> contributes 0 rows.
    assert df.shape == (3, len(cvm_processor.OUTPUT_COLUMNS)), df.shape

    single = df[df["CNPJ"] == "00.017.024/0001-53"].iloc[0]
    assert single["Valor cota"] == 43.4535906, single["Valor cota"]
    assert single["Subclasse"] == "", repr(single["Subclasse"])

    subs = df[df["CNPJ"] == "00.888.897/0001-31"]
    assert len(subs) == 2, "both subclasses must survive, not collapse"
    assert set(subs["Subclasse"]) == {"RBMFN1747320951", "MZMRC1747322915"}
    assert subs["Valor cota"].nunique() == 2, "each subclass keeps its own quota"


def test_missing_cnpjs():
    df = _load_sample(_REQUESTED)
    missing = cvm_processor.missing_cnpjs(df, _REQUESTED)
    assert missing == ["99.999.999/9999-99"], missing


def test_resolve_month_explicit_and_validation():
    assert cvm_downloader.resolve_month("202606") == "202606"
    try:
        cvm_downloader.resolve_month("2026")
        raise AssertionError("expected ValueError for a malformed month")
    except ValueError:
        pass


def test_resolve_month_defaults_to_latest():
    original = cvm_downloader.list_available_months
    cvm_downloader.list_available_months = lambda: ["202604", "202605", "202606"]
    try:
        assert cvm_downloader.resolve_month(None) == "202606"
    finally:
        cvm_downloader.list_available_months = original


def test_cache_freshness():
    from datetime import date
    import os
    import tempfile
    from pathlib import Path

    today = date.today()
    current = today.year * 100 + today.month
    previous = current - 1 if current % 100 > 1 else (current // 100 - 1) * 100 + 12
    old_month = str(previous - 100)  # a year ago — immutable on CVM's side

    with tempfile.TemporaryDirectory() as tmp:
        zp = Path(tmp) / "x.zip"
        zp.write_bytes(b"z")
        # downloaded today → fresh for any month
        assert cvm_downloader._cache_is_fresh(zp, str(current))
        assert cvm_downloader._cache_is_fresh(zp, old_month)
        # downloaded 3 days ago → stale for current/previous, fine for old
        stale = zp.stat().st_mtime - 3 * 86400
        os.utime(zp, (stale, stale))
        assert not cvm_downloader._cache_is_fresh(zp, str(current))
        assert not cvm_downloader._cache_is_fresh(zp, str(previous))
        assert cvm_downloader._cache_is_fresh(zp, old_month)


def main():
    test_load_quotas_filters_and_disambiguates_subclasses()
    test_missing_cnpjs()
    test_resolve_month_explicit_and_validation()
    test_resolve_month_defaults_to_latest()
    test_cache_freshness()
    print("cvm ingest smoke tests OK")


if __name__ == "__main__":
    main()
