# Session Logging Guide

## Overview

Version 1.0.2 introduces comprehensive session logging that captures every detail of your scraping sessions. **You don't need admin access** to download and share these logs for troubleshooting.

## What Gets Logged

Every scraping session creates a detailed log file that captures:

### 1. Session Start
```
================================================================================
NEW SCRAPING SESSION STARTED
Version: 1.0.2
Timestamp: 2026-01-28T14:30:00
================================================================================
```

### 2. File Upload
```
File uploaded: my_cnpjs.xlsx
CNPJs loaded: 60
CNPJ list: ['12.345.678/0001-90', '23.456.789/0001-80', ...]
```

### 3. Scraping Configuration
```
================================================================================
SCRAPING STARTED
Total CNPJs: 60
Stealth Mode: True
Headless Mode: True
Start Time: 2026-01-28T14:31:00
================================================================================
```

### 4. WebDriver Status
```
WebDriver initialized successfully
```

### 5. Per-CNPJ Progress
For each CNPJ, logs capture:
- **Success**: `[1/60] SUCCESS: 12.345.678/0001-90 - 22 data points - 45.3s`
- **Failure**: `[2/60] FAILED: 23.456.789/0001-80 - Status: Not found - 30.1s`
- **Exception**: `[3/60] EXCEPTION: 34.567.890/0001-70 - Timeout exceeded (180s) - 180.2s`

### 6. Full Error Details
When errors occur:
```
[50/60] EXCEPTION: 45.678.901/0001-60 - WebDriver error: Connection refused
Traceback:
  File "stealth_scraper.py", line 567, in scrape_fund_data
    result = self.search_fund(cnpj)
  File "stealth_scraper.py", line 234, in search_fund
    self.driver.current_url
selenium.common.exceptions.WebDriverException: Message: unknown error: net::ERR_CONNECTION_REFUSED
```

### 7. Session Completion
```
================================================================================
SCRAPING COMPLETED
Total CNPJs: 60
Successful: 58
Failed: 2
Total Time: 52.45 minutes
Avg Time per CNPJ: 52.5 seconds
================================================================================
```

## How to Access Logs

### Method 1: Sidebar Log Viewer (Real-Time)

1. Look at the left sidebar while scraping
2. Find the **📋 Session Log** section
3. Expand **"View Recent Logs"**
4. See the last 50 lines of the log file in real-time

### Method 2: Download from Sidebar

1. Scroll down in the sidebar
2. Under **📋 Session Log**, you'll see the log file size (e.g., "Log file: 15.2 KB")
3. Click **"📥 Download Session Log"**
4. Then click **"Save Log File"**
5. Log file will be downloaded to your computer

### Method 3: Download After Completion

1. After scraping completes, go to **📥 Download Results** section
2. You'll see two buttons:
   - **⬇️ Download Excel** - Your scraped data
   - **📋 Download Log** - The session log file
3. Click **📋 Download Log** to save the log file

## Log File Details

- **Location on server**: `session_logs/scraping_session_YYYYMMDD_HHMMSS.log`
- **Filename format**: `scraping_session_20260128_143000.log`
- **Encoding**: UTF-8
- **Size**: Typically 10-50 KB per session
- **Retention**: Logs are kept until manually deleted

## Using Logs for Troubleshooting

### Scenario 1: "Lost Connection" at 83%

If your scraping gets stuck or loses connection:

1. Download the log file using any method above
2. Look for the last CNPJ that was processed:
   ```
   [50/60] SUCCESS: 12.345.678/0001-90 - 22 data points - 45.3s
   ```
3. Check if there's an exception after that:
   ```
   [51/60] EXCEPTION: 23.456.789/0001-80 - WebDriver error: Connection refused
   ```
4. Share the log file with support for detailed analysis

### Scenario 2: Individual CNPJ Failures

If specific CNPJs fail:

1. Download the log
2. Search for the CNPJ number (e.g., `12.345.678/0001-90`)
3. Look at the status:
   - `FAILED` = ANBIMA returned an error
   - `EXCEPTION` = Technical error occurred
4. Check the error message for the reason

### Scenario 3: Performance Issues

If scraping is slow:

1. Download the log
2. Look at the timing for each CNPJ (last number on each line)
3. Examples:
   - `45.3s` - Normal
   - `180.2s` - Hit timeout (3 minutes max)
   - Check average time at the end: `Avg Time per CNPJ: 52.5 seconds`

## Sharing Logs with Support

When reporting issues:

1. **Download the log file** after the session
2. **Include the log file** when contacting support
3. **Mention**:
   - How many CNPJs you tried to scrape
   - At what percentage it failed (if applicable)
   - What error message you saw in the UI

Example message:
```
I ran a batch of 60 CNPJs and it got stuck at 83% (50 CNPJs completed).
The UI showed "lost connection" error.
Attached is the session log file: scraping_session_20260128_143000.log
```

## Log Levels Explained

- **INFO**: Normal operations (file upload, CNPJ success, completion)
- **WARNING**: Non-critical issues (CNPJ failures, could not close driver)
- **ERROR**: Errors that affect functionality (file read errors, driver init failed)
- **DEBUG**: Detailed technical info (CNPJ lists, full tracebacks)

## Privacy Note

Log files contain:
- ✅ CNPJs you're scraping
- ✅ Fund names found
- ✅ Technical errors and timing
- ❌ No passwords or authentication data
- ❌ No personal information

It's safe to share log files with support for troubleshooting.

## Example Log Excerpt

```
2026-01-28 14:31:00 - INFO - ================================================================================
2026-01-28 14:31:00 - INFO - SCRAPING STARTED
2026-01-28 14:31:00 - INFO - Total CNPJs: 3
2026-01-28 14:31:00 - INFO - Stealth Mode: True
2026-01-28 14:31:00 - INFO - Headless Mode: True
2026-01-28 14:31:05 - INFO - WebDriver initialized successfully
2026-01-28 14:31:05 - INFO - [1/3] Starting CNPJ: 12.345.678/0001-90
2026-01-28 14:31:48 - INFO - [1/3] SUCCESS: 12.345.678/0001-90 - 22 data points - 43.2s
2026-01-28 14:31:48 - INFO - [2/3] Starting CNPJ: 23.456.789/0001-80
2026-01-28 14:32:15 - WARNING - [2/3] FAILED: 23.456.789/0001-80 - Status: Not found - 27.1s
2026-01-28 14:32:15 - INFO - [3/3] Starting CNPJ: 34.567.890/0001-70
2026-01-28 14:32:58 - INFO - [3/3] SUCCESS: 34.567.890/0001-70 - 22 data points - 43.0s
2026-01-28 14:33:00 - INFO - Processing 3 results...
2026-01-28 14:33:01 - INFO - Results processed successfully - 44 rows
2026-01-28 14:33:01 - INFO - ================================================================================
2026-01-28 14:33:01 - INFO - SCRAPING COMPLETED
2026-01-28 14:33:01 - INFO - Total CNPJs: 3
2026-01-28 14:33:01 - INFO - Successful: 2
2026-01-28 14:33:01 - INFO - Failed: 1
2026-01-28 14:33:01 - INFO - Total Time: 2.02 minutes
2026-01-28 14:33:01 - INFO - Avg Time per CNPJ: 40.4 seconds
2026-01-28 14:33:01 - INFO - ================================================================================
```

---

**Questions?** Contact support with your log file attached for detailed assistance.
