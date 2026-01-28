# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
