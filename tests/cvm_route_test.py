"""CVM Streamlit route smoke test (no network — uses streamlit's AppTest).

Boots streamlit_app.py headless (COTA_NO_LOGIN=1, same trick the CI Windows
boot test uses), clicks into the CVM route, and exercises both the error
path and the success path with cvm_downloader.get_month_csv monkeypatched
to a local fixture — no real download, matching the project's "smoke tests
don't touch the network" convention (see cvm_ingest_test.py / smoke_test.py).

Run:  python tests/cvm_route_test.py   (exits non-zero on failure)
"""

import os
import sys
import tempfile

# Allow running from the repo root or the tests/ dir.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["COTA_NO_LOGIN"] = "1"

from streamlit.testing.v1 import AppTest  # noqa: E402

import cvm_downloader  # noqa: E402

_SAMPLE_CSV = """TP_FUNDO_CLASSE;CNPJ_FUNDO_CLASSE;ID_SUBCLASSE;DT_COMPTC;VL_TOTAL;VL_QUOTA;VL_PATRIM_LIQ;CAPTC_DIA;RESG_DIA;NR_COTST
CLASSES - FIF;00.017.024/0001-53;;2026-06-01;1127873.60;43.453590600000;1191031.59;0.00;0.00;1
CLASSES - FIF;00.017.024/0001-53;;2026-06-02;1128476.82;43.473615200000;1191580.45;0.00;0.00;1
"""


def _make_fixture_csv() -> str:
    fd, path = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(_SAMPLE_CSV)
    return path


def _new_app() -> AppTest:
    at = AppTest.from_file(os.path.join(ROOT, "streamlit_app.py"), default_timeout=30)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _goto_cvm(at: AppTest) -> AppTest:
    [b for b in at.button if b.key == "nav_cvm"][0].click().run()
    assert not at.exception, [str(e) for e in at.exception]
    assert at.session_state["route"] == "cvm"
    return at


def test_cvm_route_renders_and_disables_fetch_when_empty():
    at = _goto_cvm(_new_app())
    fetch_btn = [b for b in at.button if b.key == "cvm_fetch_btn"][0]
    assert fetch_btn.disabled, "fetch must be disabled until CNPJs are loaded"


def test_cvm_fetch_surfaces_errors_without_crashing():
    at = _goto_cvm(_new_app())
    at.session_state["cvm_cnpjs"] = ["00.017.024/0001-53"]
    at.session_state["cvm_month_input"] = "202606"

    original = cvm_downloader.get_month_csv
    cvm_downloader.get_month_csv = lambda month=None: (_ for _ in ()).throw(
        RuntimeError("simulated network failure")
    )
    try:
        at.run()
        [b for b in at.button if b.key == "cvm_fetch_btn"][0].click().run()
        assert not at.exception, "the route must catch fetch errors, not crash"
        assert at.session_state["cvm_results"] is None
        assert at.error, "expected an st.error message on a failed fetch"
    finally:
        cvm_downloader.get_month_csv = original


def test_cvm_fetch_success_populates_results_and_history():
    at = _goto_cvm(_new_app())
    at.session_state["cvm_cnpjs"] = ["00.017.024/0001-53", "99.999.999/9999-99"]
    at.session_state["cvm_uploaded_filename"] = "test.xlsx"
    at.session_state["cvm_month_input"] = "202606"

    fixture_path = _make_fixture_csv()
    saved_path = None
    original = cvm_downloader.get_month_csv
    cvm_downloader.get_month_csv = lambda month=None: fixture_path
    try:
        at.run()
        [b for b in at.button if b.key == "cvm_fetch_btn"][0].click().run()
        assert not at.exception, [str(e) for e in at.exception]

        df = at.session_state["cvm_results"]
        assert df is not None and len(df) == 2, "expected the 2-row fixture to load"
        assert at.session_state["cvm_missing"] == ["99.999.999/9999-99"]
        assert at.dataframe, "expected the results table to render"

        fname = at.session_state["cvm_results_filename"]
        saved_path = os.path.join(ROOT, "results", fname)
        assert os.path.exists(saved_path), f"expected {fname} persisted under results/"

        # History route should now badge this run as CVM.
        hist = _new_app()
        [b for b in hist.button if b.key == "nav_history"][0].click().run()
        assert not hist.exception, [str(e) for e in hist.exception]
        md_text = " ".join(m.value for m in hist.markdown)
        assert "CVM" in md_text, "expected a CVM tag on the History page"
    finally:
        cvm_downloader.get_month_csv = original
        os.remove(fixture_path)
        # This route persists to the real results/ dir (no DI seam for it) —
        # clean up the test artifact so repeated local runs don't accumulate.
        if saved_path and os.path.exists(saved_path):
            os.remove(saved_path)


def main():
    test_cvm_route_renders_and_disables_fetch_when_empty()
    test_cvm_fetch_surfaces_errors_without_crashing()
    test_cvm_fetch_success_populates_results_and_history()
    print("cvm route smoke tests OK")


if __name__ == "__main__":
    main()
