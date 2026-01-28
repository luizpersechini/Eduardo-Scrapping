# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
