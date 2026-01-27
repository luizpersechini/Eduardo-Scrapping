# Web UI Implementation Plan - Phase 3

**Goal:** Create a simple web interface for non-technical users to scrape ANBIMA data
**Deployment:** Streamlit Cloud (free, deploy from GitHub)
**Target User:** Friend who needs to scrape data a couple times per month

---

## 🎯 Project Requirements

### Must Have
- ✅ Upload Excel file with CNPJs
- ✅ One-click scraping start
- ✅ Real-time progress display
- ✅ Download results as Excel
- ✅ No coding knowledge required
- ✅ Accessible via URL (online)
- ✅ Deploy from GitHub automatically

### Nice to Have
- 📧 Email notification when complete
- 📊 Historical scraping records
- 🔐 Simple password protection
- 📱 Mobile-friendly interface
- 📈 Statistics dashboard

---

## 🏗️ Architecture

### Technology Stack
```
Frontend:     Streamlit (Python-based web UI)
Backend:      Existing scrapers (stealth_scraper.py)
Deployment:   Streamlit Cloud (free tier)
Storage:      Temporary session storage
CI/CD:        Automatic from GitHub push
```

### File Structure
```
Eduardo-Scrapping/
├── streamlit_app.py          # Main UI application (NEW)
├── streamlit_utils.py         # Helper functions for UI (NEW)
├── requirements_streamlit.txt # Streamlit dependencies (NEW)
├── .streamlit/
│   └── config.toml           # Streamlit configuration (NEW)
├── stealth_scraper.py        # Existing scraper (reuse)
├── main_parallel.py          # Existing logic (reuse)
├── config.py                 # Existing config (reuse)
└── README_DEPLOYMENT.md      # Deployment guide (NEW)
```

---

## 📋 Implementation Steps

### Step 1: Create Streamlit App (streamlit_app.py)

**Main Components:**
1. **Header Section**
   - App title and description
   - Instructions for user

2. **File Upload Section**
   - Excel file uploader
   - CNPJ preview table
   - Validation (check file format)

3. **Scraping Control Section**
   - "Start Scraping" button
   - Settings (optional): workers, headless mode
   - Clear warnings/status

4. **Progress Display Section**
   - Progress bar (0-100%)
   - Current CNPJ being scraped
   - Success/Failed counters
   - Time elapsed
   - ETA (estimated time remaining)

5. **Results Section**
   - Success message
   - Download button for Excel results
   - Summary statistics

6. **Error Handling**
   - User-friendly error messages
   - Retry button
   - Help/FAQ section

### Step 2: Adapt Existing Scraper for Streamlit

**Modifications needed:**
```python
# Instead of printing to console:
print("Processing...")

# Use Streamlit components:
st.progress(0.5)
st.write("Processing...")
```

**Key Changes:**
- Replace `tqdm` progress bars with `st.progress()`
- Replace `print()` with `st.write()` or `st.info()`
- Add session state for progress tracking
- Store results in memory (st.session_state)

### Step 3: Configure Streamlit Cloud

**Requirements:**
1. GitHub repository (✅ already have)
2. Streamlit Cloud account (free)
3. Configuration files

**Files needed:**
- `requirements.txt` - All Python dependencies
- `.streamlit/config.toml` - App configuration
- `packages.txt` - System packages (for Chrome)

### Step 4: Handle Chrome/Selenium in Cloud

**Challenge:** Streamlit Cloud doesn't have Chrome by default

**Solutions:**
1. **Option A: Use undetected-chromedriver-auto**
   - Auto-downloads Chrome binary
   - Works in cloud environments
   - Already using in stealth mode

2. **Option B: Use Selenium Grid (external)**
   - BrowserStack/Sauce Labs
   - More reliable but costs money

3. **Option C: Use Parse.bot API**
   - No Chrome needed (API-based)
   - Most reliable for cloud
   - Small cost but guaranteed to work

**Recommendation:** Try Option A first, fallback to Option C if needed

### Step 5: Deploy to Streamlit Cloud

**Deployment Process:**
1. Push code to GitHub
2. Go to https://share.streamlit.io/
3. Connect GitHub account
4. Select repository: `luizpersechini/Eduardo-Scrapping`
5. Set main file: `streamlit_app.py`
6. Deploy (automatic)
7. Get URL: `https://eduardo-scrapping.streamlit.app/`

**Configuration:**
- Python version: 3.9+
- Branch: main
- Auto-deploy: ON (deploys on git push)

---

## 🎨 UI Mockup (Text-based)

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                   │
│  🏦 ANBIMA Fund Data Scraper                                     │
│  ════════════════════════════════════════════════════════        │
│                                                                   │
│  Welcome! Upload your CNPJ list and start scraping ANBIMA data. │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 📤 Step 1: Upload CNPJ List                               │  │
│  │                                                            │  │
│  │  [Browse Files]  or  [Drag & Drop Excel File]            │  │
│  │                                                            │  │
│  │  ℹ️  Use the template file: input_valid_cnpjs.xlsx       │  │
│  │     (36 validated CNPJs included)                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 📋 Preview: 36 CNPJs loaded                               │  │
│  │                                                            │  │
│  │  CNPJ                  Status                             │  │
│  │  ─────────────────────────────────────────                │  │
│  │  13.054.728/0001-48    ✓ Valid                           │  │
│  │  15.585.932/0001-10    ✓ Valid                           │  │
│  │  17.313.316/0001-36    ✓ Valid                           │  │
│  │  ... (show first 5)                                       │  │
│  │                                                            │  │
│  │  [View All CNPJs ▼]                                       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ ⚙️  Settings                                              │  │
│  │                                                            │  │
│  │  ☐ Stealth Mode (Recommended)          [ON]              │  │
│  │  Workers:                               [1] (Conservative)│  │
│  │                                                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  [🚀 Start Scraping]                                             │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 📊 Progress                                                │  │
│  │                                                            │  │
│  │  ████████████████░░░░░░░░ 65% Complete                   │  │
│  │                                                            │  │
│  │  Currently scraping: 26.841.302/0001-86                   │  │
│  │                                                            │  │
│  │  ✓ Success: 23 | ❌ Failed: 0 | ⏱️ Time: 52 min          │  │
│  │  📈 ETA: 28 minutes remaining                             │  │
│  │                                                            │  │
│  │  Latest Activity:                                         │  │
│  │  ✓ 17.313.316/0001-36 - Completed (22 data points)       │  │
│  │  ✓ 15.585.932/0001-10 - Completed (22 data points)       │  │
│  │  ⚙️ 26.841.302/0001-86 - In progress...                  │  │
│  │                                                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ ✅ Scraping Complete!                                      │  │
│  │                                                            │  │
│  │  📊 Results:                                              │  │
│  │     • Total CNPJs: 36                                     │  │
│  │     • Successful: 36 (100%)                               │  │
│  │     • Failed: 0                                           │  │
│  │     • Total time: 1 hour 20 minutes                       │  │
│  │     • Data points: 792 (36 funds × 22 dates avg)         │  │
│  │                                                            │  │
│  │  [⬇️  Download Results (Excel)]                           │  │
│  │                                                            │  │
│  │  📧 Email results? [Enter email] [Send]                   │  │
│  │                                                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ────────────────────────────────────────────────────────────   │
│  ℹ️  Help | 📖 Documentation | 🐛 Report Issue                  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Technical Implementation Details

### Session State Management
```python
# streamlit_app.py
import streamlit as st

# Initialize session state
if 'scraping_in_progress' not in st.session_state:
    st.session_state.scraping_in_progress = False
    st.session_state.progress = 0
    st.session_state.results = None
    st.session_state.cnpjs = []
```

### Progress Updates
```python
# Callback function for scraper progress
def update_progress(current, total, cnpj, status):
    st.session_state.progress = current / total
    st.session_state.current_cnpj = cnpj
    st.session_state.status = status
    # Force UI refresh
    st.rerun()
```

### File Handling
```python
# Upload handling
uploaded_file = st.file_uploader("Upload CNPJ List", type=['xlsx'])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.session_state.cnpjs = df['CNPJ'].tolist()
```

### Download Results
```python
# When scraping complete
if st.session_state.results:
    excel_buffer = io.BytesIO()
    st.session_state.results.to_excel(excel_buffer)

    st.download_button(
        label="Download Results",
        data=excel_buffer,
        file_name=f"anbima_results_{datetime.now():%Y%m%d_%H%M%S}.xlsx",
        mime="application/vnd.ms-excel"
    )
```

---

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] Create `streamlit_app.py`
- [ ] Create `streamlit_utils.py`
- [ ] Update `requirements.txt` with Streamlit
- [ ] Create `.streamlit/config.toml`
- [ ] Create `packages.txt` for system dependencies
- [ ] Test locally: `streamlit run streamlit_app.py`
- [ ] Commit and push to GitHub

### Streamlit Cloud Setup
- [ ] Create Streamlit Cloud account (https://share.streamlit.io/)
- [ ] Connect GitHub account
- [ ] Select repository: Eduardo-Scrapping
- [ ] Configure deployment:
  - Main file: `streamlit_app.py`
  - Python version: 3.9+
  - Branch: main
- [ ] Deploy
- [ ] Test deployed app
- [ ] Share URL with friend

### Post-Deployment
- [ ] Create user guide (screenshots + instructions)
- [ ] Test from different devices/browsers
- [ ] Monitor usage/errors (Streamlit Analytics)
- [ ] Setup error notifications (optional)
- [ ] Document troubleshooting steps

---

## 💰 Cost Analysis

### Streamlit Cloud Free Tier
- **Cost:** $0/month
- **Includes:**
  - 1 private app OR unlimited public apps
  - 1 GB RAM
  - 2 CPU cores
  - Community support

**Sufficient for:**
- Monthly scraping sessions (couple times per month)
- 36 CNPJs per run (~1.5 hours)
- Single user (your friend)

### If Free Tier is Insufficient
**Streamlit Cloud Starter:** $20/month
- 3 private apps
- More resources
- Priority support

**Alternative:** Self-host on your server (free but requires maintenance)

---

## 🔐 Security Considerations

### Authentication
**Option 1:** No authentication (app is publicly accessible)
- Simple URL
- Anyone with link can use
- ⚠️ Risk: Others could use your resources

**Option 2:** Simple password (Streamlit built-in)
```python
import hmac
import streamlit as st

def check_password():
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], "your_secret"):
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False

    return st.session_state["password_correct"]

if not check_password():
    st.stop()
```

**Option 3:** GitHub OAuth (Streamlit Teams feature)
- Requires paid plan
- Most secure

**Recommendation:** Start with Option 1 (no auth), add Option 2 if needed

### Data Privacy
- ✅ Results stored only in session (temporary)
- ✅ No data persistence (unless user downloads)
- ✅ Files deleted after session ends
- ⚠️ Consider: Don't log sensitive CNPJ data

---

## 📊 Testing Strategy

### Local Testing
```bash
# Install Streamlit
pip install streamlit

# Run locally
streamlit run streamlit_app.py

# Open browser: http://localhost:8501
```

### Test Cases
1. ✅ Upload valid Excel file → Should preview CNPJs
2. ✅ Upload invalid file → Should show error
3. ✅ Start scraping → Should show progress
4. ✅ Complete scraping → Should enable download
5. ✅ Download results → Should get valid Excel
6. ❌ Rate limiting → Should handle gracefully
7. ❌ Network error → Should show retry option
8. ❌ Chrome crash → Should restart/retry

---

## 🎓 User Guide (for your friend)

### Quick Start
1. Go to: `https://eduardo-scrapping.streamlit.app/`
2. Click "Upload CNPJ List"
3. Select `input_valid_cnpjs.xlsx` (or your own list)
4. Click "Start Scraping"
5. Wait for completion (shows progress bar)
6. Click "Download Results"
7. Open Excel file with data

### Troubleshooting
**Problem:** Upload fails
**Solution:** Make sure file is .xlsx format with "CNPJ" column

**Problem:** Scraping stuck
**Solution:** Refresh page and try again (or report issue)

**Problem:** Download not working
**Solution:** Check browser allows downloads, try different browser

---

## 📈 Future Enhancements

### Phase 3.1 (Nice to Have)
- [ ] Email notifications when scraping completes
- [ ] Historical scraping records/dashboard
- [ ] Scheduling (automatic monthly scraping)
- [ ] Export to Google Sheets (instead of download)

### Phase 3.2 (Advanced)
- [ ] Multi-user support with accounts
- [ ] API endpoint for programmatic access
- [ ] Integration with Parse.bot as fallback
- [ ] Real-time charts/visualizations
- [ ] Mobile app (Progressive Web App)

---

## 🎯 Success Criteria

### MVP (Minimum Viable Product)
- ✅ User can upload CNPJ list
- ✅ User can start scraping with one click
- ✅ User can see progress in real-time
- ✅ User can download results
- ✅ Works on desktop and mobile browsers
- ✅ Accessible via URL (no installation)

### Definition of Done
- ✅ Deployed to Streamlit Cloud
- ✅ URL shared with friend
- ✅ Friend successfully scraped data
- ✅ User guide created
- ✅ No errors during first use

---

## 🗓️ Timeline Estimate

**Total:** 4-6 hours

- **Planning:** 30 minutes ✅ (this document)
- **Development:** 2-3 hours
  - Streamlit app: 1.5 hours
  - Scraper integration: 1 hour
  - Testing: 30 minutes
- **Deployment:** 1 hour
  - Streamlit Cloud setup: 30 minutes
  - Testing deployed app: 30 minutes
- **Documentation:** 1 hour
  - User guide: 30 minutes
  - README updates: 30 minutes
- **Buffer:** 1 hour (for unexpected issues)

---

**Next Steps:**
1. Review this plan
2. Decide on deployment platform (Streamlit recommended)
3. Start implementing `streamlit_app.py`
4. Test locally
5. Deploy to Streamlit Cloud
6. Share URL with friend

**Status:** Ready to implement
**Priority:** High (friend needs monthly scraping)
