"""
Background scrape runner — the loop lives here, not in the Streamlit script.

Why: the per-CNPJ loop used to run inside streamlit_app.py's own script run.
Any rerun mid-run (browser websocket reconnect — Chrome throttles background
tabs to one wake-up per minute —, a nav click, Streamlit's own Stop/Rerun)
made Streamlit drop the running script and start a fresh one, which restarted
the loop at CNPJ 1 with a new Chrome while the old one was still mid-CNPJ.
Eduardo's 2026-09-24 log shows six overlapping starts a minute apart:
38 CNPJs, 45 successes counted, "118.4%" success rate, stray Chromes.

Here the loop runs in a daemon thread that never touches Streamlit. It only
writes into a RunState; the script reads a snapshot once a second and
renders. Reruns just re-render. Counts are derived from a per-CNPJ dict, so a
CNPJ can never be counted twice, and the loop skips CNPJs already done.
"""

from __future__ import annotations

import logging
import re
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

from data_processor import DataProcessor
from stealth_scraper import StealthANBIMAScraper, subclass_matches

RESULTS_DIR = Path("results")


class RunState:
    """Everything one run needs and produces. Written by the worker thread,
    read (via snapshot()) by the Streamlit script."""

    def __init__(
        self,
        kind: str,
        cnpjs,
        settings: dict,
        logger: logging.Logger,
        start_time: Optional[float] = None,
        desired: Optional[dict] = None,
        scraper_factory: Optional[Callable[["RunState"], object]] = None,
    ):
        assert kind in ("scrape", "fidc"), kind
        self.kind = kind
        self.cnpjs: List[str] = [str(c) for c in cnpjs]
        self.settings = dict(settings)
        self.logger = logger
        self.desired = dict(desired or {})
        self.scraper_factory = scraper_factory  # tests inject a fake scraper
        self.start_time = start_time or time.time()
        self.run_ts = datetime.fromtimestamp(self.start_time).strftime("%Y%m%d_%H%M%S")
        self.prefix = "anbima_results" if kind == "scrape" else "fidc_results"

        self.lock = threading.Lock()
        self.results: Dict[str, dict] = {}  # cnpj -> scraper result, in run order
        self.events: List[dict] = []  # activity feed rows
        self.status_messages: List[str] = []
        self.notes: List[tuple] = []  # (st level, text) banners
        self.current: Optional[str] = None  # CNPJ in flight
        self.stop = False
        self.interrupted = False
        self.done = False
        self.finalized = False  # set by the script once copied into session
        self.error: Optional[str] = None
        self.error_tb: Optional[str] = None
        self.driver_mode: Optional[str] = None
        self.output_df = None
        self.excel_path: Optional[Path] = None
        self.end_time: Optional[float] = None
        self.thread: Optional[threading.Thread] = None

    # Counts are DERIVED from the per-CNPJ dict — never incremented.
    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results.values() if _is_success(self.kind, r))

    @property
    def failed_count(self) -> int:
        return len(self.results) - self.success_count

    def request_stop(self) -> None:
        self.stop = True
        self.logger.info("Stop requested by user")

    def note(self, level: str, text: str) -> None:
        with self.lock:
            self.notes.append((level, text))

    def record(self, cnpj: str, result: dict, event: dict, message: str) -> None:
        with self.lock:
            self.results[cnpj] = result
            self.events.append(event)
            self.status_messages.append(message)

    def snapshot(self) -> dict:
        with self.lock:
            success = self.success_count
            return {
                "events": list(self.events),
                "notes": list(self.notes),
                "success": success,
                "failed": len(self.results) - success,
                "total": len(self.cnpjs),
                "current": self.current,
                "stop": self.stop,
                "done": self.done,
                "start_time": self.start_time,
                "elapsed": (self.end_time or time.time()) - self.start_time,
            }


def _is_success(kind: str, result: dict) -> bool:
    if result.get("Status") != "Success":
        return False
    if kind == "fidc":
        subs = result.get("subclasses") or []
        return sum(len(s.get("periodic_data") or []) for s in subs) > 0
    return True


def _make_scraper(run: RunState):
    if run.scraper_factory is not None:
        return run.scraper_factory(run)
    headless = bool(run.settings.get("headless", False))
    if run.settings.get("stealth", True):
        return StealthANBIMAScraper(
            headless=headless, proxy=run.settings.get("proxy") or None
        )
    from anbima_scraper import ANBIMAScraper

    return ANBIMAScraper(headless=headless)


def _tag(run: RunState, idx: int, total: int) -> str:
    return f"[{idx}/{total}]" if run.kind == "scrape" else f"[FIDC {idx}/{total}]"


def _apply_desired_filter(run: RunState, tag: str, cnpj: str, result: dict) -> None:
    """Optional per-CNPJ subclass filter (FIDC): keep only the subclass the
    user asked for. If the label matches nothing, keep all and say so."""
    desired = run.desired.get(re.sub(r"\s+", "", str(cnpj)))
    if not desired or not result.get("subclasses"):
        return
    kept = [s for s in result["subclasses"] if subclass_matches(desired, s)]
    if kept:
        result["subclasses"] = kept
        run.logger.info(f"{tag} filtered to '{desired}': {len(kept)} subclass(es)")
    else:
        run.logger.warning(
            f"{tag} desired '{desired}' matched no subclass — keeping all "
            f"{len(result['subclasses'])}"
        )


def _scrape_one(scraper, run: RunState, idx: int, total: int, cnpj: str):
    """Scrape one CNPJ. Returns (result, activity event, status message)."""
    log = run.logger
    tag = _tag(run, idx, total)
    t0 = time.time()
    try:
        if run.kind == "scrape":
            result = scraper.scrape_fund_data(cnpj)
        else:
            result = scraper.scrape_fidc_data(cnpj)
            _apply_desired_filter(run, tag, cnpj, result)
        secs = time.time() - t0
        ms = int(secs * 1000)

        if _is_success(run.kind, result):
            if run.kind == "scrape":
                pts = len(result.get("periodic_data") or [])
                name = str(result.get("Nome do Fundo") or "—")
                log.info(f"{tag} SUCCESS: {cnpj} - {pts} data points - {secs:.1f}s")
                msg = f"✅ {cnpj} - Success ({pts} data points)"
            else:
                subs = result.get("subclasses") or []
                pts = sum(len(s.get("periodic_data") or []) for s in subs)
                name = f"{len(subs)} subclasse{'s' if len(subs) != 1 else ''}"
                log.info(
                    f"{tag} SUCCESS: {cnpj} - {len(subs)} subclasses, {pts} rows"
                )
                msg = f"✅ {cnpj} - Success ({pts} rows)"
            event = {
                "cnpj": cnpj,
                "name": name,
                "status": "success",
                "points": pts,
                "ms": ms,
            }
            return result, event, msg

        status = str(result.get("Status", "Failed"))
        name = (
            str(result.get("Nome do Fundo") or "—") if run.kind == "scrape" else status
        )
        log.warning(f"{tag} FAILED: {cnpj} - Status: {status} - {secs:.1f}s")
        event = {"cnpj": cnpj, "name": name, "status": "failed", "points": 0, "ms": ms}
        return result, event, f"❌ {cnpj} - {status}"

    except Exception as e:
        secs = time.time() - t0
        err = str(e)[:50]
        log.error(f"{tag} EXCEPTION: {cnpj} - {e} - {secs:.1f}s")
        log.debug(f"Traceback:\n{traceback.format_exc()}")
        if run.kind == "scrape":
            result = {
                "CNPJ": cnpj,
                "Nome do Fundo": "N/A",
                "periodic_data": [],
                "Status": f"Error: {err}",
            }
        else:
            result = {"CNPJ": cnpj, "Status": f"Error: {err}", "subclasses": []}
        event = {
            "cnpj": cnpj,
            "name": f"Error: {err}",
            "status": "failed",
            "points": 0,
            "ms": int(secs * 1000),
        }
        return result, event, f"❌ {cnpj} - Error: {err}"


def _process(run: RunState):
    proc = DataProcessor()
    results = list(run.results.values())
    if run.kind == "scrape":
        return proc.process_scraped_data(results)
    return proc.process_fidc_data(results)


def _persist(run: RunState, partial: bool):
    """Write the Excel for everything collected so far. Returns (df, path)."""
    df = _process(run)
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / f"{run.prefix}_{run.run_ts}{'_partial' if partial else ''}.xlsx"
    DataProcessor.write_excel(df, path)
    return df, path


def _worker(run: RunState) -> None:
    log = run.logger
    scraper = None
    total = len(run.cnpjs)
    partial_path = RESULTS_DIR / f"{run.prefix}_{run.run_ts}_partial.xlsx"
    try:
        scraper = _make_scraper(run)
        if run.kind == "fidc" and not hasattr(scraper, "scrape_fidc_data"):
            run.error = (
                "The selected scraper has no FIDC support. Turn Stealth mode ON "
                "(the FIDC workflow requires the stealth scraper)."
            )
            log.error(f"[FIDC] {run.error}")
            return

        if not scraper.setup_driver():
            run.error = getattr(scraper, "last_init_error", None) or "Unknown error"
            run.error_tb = getattr(scraper, "last_init_traceback", None)
            log.error(f"setup_driver failed: {run.error}")
            if run.error_tb:
                log.debug(run.error_tb)
            return

        run.driver_mode = getattr(scraper, "driver_mode", None)
        log.info(f"WebDriver initialized successfully via: {run.driver_mode}")
        if run.driver_mode and "plain Selenium" in run.driver_mode:
            run.note(
                "info",
                f"ℹ️ WebDriver: **{run.driver_mode}** (UC unavailable — stealth level reduced)",
            )
        elif run.driver_mode:
            run.note("success", f"✅ WebDriver: **{run.driver_mode}**")

        for idx, cnpj in enumerate(run.cnpjs, 1):
            if cnpj in run.results:  # already done (idempotent by construction)
                continue
            if run.stop:
                log.info(f"Scraping stopped by user at CNPJ {idx}/{total}")
                run.note(
                    "warning", f"⚠️ Scraping stopped by user after {idx - 1}/{total} CNPJs"
                )
                run.interrupted = True
                break

            run.current = cnpj
            log.info(f"{_tag(run, idx, total)} Starting CNPJ: {cnpj}")
            result, event, msg = _scrape_one(scraper, run, idx, total, cnpj)
            run.record(cnpj, result, event, msg)
            run.current = None

            # Incremental save — survives a killed process.
            try:
                _persist(run, partial=True)
                run.excel_path = partial_path
            except Exception as e:
                log.warning(f"Incremental save failed: {e}")

            # Circuit breaker: Chrome won't stay alive. Stop now instead of
            # iterating the rest of the list as instant failures.
            if getattr(scraper, "_driver_permanently_dead", False):
                run.note(
                    "error",
                    "🛑 Chrome kept dying and could not be recovered — stopping the run. "
                    "Turn the **Headless browser** toggle OFF (Review screen) and retry. "
                    f"Partial results up to {idx}/{total} are saved (see History).",
                )
                log.error(f"Aborting run at {idx}/{total} — driver permanently dead")
                run.interrupted = True
                break

    except Exception as e:
        run.note("error", f"❌ Error during scraping: {e}")
        log.error(f"Error during scraping: {e}")
        log.debug(f"Full traceback:\n{traceback.format_exc()}")
        run.interrupted = True

    finally:
        if scraper is not None:
            try:
                scraper.close()
                log.info("WebDriver closed successfully")
            except Exception as e:
                run.note("warning", f"⚠️ Warning: Could not close scraper properly - {e}")
                log.warning(f"Could not close scraper properly - {e}")

        if run.results:
            try:
                log.info(f"Processing {len(run.results)} results...")
                interrupted = run.interrupted or run.stop
                df, path = _persist(run, partial=interrupted)
                run.output_df = df
                run.excel_path = path
                log.info(f"Results processed successfully - {len(df)} rows")
                # Clean completion: promote to the final name, drop the partial.
                if not interrupted and partial_path.exists() and partial_path != path:
                    try:
                        partial_path.unlink()
                    except Exception:
                        pass
                log.info(f"Excel saved to {path}")
            except Exception as e:
                run.note("warning", f"⚠️ Warning: Could not process all results - {e}")
                log.error(f"Error processing results: {e}")
                log.debug(traceback.format_exc())

        run.end_time = time.time()
        total_time = run.end_time - run.start_time
        log.info("=" * 80)
        log.info("SCRAPING ENDED" if run.kind == "scrape" else "FIDC SCRAPING ENDED")
        log.info(f"Total CNPJs requested: {total}")
        log.info(f"CNPJs processed: {len(run.results)}")
        log.info(f"Successful: {run.success_count}")
        log.info(f"Failed: {run.failed_count}")
        log.info(f"Total Time: {total_time / 60:.2f} minutes")
        if run.results:
            log.info(f"Avg Time per CNPJ: {total_time / len(run.results):.1f} seconds")
        log.info("=" * 80)
        run.done = True


def start(run: RunState) -> RunState:
    """Start the worker thread for `run` (once). Returns `run` for chaining."""
    if run.thread is None:
        t = threading.Thread(
            target=_worker,
            args=(run,),
            name=f"cota-{run.kind}-{run.run_ts}",
            daemon=True,
        )
        run.thread = t
        t.start()
    return run
