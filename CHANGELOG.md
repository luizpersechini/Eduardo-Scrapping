# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.4] - 2026-01-28

### Fixed
- **Critical**: Enhanced anti-bot detection evasion for ANBIMA website
- ChromeDriver being detected and killed by anti-bot systems
- Repeated connection failures due to bot detection

### Added
- Enhanced stealth measures to avoid automation detection:
  - Disable `AutomationControlled` blink feature
  - Exclude automation switches
  - Override `navigator.webdriver` property
  - CDP command to set realistic user agent
  - Auto-detect Chrome version to avoid mismatch
- Warning in UI when headless mode is enabled
- Increased delays between actions (8-15 seconds vs 5-10 seconds)

### Changed
- **Headless mode now defaults to FALSE** (OFF) in UI
- Longer delays between actions to appear more human
- More realistic browser fingerprint
- Enhanced logging for anti-bot detection issues
- Recommend non-headless mode for better success rate

### Why This Matters
ANBIMA's anti-bot system was detecting and blocking the scraper,
causing repeated ChromeDriver crashes. Enhanced stealth measures
make the scraper appear more like a real human user.

**Important**: Headless mode is MORE likely to be detected. For best
results, run with headless mode disabled (visible browser window).

## [1.0.3] - 2026-01-28

### Fixed
- **Critical**: ChromeDriver connection refused errors - "Max retries exceeded with url: /session/..."
- **Critical**: Driver crashes causing entire batch to fail
- Connection loss detection and automatic recovery mid-scraping
- Improved driver health checks (test both URL and title)
- Longer wait time (5s) before driver recovery for stability

### Added
- `safe_driver_operation()` wrapper for automatic connection recovery
- All driver operations now wrapped with connection error detection
- Specific error detection for "connection refused" and "max retries exceeded"
- Driver recovery attempts before every critical operation
- Verification that recovered driver is responsive before continuing

### Changed
- Driver recovery now waits 5 seconds instead of 2 seconds
- Multiple driver health checks before operations
- Each scraping step (search, get name, navigate, extract) wrapped with recovery logic
- Better error messages distinguish connection errors from other failures

### Technical Details
- Detects: "connection refused", "max retries exceeded", "cannot call" errors
- Auto-recovery: Up to 2 attempts per operation with driver reinitization
- Health verification: Tests both `current_url` and `title` properties
- Clean shutdown: Forces driver.quit() and clears references before recovery

## [1.0.2] - 2026-01-28

### Added
- **Comprehensive session logging** - Every scraping session now creates a detailed log file
- **Downloadable log files** - Users can download session logs for troubleshooting
- **Real-time log viewer** - View recent logs in sidebar (last 50 lines)
- **Per-CNPJ timing** - Logs show exact time taken for each CNPJ
- **Full error tracebacks** - Complete stack traces logged for all errors
- **Session statistics** - Detailed summary logged at start and completion

### Logging Details
- Log files saved to `session_logs/` directory
- Filename format: `scraping_session_YYYYMMDD_HHMMSS.log`
- Captures: file uploads, driver initialization, CNPJ progress, success/failures, errors, completion stats
- Includes timestamps, log levels (INFO, WARNING, ERROR, DEBUG)
- Download button available in results section and sidebar
- Log file size displayed in UI

### Why This Helps
- Users without Streamlit admin access can now capture and share logs
- Detailed diagnostics for "lost connection" and hanging issues
- Complete audit trail of every scraping session
- Easy to share logs with support for debugging

## [1.0.1] - 2026-01-28

### Fixed
- **Critical**: Scraper hanging at 83% progress - added per-CNPJ timeout protection (3 minutes max)
- **Critical**: UI becoming unresponsive with white overlay - improved exception handling with try/catch per CNPJ
- Individual CNPJ failures no longer stop entire scraping process
- Added graceful degradation - partial results are always saved
- Improved error messages in activity log (truncated to 50 chars)
- Always close scraper properly even if errors occur (finally block)

### Added
- Per-CNPJ timeout protection (MAX_CNPJ_TIMEOUT = 180 seconds)
- Timeout checks at each scraping step (search, get name, navigate, extract)
- Individual CNPJ exception handling to prevent cascade failures
- Better progress tracking continues even when individual CNPJs fail

### Changed
- Exception handling now wraps each CNPJ individually
- Process results even if some CNPJs failed
- Display warnings instead of errors for non-critical issues

## [1.0.0] - 2026-01-27

### Added
- Version control display in UI (sidebar and header)
- Automatic driver recovery for background/sleep stability
- Activity log with real-time updates
- Login authentication with SHA-256 hashed password
- Stealth mode scraping with anti-spam protection
- Excel file upload and download
- Real-time progress tracking with metrics
- Headless and visible browser modes
- Comprehensive security documentation

### Fixed
- Activity log duplicates issue (using st.empty() placeholder)
- Browser stopping when Chrome goes to background
- Browser stopping during computer sleep
- WebDriver connection recovery with automatic retry (up to 3 attempts)
- Deprecation warnings for use_container_width parameter

### Security
- Removed hardcoded API keys from codebase
- Added environment variable support for secrets
- Enhanced .gitignore for sensitive files
- Created SECURITY.md with best practices
- Generated secure 32-character random password for authentication

### Changed
- Chrome options optimized for background stability
- Retry logic with exponential backoff
- Driver kept alive in same process (use_subprocess=False)
- Template download removed (users upload their own files)

### Technical
- Python 3.11+ compatibility
- pandas >= 2.2.0 for Python 3.13 support
- undetected-chromedriver >= 3.5.5
- Added setuptools for distutils compatibility
