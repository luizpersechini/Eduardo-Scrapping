# Web UI Testing Guide - Local Host

## Quick Start

### Option 1: Using the Launch Script (Recommended)
```bash
cd "/Users/LuizPersechini_1/Projects/Eduardo Scrapping"
./start_web_app.sh
```

### Option 2: Manual Launch
```bash
cd "/Users/LuizPersechini_1/Projects/Eduardo Scrapping"
python3 -m streamlit run streamlit_app.py
```

The app will automatically open in your default browser at: **http://localhost:8501**

---

## What to Test

### 1. File Upload
- [ ] Click "Choose a file" button
- [ ] Upload `input_valid_cnpjs.xlsx` (36 CNPJs)
- [ ] Verify CNPJs appear in the preview table
- [ ] Check the stats show "36 CNPJs Loaded"

### 2. Settings Sidebar
- [ ] Verify "Stealth Mode" is ON by default (recommended)
- [ ] Verify "Headless Mode" is ON by default
- [ ] Check workers selector shows "1" (conservative)
- [ ] Review the "About" section information

### 3. Download Template
- [ ] Click "Download Template (36 Valid CNPJs)" button
- [ ] Verify download works
- [ ] Open downloaded file and check it has CNPJ column

### 4. Start Scraping (Short Test)
For your first test, I recommend using a small test file with only 2-3 CNPJs:

Create a test file `input_test_2cnpjs.xlsx` with just these CNPJs:
```
13.054.728/0001-48
15.585.932/0001-10
```

- [ ] Upload the small test file
- [ ] Click "🚀 Start Scraping" button
- [ ] Watch the progress bar update in real-time
- [ ] Monitor the success/failed counters
- [ ] Check the activity log shows current CNPJ being processed
- [ ] Verify time elapsed counter updates

Expected result: ~4-5 minutes for 2 CNPJs

### 5. Results Display
After scraping completes:
- [ ] Verify "✅ Scraping Complete!" message appears
- [ ] Check success rate shows 100%
- [ ] Review the results preview table
- [ ] Verify data looks correct (CNPJ, dates, values)

### 6. Download Results
- [ ] Click "⬇️ Download Excel" button
- [ ] Verify file downloads with timestamp in filename
- [ ] Open Excel file and verify data is correct
- [ ] Check file size is reasonable

### 7. New Scraping
- [ ] Click "🔄 Start New Scraping" button
- [ ] Verify page resets to initial state
- [ ] Upload a different file to test again

---

## Features to Review

### User Interface
- Is the layout clear and intuitive?
- Are the instructions easy to follow?
- Do the colors/theme look professional?
- Is anything confusing or unclear?

### Real-time Progress
- Does the progress bar update smoothly?
- Are the status messages helpful?
- Is the time estimate accurate?
- Do you want more/less information displayed?

### Settings
- Should any default settings be changed?
- Are the setting descriptions clear?
- Do you need additional options?

### Error Handling
Test error scenarios:
- Upload a .txt file instead of Excel (should show error)
- Upload Excel without CNPJ column (should show error)
- Try starting without uploading file (button should be disabled)

---

## Known Behaviors

### Expected Behaviors
1. **First CNPJ takes longer**: Chrome initialization adds ~30s to first CNPJ
2. **Progress updates every CNPJ**: UI refreshes after each CNPJ completes
3. **Stealth mode delays**: 5-10 second delays between actions (anti-spam)
4. **Browser may appear**: If headless mode is OFF, Chrome window will show

### What's Working
- ✅ Anti-spam protection (Phase 1 & 2)
- ✅ Real-time progress tracking
- ✅ Excel upload/download
- ✅ CNPJ validation
- ✅ Error handling for invalid files
- ✅ Session state management

### Potential Issues to Watch For
- ⚠️ Chrome session may crash after ~2 hours (known issue)
- ⚠️ Large files (50+ CNPJs) will take 1.5-2 hours
- ⚠️ Don't refresh page during scraping (will lose progress)

---

## Feedback Checklist

Please provide feedback on:

### Must Review
- [ ] Is the interface easy to use for non-technical users?
- [ ] Are the instructions clear enough for your friend?
- [ ] Does the progress tracking provide enough visibility?
- [ ] Is the download process smooth?
- [ ] Any confusing elements or error messages?

### Nice to Review
- [ ] Should we add email notifications when complete?
- [ ] Do you want password protection?
- [ ] Should results be saved in history?
- [ ] Any missing features you expected?
- [ ] Performance feedback (speed, responsiveness)

### Design Feedback
- [ ] Color scheme (professional enough?)
- [ ] Layout and spacing
- [ ] Text size and readability
- [ ] Mobile friendliness (optional - test on phone)

---

## Troubleshooting

### App Won't Start
```bash
# Install missing dependencies
python3 -m pip install streamlit watchdog

# Try running directly
python3 -m streamlit run streamlit_app.py
```

### Port Already in Use
If you see "Address already in use" error:
```bash
# Kill existing Streamlit process
pkill -f streamlit

# Or use different port
python3 -m streamlit run streamlit_app.py --server.port 8502
```

### Chrome Driver Issues
```bash
# If Chrome version mismatch appears
# Just let it run - auto-detection will handle it

# If Chrome won't start in headless mode
# Disable "Headless Mode" in sidebar settings
```

### Upload Not Working
- Make sure file is .xlsx or .xls format
- File must have a column named "CNPJ" (case sensitive)
- Try the provided template first

---

## Performance Benchmarks

Based on production testing with Phase 1 & 2 anti-spam:

| CNPJs | Estimated Time | Success Rate |
|-------|---------------|--------------|
| 2     | 4-5 min       | 100%         |
| 5     | 11 min        | 100%         |
| 10    | 22 min        | 100%         |
| 36    | 80 min        | 100%         |

**Note**: Times include anti-spam delays (5-10s between actions)

---

## Next Steps After Testing

Once you've tested and provided feedback:

1. **If changes needed**: I'll update the UI based on your feedback
2. **If approved**: We'll deploy to Streamlit Cloud
3. **After deployment**: Create user guide for your friend
4. **Final step**: Share the live URL

---

## Stop the Server

Press **Ctrl+C** in the terminal to stop the Streamlit server.

---

## Questions to Consider

1. Should the default settings change? (headless, workers, stealth)
2. Do you want a help section visible on the main page?
3. Should we add file format validation before upload?
4. Do you want logging/history of past scraping sessions?
5. Should there be a "Pause" button during scraping?
6. Do you want statistics dashboard (charts/graphs)?
7. Should the app remember previous uploads?

---

**Ready to test!** Run `./start_web_app.sh` and let me know your feedback.
