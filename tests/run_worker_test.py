"""run_worker smoke test (no network, no browser — fake scrapers).

Covers the guarantees that fix the 2026-09-24 "45 successes out of 38"
incident:
  - counts derive from a per-CNPJ dict (a CNPJ is never counted twice)
  - the loop skips CNPJs already recorded (safe to re-enter)
  - Stop leaves a *_partial.xlsx and marks the run interrupted
  - driver init failure ends the run with `error` set and no Excel
  - FIDC kind: success needs rows, desired-subclass filter applies

Run:  python tests/run_worker_test.py   (exits non-zero on failure)
"""

import logging
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import run_worker  # noqa: E402

_LOG = logging.getLogger("run_worker_test")
_LOG.addHandler(logging.NullHandler())


class FakeScraper:
    driver_mode = "undetected-chromedriver (fake)"
    _driver_permanently_dead = False

    def __init__(self, fail=(), init_ok=True):
        self.fail = set(fail)
        self.init_ok = init_ok
        self.calls = []
        self.closed = False

    def setup_driver(self):
        return self.init_ok

    def close(self):
        self.closed = True

    def scrape_fund_data(self, cnpj):
        self.calls.append(cnpj)
        if cnpj in self.fail:
            return {"CNPJ": cnpj, "Nome do Fundo": "N/A", "periodic_data": [], "Status": "No results"}
        return {
            "CNPJ": cnpj,
            "Nome do Fundo": f"FUNDO {cnpj[-2:]}",
            "periodic_data": [
                {"Data da cotização": "01/09/2026", "Valor cota": "R$ 1,10"},
                {"Data da cotização": "02/09/2026", "Valor cota": "R$ 1,20"},
            ],
            "Status": "Success",
        }

    def scrape_fidc_data(self, cnpj):
        self.calls.append(cnpj)
        row = {
            "Data competência": "01/09/2026",
            "Valor patrimônio líquido": "R$ 100,00",
            "Valor cota": "R$ 1,00",
            "Valor volume total de aplicação": "R$ 0,00",
            "Valor volume total de resgates": "R$ 0,00",
            "Número total de cotistas": "10",
        }
        return {
            "CNPJ": cnpj,
            "Status": "Success",
            "subclasses": [
                {"subclasse_name": "SENIOR", "subclasse_code": "S1", "periodic_data": [row]},
                {"subclasse_name": "MEZANINO", "subclasse_code": "M1", "periodic_data": [dict(row)]},
            ],
        }


CNPJS = ["11.111.111/0001-11", "22.222.222/0001-22", "33.333.333/0001-33"]


def _run(kind, scraper, **kw):
    run = run_worker.RunState(
        kind, CNPJS, {"stealth": True, "headless": False}, _LOG,
        scraper_factory=lambda r: scraper, **kw,
    )
    run_worker._worker(run)  # synchronous — same code the thread runs
    return run


def test_counts_and_excel(tmp):
    sc = FakeScraper(fail={CNPJS[1]})
    run = _run("scrape", sc)
    assert run.done and not run.interrupted and sc.closed
    assert sc.calls == CNPJS
    assert (run.success_count, run.failed_count) == (2, 1), (run.success_count, run.failed_count)
    assert len(run.events) == 3
    assert run.excel_path.name == f"anbima_results_{run.run_ts}.xlsx"
    assert run.excel_path.exists()
    assert not (tmp / f"anbima_results_{run.run_ts}_partial.xlsx").exists(), "partial must be promoted"
    assert run.output_df is not None and len(run.output_df) > 0


def test_reentry_skips_done_cnpjs(tmp):
    sc = FakeScraper()
    run = run_worker.RunState("scrape", CNPJS, {"stealth": True}, _LOG, scraper_factory=lambda r: sc)
    # Simulate a CNPJ already recorded by an earlier pass of the same run.
    run.record(CNPJS[0], sc.scrape_fund_data(CNPJS[0]), {"cnpj": CNPJS[0], "status": "success", "points": 2, "ms": 1}, "ok")
    sc.calls.clear()
    run_worker._worker(run)
    assert sc.calls == CNPJS[1:], sc.calls
    assert len(run.results) == 3 and run.success_count == 3, "no double counting"


def test_stop_leaves_partial(tmp):
    sc = FakeScraper()
    run = run_worker.RunState("scrape", CNPJS, {"stealth": True}, _LOG, scraper_factory=lambda r: sc)
    run.request_stop()
    run_worker._worker(run)
    assert run.done and run.interrupted and len(run.results) == 0
    assert run.output_df is None  # nothing scraped → nothing to promote


def test_driver_init_failure(tmp):
    sc = FakeScraper(init_ok=False)
    sc.last_init_error = "boom"
    run = _run("scrape", sc)
    assert run.done and run.error == "boom" and run.output_df is None
    assert not any(tmp.iterdir()), "no Excel on init failure"


def test_fidc_filter_and_success(tmp):
    sc = FakeScraper()
    run = _run("fidc", sc, desired={"11.111.111/0001-11": "SENIOR"})
    assert run.success_count == 3 and run.failed_count == 0
    first = run.results[CNPJS[0]]
    assert [s["subclasse_name"] for s in first["subclasses"]] == ["SENIOR"], "desired filter"
    assert len(run.results[CNPJS[1]]["subclasses"]) == 2
    assert run.excel_path.name.startswith("fidc_results_") and run.excel_path.exists()
    assert run.events[0]["name"] == "1 subclasse" and run.events[1]["name"] == "2 subclasses"


def main():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        run_worker.RESULTS_DIR = tmp
        for t in (test_counts_and_excel, test_reentry_skips_done_cnpjs, test_stop_leaves_partial,
                  test_driver_init_failure, test_fidc_filter_and_success):
            for f in tmp.iterdir():
                f.unlink()
            t(tmp)
    print("run_worker smoke tests OK")


if __name__ == "__main__":
    main()
