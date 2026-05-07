"""
Cota theme module
=================

Cota is the brand we use in the UI for this app — a modern fintech-style
re-skin on top of Streamlit. This module owns:

* the global CSS string (`COTA_CSS`),
* a helper to inject it (`inject_css`),
* small HTML helpers (brand mark, topbar, stepper, KPI tile, etc.)
  that the main app composes via `st.markdown(..., unsafe_allow_html=True)`.

Streamlit can't render the React prototype verbatim — see WINDOWS_SETUP /
the design handoff README — so this module restyles native widgets to
match the Cota design tokens (warm-neutral surface, emerald accent,
Geist Sans/Mono) and provides drop-in HTML for a few elements that are
not first-class in Streamlit (topbar, stepper, KPI tiles, status pill).

Usage
-----
    import cota_theme
    cota_theme.inject_css()                 # call once near the top of the app
    st.markdown(cota_theme.brand_mark(), unsafe_allow_html=True)

Design tokens
-------------
sRGB approximations of the design's oklch() palette. We can't put oklch()
in `config.toml`, but we *can* use it in raw CSS — the CSS variables below
use oklch() so the result matches the prototype exactly.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Global CSS — ported from the design's styles.css, with Streamlit-specific
# overrides bolted on so native widgets pick up the Cota look.
# ---------------------------------------------------------------------------

COTA_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>
:root {
  /* warm-neutral palette */
  --bg:        oklch(0.985 0.005 90);
  --bg-elev:   oklch(1 0 0);
  --bg-sunk:   oklch(0.965 0.006 90);
  --line:      oklch(0.92 0.005 90);
  --line-soft: oklch(0.95 0.005 90);

  --fg:        oklch(0.22 0.01 60);
  --fg-2:      oklch(0.42 0.01 60);
  --fg-3:      oklch(0.58 0.008 60);
  --fg-mute:   oklch(0.7 0.005 60);

  /* emerald accent */
  --accent:        oklch(0.62 0.15 155);
  --accent-strong: oklch(0.55 0.16 155);
  --accent-soft:   oklch(0.95 0.04 155);
  --accent-tint:   oklch(0.97 0.025 155);

  --ok:        oklch(0.62 0.15 155);
  --warn:      oklch(0.75 0.13 75);
  --warn-soft: oklch(0.96 0.04 75);
  --err:       oklch(0.6 0.18 25);
  --err-soft:  oklch(0.96 0.03 25);

  --shadow-1: 0 1px 2px oklch(0.2 0.01 60 / 0.04), 0 1px 1px oklch(0.2 0.01 60 / 0.03);
  --shadow-2: 0 4px 12px oklch(0.2 0.01 60 / 0.06), 0 2px 4px oklch(0.2 0.01 60 / 0.04);
  --shadow-pop: 0 30px 60px -20px oklch(0.2 0.01 60 / 0.18), 0 10px 24px -12px oklch(0.2 0.01 60 / 0.1);

  --r-sm: 6px;
  --r-md: 10px;
  --r-lg: 14px;
  --r-xl: 18px;
}

/* ─────────────────────────────────────────────────────
   Streamlit base overrides — make the host page look like Cota.
   Streamlit wraps its app in a few generated containers, so we
   target both the documented data-testid attributes and the
   class shapes that have been stable across recent versions.
   ───────────────────────────────────────────────────── */

html, body, [data-testid="stAppViewContainer"], .stApp {
  background: var(--bg) !important;
  font-family: "Geist", ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif !important;
  color: var(--fg) !important;
  font-size: 14px !important;
  line-height: 1.45 !important;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

/* Hide Streamlit's default chrome — we render our own topbar/footer */
#MainMenu, header[data-testid="stHeader"], footer { visibility: hidden; height: 0 !important; }
.stDeployButton { display: none !important; }

/* Tighten the default block padding so the app feels like the Cota mock */
[data-testid="stAppViewBlockContainer"], .block-container {
  max-width: 1280px !important;
  padding-top: 0 !important;
  padding-bottom: 64px !important;
}

/* Mono utility — used inline for CNPJs, IDs, numbers */
.cota-mono, code, kbd, samp { font-family: "Geist Mono", ui-monospace, "SF Mono", Menlo, monospace !important; }
.cota-muted { color: var(--fg-mute); }

/* ─────────────────────────────────────────────────────
   Buttons — the Streamlit button gets a Cota look.
   Streamlit emits `<button data-testid="stBaseButton-secondary">` for
   regular buttons and `-primary` for `type="primary"`.
   ───────────────────────────────────────────────────── */
.stButton > button,
[data-testid^="stBaseButton-"] {
  font-family: inherit !important;
  font-weight: 500 !important;
  font-size: 13px !important;
  border-radius: var(--r-md) !important;
  height: 36px !important;
  padding: 0 14px !important;
  border: 1px solid var(--line) !important;
  background: var(--bg-elev) !important;
  color: var(--fg) !important;
  box-shadow: none !important;
  transition: background .15s, border-color .15s, color .15s, transform .05s !important;
}
.stButton > button:hover,
[data-testid^="stBaseButton-"]:hover {
  background: var(--bg-sunk) !important;
  border-color: var(--line) !important;
  color: var(--fg) !important;
}
.stButton > button:active,
[data-testid^="stBaseButton-"]:active { transform: translateY(1px); }

/* Primary button = dark fg pill (Cota convention, not emerald — emerald is data colour). */
[data-testid="stBaseButton-primary"] {
  background: var(--fg) !important;
  color: var(--bg-elev) !important;
  border-color: var(--fg) !important;
}
[data-testid="stBaseButton-primary"]:hover {
  background: oklch(0.16 0.01 60) !important;
  border-color: oklch(0.16 0.01 60) !important;
}

/* Inputs — text + password */
.stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input {
  background: var(--bg-elev) !important;
  border: 1px solid var(--line) !important;
  border-radius: var(--r-md) !important;
  color: var(--fg) !important;
  font-size: 13.5px !important;
  padding: 10px 12px !important;
  box-shadow: none !important;
}
.stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px oklch(0.62 0.15 155 / 0.15) !important;
  outline: none !important;
}
.stTextInput label, .stTextArea label, .stNumberInput label,
.stCheckbox label, .stRadio label, .stSelectbox label, .stFileUploader label {
  font-size: 12px !important; font-weight: 500 !important;
  color: var(--fg-2) !important;
}

/* Checkbox / toggle — paint the accent emerald when checked */
.stCheckbox [data-testid="stCheckbox"] svg { color: var(--accent) !important; }

/* Progress bar — emerald fill */
.stProgress > div > div > div > div { background: var(--accent) !important; }

/* Alerts — quieter, Cota-style */
[data-testid="stAlert"] {
  border-radius: var(--r-md) !important;
  border: 1px solid var(--line) !important;
  box-shadow: var(--shadow-1) !important;
}
[data-testid="stAlertContentSuccess"] { background: var(--accent-tint) !important; color: var(--accent-strong) !important; }
[data-testid="stAlertContentError"]   { background: var(--err-soft)   !important; color: var(--err) !important; }
[data-testid="stAlertContentWarning"] { background: var(--warn-soft)  !important; color: oklch(0.5 0.13 75) !important; }
[data-testid="stAlertContentInfo"]    { background: var(--bg-sunk)    !important; color: var(--fg-2) !important; }

/* Code blocks / dataframes — match Cota palette */
[data-testid="stCodeBlock"], pre { background: var(--bg-sunk) !important; border-radius: var(--r-md) !important; border: 1px solid var(--line) !important; }
[data-testid="stTable"], [data-testid="stDataFrame"] { border: 1px solid var(--line) !important; border-radius: var(--r-md) !important; overflow: hidden; }

/* File uploader — restyle to Cota dropzone */
[data-testid="stFileUploaderDropzone"] {
  border: 1.5px dashed var(--line) !important;
  background: var(--bg-sunk) !important;
  border-radius: var(--r-lg) !important;
  padding: 32px 24px !important;
  transition: all .15s !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
  border-color: var(--fg-mute) !important;
  background: oklch(0.97 0.005 90) !important;
}
[data-testid="stFileUploaderDropzone"] button {
  background: var(--bg-elev) !important;
  border: 1px solid var(--line) !important;
}
section[data-testid="stFileUploaderDropzoneInstructions"] small { color: var(--fg-mute) !important; }

/* Sidebar — fully removed; Cota uses a topbar. Hide the collapsed-state
   handle as well so there's nothing dangling at the left edge. */
section[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
button[aria-label="Open sidebar"],
button[aria-label="Close sidebar"] { display: none !important; }

/* ─────────────────────────────────────────────────────
   Cota custom components — pure HTML emitted by helpers below.
   ───────────────────────────────────────────────────── */

/* brand mark */
.cota-mark {
  display: inline-grid; place-items: center; position: relative;
  width: 36px; height: 36px;
  background: var(--fg); border-radius: 9px; overflow: hidden;
}
.cota-mark.sm { width: 26px; height: 26px; border-radius: 7px; }
.cota-mark .dot {
  width: 7px; height: 7px; border-radius: 99px;
  background: var(--accent);
  box-shadow: 0 0 8px var(--accent);
  position: relative; z-index: 1;
}
.cota-mark.sm .dot { width: 5px; height: 5px; }
.cota-mark .bar {
  position: absolute; inset: 0;
  background: linear-gradient(75deg, transparent 40%, oklch(1 0 0 / 0.12) 50%, transparent 60%);
}
.cota-brand-row { display: flex; align-items: center; gap: 12px; }
.cota-brand-name { font-weight: 600; font-size: 18px; letter-spacing: -0.01em; color: var(--fg); }
.cota-brand-name.sm { font-size: 15px; }
.cota-brand-tagline { font-size: 12px; color: var(--fg-mute); }

/* topbar */
.cota-topbar {
  position: sticky; top: 0; z-index: 100;
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 28px;
  margin: 0 -28px 24px -28px;        /* burst out of the block-container's padding */
  background: oklch(1 0 0 / 0.85);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--line);
}
.cota-topbar-left, .cota-topbar-right { display: flex; align-items: center; gap: 12px; }
.cota-topbar-divider { width: 1px; height: 20px; background: var(--line); margin: 0 6px; }
.cota-topbar-nav { display: flex; gap: 2px; }
.cota-status-pill {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 10px;
  border: 1px solid var(--line);
  border-radius: 99px;
  font-size: 12px; color: var(--fg-2);
  background: var(--bg-elev);
}
.cota-status-dot { width: 6px; height: 6px; border-radius: 99px; background: var(--ok); box-shadow: 0 0 0 3px oklch(0.62 0.15 155 / 0.15); }
.cota-usermenu {
  display: inline-flex; align-items: center; gap: 10px;
  padding: 4px 6px 4px 4px;
  border: 1px solid var(--line);
  border-radius: 99px;
  background: var(--bg-elev);
}
.cota-avatar {
  width: 28px; height: 28px; border-radius: 99px;
  background: var(--fg); color: var(--bg-elev);
  display: grid; place-items: center;
  font-size: 12px; font-weight: 600;
}
.cota-usermenu-text { display: flex; flex-direction: column; line-height: 1.15; padding-right: 4px; }
.cota-usermenu-name { font-size: 12.5px; font-weight: 500; color: var(--fg); }
.cota-usermenu-role { font-size: 11px; color: var(--fg-mute); }

/* page header */
.cota-page-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 32px; flex-wrap: wrap; margin: 12px 0 24px;
}
.cota-page-title { margin: 0 0 4px; font-size: 28px; font-weight: 600; letter-spacing: -0.02em; }
.cota-page-sub { margin: 0; color: var(--fg-2); font-size: 14px; max-width: 56ch; }

/* footer */
.cota-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 28px; margin: 32px -28px -64px -28px;
  border-top: 1px solid var(--line);
  font-size: 12px; color: var(--fg-2);
  background: var(--bg);
}

/* login */
.cota-login-shell {
  position: relative; min-height: calc(100vh - 80px);
  display: grid; place-items: center;
  padding: 32px 0; overflow: hidden;
}
.cota-login-bg { position: absolute; inset: 0; pointer-events: none; }
.cota-login-bg-grid {
  position: absolute; inset: -2px;
  background-image:
    linear-gradient(to right, oklch(0.9 0.005 90 / 0.5) 1px, transparent 1px),
    linear-gradient(to bottom, oklch(0.9 0.005 90 / 0.5) 1px, transparent 1px);
  background-size: 56px 56px;
  mask-image: radial-gradient(ellipse 70% 60% at 50% 40%, black 30%, transparent 80%);
}
.cota-login-bg-glow {
  position: absolute; left: 50%; top: 35%;
  width: 720px; height: 480px; transform: translate(-50%, -50%);
  background: radial-gradient(closest-side, oklch(0.92 0.07 155 / 0.6), transparent 70%);
  filter: blur(20px);
}
.cota-login-card {
  position: relative; z-index: 1;
  width: min(440px, 100%);
  background: var(--bg-elev);
  border: 1px solid var(--line);
  border-radius: var(--r-xl);
  padding: 32px;
  box-shadow: var(--shadow-pop);
}
.cota-login-title {
  font-size: 26px; font-weight: 600; letter-spacing: -0.02em;
  margin: 24px 0 6px;
}
.cota-login-sub { color: var(--fg-2); margin: 0 0 20px; font-size: 13px; }
.cota-login-foot { margin-top: 24px; padding-top: 20px; border-top: 1px solid var(--line-soft); }
.cota-login-foot-row { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--fg-2); }
.cota-login-foot-row.muted { color: var(--fg-mute); margin-top: 6px; }

/* badge / tag */
.cota-badge {
  display: inline-flex; align-items: center;
  padding: 3px 9px;
  font-size: 11px; font-weight: 500;
  background: var(--bg-sunk); color: var(--fg-2);
  border: 1px solid var(--line);
  border-radius: 99px;
}
.cota-tag {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 8px;
  font-size: 11px; font-weight: 500;
  border-radius: 99px;
  border: 1px solid transparent;
}
.cota-tag-ready { background: var(--bg-sunk); color: var(--fg-2); border-color: var(--line); }
.cota-tag-ok    { background: var(--accent-tint); color: var(--accent-strong); border-color: var(--accent-soft); }
.cota-tag-err   { background: var(--err-soft); color: var(--err); border-color: oklch(0.85 0.12 25 / 0.4); }
.cota-tag-warn  { background: var(--warn-soft); color: oklch(0.5 0.13 75); border-color: oklch(0.85 0.12 75 / 0.4); }

/* card surface */
.cota-card {
  background: var(--bg-elev);
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  padding: 24px;
  box-shadow: var(--shadow-1);
  margin-bottom: 20px;
}
.cota-card-title { margin: 0 0 4px; font-size: 17px; font-weight: 600; letter-spacing: -0.01em; }
.cota-card-sub   { margin: 0 0 16px; font-size: 13px; color: var(--fg-2); }

/* Style Streamlit's bordered container as a Cota card so widgets inside
   pick up the right surface without us having to wrap them in raw HTML. */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--bg-elev) !important;
  border: 1px solid var(--line) !important;
  border-radius: var(--r-lg) !important;
  padding: 20px !important;
  box-shadow: var(--shadow-1) !important;
}

/* ─────────────────────────────────────────────────────
   Stepper — Upload → Review → Scrape → Download
   ───────────────────────────────────────────────────── */
.cota-stepper {
  list-style: none; padding: 10px 14px; margin: 0;
  display: inline-flex; align-items: stretch; gap: 0;
  background: var(--bg-elev);
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-1);
}
.cota-step {
  position: relative;
  display: flex; align-items: center; gap: 10px;
  padding: 4px 18px 4px 4px;
}
.cota-step + .cota-step { padding-left: 18px; }
.cota-step-bullet {
  width: 24px; height: 24px; border-radius: 99px;
  border: 1px solid var(--line);
  background: var(--bg-sunk);
  color: var(--fg-mute);
  display: grid; place-items: center;
  font-size: 11px; font-weight: 600;
  flex: none; transition: all .2s;
}
.cota-step.active .cota-step-bullet {
  background: var(--fg); color: var(--bg-elev); border-color: var(--fg);
  box-shadow: 0 0 0 4px oklch(0.62 0.15 155 / 0.18);
}
.cota-step.done .cota-step-bullet {
  background: var(--accent); color: var(--bg-elev); border-color: var(--accent);
}
.cota-step-text { display: flex; flex-direction: column; line-height: 1.2; }
.cota-step-label { font-size: 12.5px; font-weight: 500; color: var(--fg); }
.cota-step.pending .cota-step-label { color: var(--fg-mute); }
.cota-step-help { font-size: 11px; color: var(--fg-mute); }
.cota-step-line {
  height: 1px; flex: 0 0 24px;
  background: var(--line); align-self: center; margin-left: 4px;
}
.cota-step.done + .cota-step .cota-step-line,
.cota-step.done .cota-step-line { background: var(--accent); }

/* ─────────────────────────────────────────────────────
   CNPJ table (review phase)
   ───────────────────────────────────────────────────── */
.cota-searchrow { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.cota-searchrow-meta { font-size: 12px; color: var(--fg-mute); white-space: nowrap; }

.cota-cnpj-table {
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  overflow: hidden;
  background: var(--bg-elev);
}
.cota-cnpj-row {
  display: grid;
  grid-template-columns: 36px 160px 1fr 80px;
  align-items: center;
  padding: 10px 14px;
  font-size: 13px;
  border-bottom: 1px solid var(--line-soft);
}
.cota-cnpj-row:last-child { border-bottom: 0; }
.cota-cnpj-head {
  background: var(--bg-sunk);
  font-size: 11px; font-weight: 500; text-transform: uppercase;
  letter-spacing: 0.04em; color: var(--fg-mute);
}
.cota-cnpj-body { max-height: 360px; overflow-y: auto; }
.cota-col-idx { color: var(--fg-mute); font-family: "Geist Mono", monospace; font-size: 12px; }
.cota-col-cnpj { font-family: "Geist Mono", monospace; color: var(--fg); }
.cota-col-name { color: var(--fg-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cota-col-status { display: flex; justify-content: flex-end; }
.cota-empty { padding: 32px; text-align: center; color: var(--fg-mute); font-size: 13px; }

/* ─────────────────────────────────────────────────────
   Run summary box (right column of review)
   ───────────────────────────────────────────────────── */
.cota-run-summary {
  background: var(--bg-sunk);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  padding: 14px 16px;
  display: flex; flex-direction: column;
  gap: 10px;
  margin: 12px 0;
}
.cota-run-summary-row {
  display: grid; grid-template-columns: 1fr auto;
  align-items: center; gap: 10px;
  font-size: 13px; color: var(--fg-2);
}
.cota-run-summary-val { color: var(--fg); font-weight: 500; font-family: "Geist Mono", monospace; }

/* ─────────────────────────────────────────────────────
   Setting row (label + help + control). Used in the right card of Review.
   We render label/help via HTML and place the Streamlit widget below it.
   ───────────────────────────────────────────────────── */
.cota-setting-text { display: flex; flex-direction: column; gap: 2px; padding: 8px 0 4px; }
.cota-setting-label { font-size: 13.5px; font-weight: 500; color: var(--fg); }
.cota-setting-help  { font-size: 12px; color: var(--fg-mute); }

/* ─────────────────────────────────────────────────────
   Scrape progress — ring + KPIs + progress bar + activity feed
   ───────────────────────────────────────────────────── */
.cota-progress-hero {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 24px;
  align-items: center;
  margin: 4px 0 12px;
}
@media (max-width: 720px) { .cota-progress-hero { grid-template-columns: 1fr; } }

.cota-ring-wrap { display: grid; place-items: center; }
.cota-ring-bg { fill: none; stroke: var(--line); stroke-width: 8; }
.cota-ring-fg {
  fill: none; stroke: var(--accent);
  stroke-width: 8; stroke-linecap: round;
  transition: stroke-dashoffset .4s ease;
}
.cota-ring-pct {
  font: 600 26px/1 "Geist Mono", monospace;
  fill: var(--fg); letter-spacing: -0.02em;
}
.cota-ring-lab {
  font: 11px/1 "Geist", sans-serif;
  fill: var(--fg-mute); letter-spacing: 0.04em;
  text-transform: uppercase;
}

.cota-progress-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
@media (max-width: 540px) { .cota-progress-stats { grid-template-columns: repeat(2, 1fr); } }

.cota-stat {
  background: var(--bg-sunk);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  padding: 10px 12px;
  display: flex; flex-direction: column; gap: 2px;
}
.cota-stat-label {
  font-size: 11px; color: var(--fg-mute);
  text-transform: uppercase; letter-spacing: 0.04em;
}
.cota-stat-value {
  font-size: 16px; font-weight: 500; color: var(--fg);
  font-family: "Geist Mono", monospace;
}
.cota-stat.accent {
  background: var(--accent-tint);
  border-color: var(--accent-soft);
}
.cota-stat.accent .cota-stat-value { color: var(--accent-strong); }
.cota-stat.ok  .cota-stat-value { color: var(--accent-strong); }
.cota-stat.err .cota-stat-value { color: var(--err); }

.cota-progress-bar-track {
  height: 6px; border-radius: 99px;
  background: var(--line-soft);
  overflow: hidden;
  margin: 8px 0 16px;
}
.cota-progress-bar-fill {
  height: 100%; background: var(--accent);
  border-radius: 99px;
  transition: width .35s ease;
}

.cota-activity {
  background: var(--bg-sunk);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  padding: 14px 16px;
  display: flex; flex-direction: column; gap: 10px;
}
.cota-activity-head {
  display: flex; align-items: center; justify-content: space-between;
}
.cota-activity-title { font-size: 12.5px; font-weight: 500; color: var(--fg); }
.cota-activity-meta {
  font-size: 11px; color: var(--fg-mute);
  font-family: "Geist Mono", monospace;
}
.cota-activity-list { display: flex; flex-direction: column; gap: 2px; }
.cota-activity-row {
  display: grid;
  grid-template-columns: 12px 160px 1fr 120px 70px;
  align-items: center; gap: 10px;
  padding: 6px 6px;
  font-size: 12.5px;
  border-radius: var(--r-sm);
}
.cota-activity-row.success { color: var(--fg); }
.cota-activity-row.failed  { color: var(--fg); background: var(--err-soft); }
.cota-activity-row.pending { color: var(--fg-2); background: oklch(1 0 0 / 0.6); }

.cota-act-dot { width: 7px; height: 7px; border-radius: 99px; }
.cota-act-dot.success { background: var(--accent); }
.cota-act-dot.failed  { background: var(--err); }
.cota-act-dot.pending {
  background: var(--fg-mute);
  animation: cota-pulse 1.4s ease-in-out infinite;
}
@keyframes cota-pulse { 0%,100% { opacity: .4 } 50% { opacity: 1 } }

.cota-act-cnpj { font-family: "Geist Mono", monospace; font-size: 12px; }
.cota-act-name {
  color: var(--fg-2);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.cota-activity-row.failed .cota-act-name { color: var(--err); }
.cota-act-points, .cota-act-ms {
  font-size: 11.5px; color: var(--fg-2);
  font-family: "Geist Mono", monospace;
}
.cota-shimmer {
  background: linear-gradient(90deg, transparent, oklch(0.95 0.005 90), transparent);
  background-size: 200% 100%;
  animation: cota-shimmer 1.4s linear infinite;
  color: var(--fg-2);
}
@keyframes cota-shimmer {
  0%   { background-position: 200% 0 }
  100% { background-position: -200% 0 }
}

/* ─────────────────────────────────────────────────────
   Results — summary card + KPI row + result table
   ───────────────────────────────────────────────────── */
.cota-success-circle {
  width: 56px; height: 56px;
  border-radius: 99px;
  background: var(--accent-tint);
  border: 1px solid var(--accent-soft);
  color: var(--accent-strong);
  display: grid; place-items: center;
}
.cota-success-circle.warn {
  background: var(--warn-soft);
  border-color: oklch(0.85 0.12 75 / 0.4);
  color: oklch(0.5 0.13 75);
}

.cota-kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-top: 12px;
}
@media (max-width: 720px) { .cota-kpi-row { grid-template-columns: repeat(2, 1fr); } }
.cota-kpi {
  background: var(--bg-sunk);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  padding: 14px 16px;
}
.cota-kpi-label {
  font-size: 11px; color: var(--fg-mute);
  text-transform: uppercase; letter-spacing: 0.04em;
}
.cota-kpi-value {
  font-size: 22px; font-weight: 600; color: var(--fg);
  margin-top: 4px; letter-spacing: -0.01em;
  font-family: "Geist Mono", monospace;
}
.cota-kpi.err .cota-kpi-value { color: var(--err); }
.cota-kpi.ok  .cota-kpi-value { color: var(--accent-strong); }

.cota-result-table {
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  overflow: hidden;
  background: var(--bg-elev);
}
.cota-result-row {
  display: grid;
  grid-template-columns: 160px 1fr 110px 80px 100px;
  align-items: center;
  padding: 10px 14px;
  font-size: 13px;
  border-bottom: 1px solid var(--line-soft);
}
.cota-result-row:last-child { border-bottom: 0; }
.cota-result-head {
  background: var(--bg-sunk);
  font-size: 11px; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.04em;
  color: var(--fg-mute);
}
.cota-result-body { max-height: 480px; overflow-y: auto; }
.cota-rcol-cnpj  { font-family: "Geist Mono", monospace; }
.cota-rcol-name  { color: var(--fg-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cota-rcol-points,
.cota-rcol-time  { text-align: right; font-family: "Geist Mono", monospace; }
.cota-rcol-time  { color: var(--fg-mute); }
.cota-rcol-status { display: flex; justify-content: flex-end; }

/* ─────────────────────────────────────────────────────
   History route
   ───────────────────────────────────────────────────── */
.cota-history-list { display: flex; flex-direction: column; }
.cota-history-row {
  display: grid;
  grid-template-columns: 36px 1fr auto auto;
  gap: 14px; align-items: center;
  padding: 14px 4px;
  border-bottom: 1px solid var(--line-soft);
}
.cota-history-row:last-child { border-bottom: 0; }
.cota-history-icon {
  width: 36px; height: 36px;
  background: var(--bg-sunk);
  border: 1px solid var(--line);
  border-radius: var(--r-sm);
  display: grid; place-items: center;
  color: var(--fg-2);
}
.cota-history-title {
  font-size: 13px;
  font-family: "Geist Mono", monospace;
}
.cota-history-meta {
  font-size: 12px; color: var(--fg-mute);
  margin-top: 2px;
}

/* ─────────────────────────────────────────────────────
   Settings route — env rows
   ───────────────────────────────────────────────────── */
.cota-env-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid var(--line-soft);
  font-size: 13px;
  gap: 12px;
}
.cota-env-row:last-of-type { border-bottom: 0; }
.cota-env-label { color: var(--fg-2); flex-shrink: 0; }
.cota-env-value {
  color: var(--fg);
  font-family: "Geist Mono", monospace;
  font-size: 12.5px;
  text-align: right;
  word-break: break-all;
}
</style>
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def inject_css() -> None:
    """Inject Cota's CSS + Geist font links. Call this once near the top of
    `streamlit_app.py`, after `st.set_page_config(...)`."""
    import streamlit as st
    st.markdown(COTA_CSS, unsafe_allow_html=True)


def brand_mark(size: str = "lg", with_text: bool = True, tagline: str | None = "ANBIMA fund data, on demand") -> str:
    """Return HTML for the Cota brand mark (dark square with glowing emerald dot).

    `size` ∈ {"lg", "sm"}. `with_text` adds "Cota" beside the mark.

    NOTE: HTML is emitted with no leading whitespace per line. Markdown parsers
    (Streamlit uses CommonMark) treat a line indented by 4+ spaces as a code
    block, even when `unsafe_allow_html=True` is set, which causes our HTML
    to render as visible text instead of being parsed as elements.
    """
    sm = " sm" if size == "sm" else ""
    name_sm = " sm" if size == "sm" else ""
    text = ""
    if with_text:
        tagline_html = f'<div class="cota-brand-tagline">{tagline}</div>' if tagline and size == "lg" else ""
        text = (
            f'<div class="cota-brand-text">'
            f'<div class="cota-brand-name{name_sm}">Cota</div>'
            f'{tagline_html}'
            f'</div>'
        )
    return (
        f'<div class="cota-brand-row">'
        f'<div class="cota-mark{sm}" aria-hidden="true">'
        f'<span class="dot"></span><span class="bar"></span>'
        f'</div>'
        f'{text}'
        f'</div>'
    )


def topbar(user: str, route: str, status_text: str = "Scraper online") -> str:
    """Render Cota's sticky topbar.

    HTML is emitted as a single line (no leading whitespace) so Streamlit's
    markdown parser doesn't mistake indented lines for code blocks.
    """
    avatar = (user[:1] or "?").upper()
    user_safe = user.replace("<", "&lt;").replace(">", "&gt;")

    def _link(name: str, label: str) -> str:
        active = " active" if route == name else ""
        active_style = "color:var(--fg);background:var(--bg-sunk);" if active else ""
        return (
            f'<span class="cota-navlink{active}" '
            f'style="border:0;background:transparent;color:var(--fg-2);'
            f'font-size:13px;font-weight:500;padding:6px 12px;border-radius:6px;'
            f'{active_style}">{label}</span>'
        )

    return (
        '<div class="cota-topbar">'
        '<div class="cota-topbar-left">'
        f'{brand_mark(size="sm", with_text=True, tagline=None)}'
        '<span class="cota-topbar-divider"></span>'
        '<nav class="cota-topbar-nav">'
        f'{_link("scrape", "New scrape")}'
        f'{_link("history", "History")}'
        f'{_link("settings", "Settings")}'
        '</nav>'
        '</div>'
        '<div class="cota-topbar-right">'
        f'<span class="cota-status-pill"><span class="cota-status-dot"></span> {status_text}</span>'
        '<span class="cota-usermenu">'
        f'<span class="cota-avatar">{avatar}</span>'
        '<span class="cota-usermenu-text">'
        f'<span class="cota-usermenu-name">{user_safe}</span>'
        '<span class="cota-usermenu-role">Workspace admin</span>'
        '</span></span></div></div>'
    )


def page_head(title: str, sub: str, right_html: str = "") -> str:
    """Cota page header (large title + subtitle, optional right slot)."""
    return (
        '<div class="cota-page-head">'
        f'<div><h1 class="cota-page-title">{title}</h1>'
        f'<p class="cota-page-sub">{sub}</p></div>'
        f'<div>{right_html}</div>'
        '</div>'
    )


def footer(version: str = "v2.4.0", build: str = "build a91c3f") -> str:
    return (
        '<div class="cota-footer">'
        '<span>Cota · ANBIMA fund data scraper</span>'
        f'<span class="cota-muted">{version} · {build}</span>'
        '</div>'
    )


def login_bg() -> str:
    """Decorative grid + emerald glow used on the login page only."""
    return (
        '<div class="cota-login-bg" aria-hidden="true">'
        '<div class="cota-login-bg-grid"></div>'
        '<div class="cota-login-bg-glow"></div>'
        '</div>'
    )


# ---------------------------------------------------------------------------
# Stepper
# ---------------------------------------------------------------------------

_STEP_DEFS = [
    ("upload", "Upload",   "CNPJ list"),
    ("review", "Review",   "Verify & configure"),
    ("scrape", "Scrape",   "Fetch fund data"),
    ("done",   "Download", "Export results"),
]
_STEP_ORDER = {k: i for i, (k, _, _) in enumerate(_STEP_DEFS)}


def stepper(phase: str) -> str:
    """Render the four-step workflow indicator (Upload → Review → Scrape → Download).

    `phase` ∈ {"upload", "review", "scrape", "done"}.
    """
    cur = _STEP_ORDER.get(phase, 0)
    items = []
    for i, (key, label, help_text) in enumerate(_STEP_DEFS):
        if i < cur:
            state = "done"
            bullet = "✓"
        elif i == cur:
            state = "active"
            bullet = str(i + 1)
        else:
            state = "pending"
            bullet = str(i + 1)
        line = '<div class="cota-step-line"></div>' if i < len(_STEP_DEFS) - 1 else ""
        items.append(
            f'<li class="cota-step {state}">'
            f'<div class="cota-step-bullet">{bullet}</div>'
            '<div class="cota-step-text">'
            f'<div class="cota-step-label">{label}</div>'
            f'<div class="cota-step-help">{help_text}</div>'
            '</div>'
            f'{line}'
            '</li>'
        )
    return f'<ol class="cota-stepper" aria-label="Workflow progress">{"".join(items)}</ol>'


# ---------------------------------------------------------------------------
# CNPJ table
# ---------------------------------------------------------------------------

def cnpj_table(cnpjs: list, query: str = "", names: list | None = None) -> str:
    """Render a Cota-styled, searchable table of CNPJs.

    `cnpjs` is the full list (display all rows that contain `query`).
    `names` is an optional parallel list of fund names.
    """
    q = (query or "").strip()
    rows_html = []
    visible = 0
    for i, c in enumerate(cnpjs):
        c_str = str(c)
        if q and q not in c_str:
            continue
        visible += 1
        name = (names[i] if names and i < len(names) else "") or "—"
        name_safe = str(name).replace("<", "&lt;").replace(">", "&gt;")
        rows_html.append(
            '<div class="cota-cnpj-row">'
            f'<span class="cota-col-idx">{str(i + 1).zfill(2)}</span>'
            f'<span class="cota-col-cnpj">{c_str}</span>'
            f'<span class="cota-col-name">{name_safe}</span>'
            '<span class="cota-col-status"><span class="cota-tag cota-tag-ready">Ready</span></span>'
            '</div>'
        )

    body = (
        "".join(rows_html)
        if rows_html
        else f'<div class="cota-empty">No CNPJs match "{q}".</div>'
    )
    meta = f'<div class="cota-searchrow-meta">{visible} of {len(cnpjs)}</div>'

    return (
        '<div class="cota-cnpj-table">'
        '<div class="cota-cnpj-row cota-cnpj-head">'
        '<span class="cota-col-idx">#</span>'
        '<span class="cota-col-cnpj">CNPJ</span>'
        '<span class="cota-col-name">Estimated fund</span>'
        '<span class="cota-col-status">Status</span>'
        '</div>'
        f'<div class="cota-cnpj-body">{body}</div>'
        '</div>'
        f'{meta}'
    )


# ---------------------------------------------------------------------------
# Run summary (Review right column)
# ---------------------------------------------------------------------------

def run_summary(rows: list[tuple[str, str]]) -> str:
    """Render a small key/value summary block. Each row is (label, value)."""
    items = "".join(
        f'<div class="cota-run-summary-row"><span>{label}</span>'
        f'<span class="cota-run-summary-val">{value}</span></div>'
        for label, value in rows
    )
    return f'<div class="cota-run-summary">{items}</div>'


def setting_text(label: str, help_text: str) -> str:
    """Render the label/help text for a setting row. Place the Streamlit
    control widget immediately after via the normal `st.toggle` etc."""
    return (
        '<div class="cota-setting-text">'
        f'<div class="cota-setting-label">{label}</div>'
        f'<div class="cota-setting-help">{help_text}</div>'
        '</div>'
    )


# ---------------------------------------------------------------------------
# Scrape progress helpers
# ---------------------------------------------------------------------------

def progress_hero(
    pct: float,
    processed: str,
    success: int,
    failed: int,
    elapsed_min: float,
    remaining_min: float | None,
    throughput_per_min: float | None,
) -> str:
    """Return the HTML for the ring + 6 KPI tiles (progress hero block).

    `pct` is 0.0 – 1.0. All other values are pre-formatted by the caller.
    """
    import math
    r = 56
    c = 2 * math.pi * r
    offset = c * (1 - max(0.0, min(1.0, pct)))
    pct_pct = int(round(pct * 100))

    remaining_str = f"{remaining_min:.1f} min" if remaining_min is not None else "—"
    throughput_str = f"{throughput_per_min:.1f} /min" if throughput_per_min is not None else "—"

    ring = (
        '<div class="cota-ring-wrap">'
        '<svg width="140" height="140" viewBox="0 0 140 140">'
        f'<circle cx="70" cy="70" r="{r}" class="cota-ring-bg"/>'
        f'<circle cx="70" cy="70" r="{r}" class="cota-ring-fg" '
        f'stroke-dasharray="{c:.3f}" stroke-dashoffset="{offset:.3f}" '
        f'transform="rotate(-90 70 70)"/>'
        f'<text x="70" y="68" text-anchor="middle" class="cota-ring-pct">{pct_pct}%</text>'
        '<text x="70" y="86" text-anchor="middle" class="cota-ring-lab">complete</text>'
        '</svg></div>'
    )

    def stat(label: str, value: str, kind: str = "") -> str:
        cls = ("cota-stat " + kind).strip()
        return (
            f'<div class="{cls}">'
            f'<div class="cota-stat-label">{label}</div>'
            f'<div class="cota-stat-value">{value}</div>'
            '</div>'
        )

    failed_kind = "err" if failed > 0 else ""

    stats = (
        '<div class="cota-progress-stats">'
        f'{stat("Processed", processed, "accent")}'
        f'{stat("Success", str(success), "ok")}'
        f'{stat("Failed", str(failed), failed_kind)}'
        f'{stat("Elapsed", f"{elapsed_min:.1f} min")}'
        f'{stat("Remaining", remaining_str)}'
        f'{stat("Throughput", throughput_str)}'
        '</div>'
    )

    return f'<div class="cota-progress-hero">{ring}{stats}</div>'


def progress_bar_html(pct: float) -> str:
    """Thin emerald progress bar."""
    pct = max(0.0, min(1.0, pct))
    return (
        '<div class="cota-progress-bar-track">'
        f'<div class="cota-progress-bar-fill" style="width:{pct*100:.1f}%"></div>'
        '</div>'
    )


def activity_panel(events: list[dict], current_event: dict | None = None, limit: int = 8) -> str:
    """Live activity feed.

    `events` is a list of dicts with keys: cnpj, name, status ("success"|"failed"),
    points (int), ms (int). Most recent first is *not* required — we slice the
    last `limit` and reverse for display so newest is on top.

    `current_event` is an optional dict {cnpj, name} for the in-flight CNPJ
    (rendered with a shimmering "Fetching…" row).
    """
    rows = []
    if current_event:
        rows.append(
            '<div class="cota-activity-row pending">'
            '<span class="cota-act-dot pending"></span>'
            f'<span class="cota-act-cnpj">{current_event.get("cnpj","")}</span>'
            f'<span class="cota-act-name cota-shimmer">Fetching…</span>'
            '<span class="cota-act-points">—</span>'
            '<span class="cota-act-ms">…</span>'
            '</div>'
        )
    for ev in list(events)[-limit:][::-1]:
        status = ev.get("status", "success")
        cnpj = str(ev.get("cnpj", ""))
        name = str(ev.get("name", "")).replace("<", "&lt;").replace(">", "&gt;")
        if status == "success":
            points = f'{int(ev.get("points", 0))} points'
        else:
            points = "no data"
        ms = f'{int(ev.get("ms", 0))}ms'
        rows.append(
            f'<div class="cota-activity-row {status}">'
            f'<span class="cota-act-dot {status}"></span>'
            f'<span class="cota-act-cnpj">{cnpj}</span>'
            f'<span class="cota-act-name">{name}</span>'
            f'<span class="cota-act-points">{points}</span>'
            f'<span class="cota-act-ms">{ms}</span>'
            '</div>'
        )
    if not rows:
        body = '<div class="cota-empty">Warming up the driver…</div>'
    else:
        body = "".join(rows)

    return (
        '<div class="cota-activity">'
        '<div class="cota-activity-head">'
        '<span class="cota-activity-title">Live activity</span>'
        f'<span class="cota-activity-meta">last {limit} events</span>'
        '</div>'
        f'<div class="cota-activity-list">{body}</div>'
        '</div>'
    )


# ---------------------------------------------------------------------------
# Results page helpers
# ---------------------------------------------------------------------------

def success_circle(variant: str = "ok") -> str:
    """Large emerald-tinted circle with a check icon (or amber + ! if interrupted).

    `variant` ∈ {"ok", "warn"}.
    """
    cls = "cota-success-circle" + (" warn" if variant == "warn" else "")
    if variant == "warn":
        # exclamation mark for interrupted/partial runs
        icon_path = '<path d="M12 9v4"/><path d="M12 17h.01"/>'
    else:
        # check mark for clean completion
        icon_path = '<path d="m4 12 5 5L20 6"/>'
    return (
        f'<div class="{cls}">'
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        f'{icon_path}'
        '</svg>'
        '</div>'
    )


def kpi_row(items: list[tuple]) -> str:
    """Four (or N) KPI tiles in a grid.

    Each `item` is `(label, value)` or `(label, value, kind)` where kind
    is "ok" / "err" / "" (default).
    """
    tiles = []
    for it in items:
        if len(it) == 3:
            label, value, kind = it
        else:
            label, value = it
            kind = ""
        cls = ("cota-kpi " + kind).strip()
        tiles.append(
            f'<div class="{cls}">'
            f'<div class="cota-kpi-label">{label}</div>'
            f'<div class="cota-kpi-value">{value}</div>'
            '</div>'
        )
    return f'<div class="cota-kpi-row">{"".join(tiles)}</div>'


def result_table(events: list[dict], filter_by: str = "All") -> str:
    """Render the results table.

    `events` is the activity_events list (one dict per CNPJ).
    `filter_by` ∈ {"All", "Success", "Failed"} narrows the view.
    """
    keep = events
    if filter_by == "Success":
        keep = [e for e in events if e.get("status") == "success"]
    elif filter_by == "Failed":
        keep = [e for e in events if e.get("status") == "failed"]

    rows = []
    for e in keep:
        cnpj = str(e.get("cnpj", ""))
        name = str(e.get("name", "")).replace("<", "&lt;").replace(">", "&gt;")
        status = e.get("status", "success")
        if status == "success":
            points = f'{int(e.get("points", 0)):,}'
            tag = '<span class="cota-tag cota-tag-ok">✓ Success</span>'
        else:
            points = "—"
            tag = '<span class="cota-tag cota-tag-err">✗ Failed</span>'
        ms = f'{int(e.get("ms", 0))} ms'
        rows.append(
            '<div class="cota-result-row">'
            f'<span class="cota-rcol-cnpj">{cnpj}</span>'
            f'<span class="cota-rcol-name">{name}</span>'
            f'<span class="cota-rcol-points">{points}</span>'
            f'<span class="cota-rcol-time">{ms}</span>'
            f'<span class="cota-rcol-status">{tag}</span>'
            '</div>'
        )
    body = "".join(rows) or '<div class="cota-empty">No results to show.</div>'
    return (
        '<div class="cota-result-table">'
        '<div class="cota-result-row cota-result-head">'
        '<span class="cota-rcol-cnpj">CNPJ</span>'
        '<span class="cota-rcol-name">Fund name</span>'
        '<span class="cota-rcol-points">Data points</span>'
        '<span class="cota-rcol-time">Time</span>'
        '<span class="cota-rcol-status">Status</span>'
        '</div>'
        f'<div class="cota-result-body">{body}</div>'
        '</div>'
    )


# ---------------------------------------------------------------------------
# History row + Env row
# ---------------------------------------------------------------------------

_HISTORY_ICON_SVG = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
    'stroke-linejoin="round">'
    '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/>'
    '<path d="M3 3v5h5"/>'
    '<path d="M12 7v5l3 2"/>'
    '</svg>'
)


def history_row(run_id: str, meta: str, success_pct: float | None) -> str:
    """One row of the History list (no action buttons here — the Streamlit
    download_button widget is rendered separately by the caller)."""
    if success_pct is None:
        tag = '<span class="cota-tag cota-tag-ready">—</span>'
    elif success_pct >= 99.5:
        tag = '<span class="cota-tag cota-tag-ok">100%</span>'
    elif success_pct >= 90:
        tag = f'<span class="cota-tag cota-tag-ok">{success_pct:.0f}%</span>'
    else:
        tag = f'<span class="cota-tag cota-tag-warn">{success_pct:.0f}%</span>'
    return (
        '<div class="cota-history-row">'
        f'<div class="cota-history-icon">{_HISTORY_ICON_SVG}</div>'
        '<div>'
        f'<div class="cota-history-title">{run_id}</div>'
        f'<div class="cota-history-meta">{meta}</div>'
        '</div>'
        f'<div>{tag}</div>'
        '<div></div>'  # spacer; caller places the download_button below or beside
        '</div>'
    )


def env_row(label: str, value: str) -> str:
    return (
        '<div class="cota-env-row">'
        f'<span class="cota-env-label">{label}</span>'
        f'<span class="cota-env-value">{value}</span>'
        '</div>'
    )
