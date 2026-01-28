# Deployment Guide - ANBIMA Fund Data Scraper

## 🚀 Quick Deployment to Streamlit Cloud

### Prerequisites
- GitHub account: `luizpersechini`
- Repository: https://github.com/luizpersechini/Eduardo-Scrapping
- Latest commit pushed to `main` branch

### Deployment Steps

1. **Go to Streamlit Cloud**
   - Visit: https://share.streamlit.io/
   - Sign in with GitHub account

2. **Deploy New App** (or update existing)
   - Click "New app" button
   - Fill in the details:
     - **Repository**: `luizpersechini/Eduardo-Scrapping`
     - **Branch**: `main`
     - **Main file path**: `streamlit_app.py`
     - **App URL**: Custom URL (e.g., `eduardo-scrapping`)

3. **Advanced Settings** (Recommended)
   - Python version: **3.11** (recommended for stability)
   - No environment variables needed (API keys disabled)

4. **Deploy**
   - Click "Deploy!" button
   - Wait 2-5 minutes for deployment
   - Monitor build logs for any issues

### 📋 Current Version

- **Version**: 1.0.0
- **Latest Commit**: ff6da7b - "Add version control to UI"
- **Previous Commit**: 17d0cc4 - "Fix background stability and activity log duplicates"

### 🔑 Login Credentials

Stored in: `EDUARDO_CREDENTIALS.txt` (gitignored)

- **Username**: `eduardo`
- **Password**: `ZNfXWn3UU7k13Vh9mqZAHg11qKwtYgAOTcNPgITk_Is`

### ✅ Features Deployed

- ✅ Login authentication with SHA-256 hashed password
- ✅ Version control display (header + sidebar)
- ✅ Activity log without duplicates
- ✅ Background/sleep stability with auto-recovery
- ✅ Stealth mode scraping with anti-spam
- ✅ Excel upload/download
- ✅ Real-time progress tracking
- ✅ Automatic retry logic (up to 3 attempts)

### 🔧 Technical Details

**Dependencies**:
- Python 3.11+
- Streamlit >= 1.28.0
- pandas >= 2.2.0
- selenium == 4.15.2
- undetected-chromedriver >= 3.5.5

**Chrome Options for Background Stability**:
- Disabled background throttling
- Disabled renderer backgrounding
- Keep-alive process management
- Automatic driver recovery

### 📊 Post-Deployment

After successful deployment:
- App will auto-redeploy on every push to `main` branch
- Version number will update automatically from VERSION file
- Git commit hash will show in sidebar

### ⚠️ Troubleshooting

**If deployment fails**:
1. Check Python version (use 3.11, not 3.13)
2. Review Streamlit Cloud build logs
3. Verify all dependencies in requirements.txt
4. Check for missing files in repository

**Common Issues**:
- **Chromium not found**: Streamlit Cloud provides Chromium automatically
- **Module not found**: Check requirements.txt is up to date
- **Build timeout**: May need to reduce dependencies or optimize imports

### 🔄 Auto-Deployment

The app is configured for automatic deployment:
- Every push to `main` branch triggers redeployment
- Can be paused in Streamlit Cloud dashboard settings
- Build logs available in Streamlit Cloud interface

### 📝 Version Management

To update version:
1. Edit `VERSION` file (e.g., change to `1.0.1`)
2. Update `CHANGELOG.md` with changes
3. Commit and push to GitHub
4. Streamlit Cloud will auto-deploy with new version

---

**Repository**: https://github.com/luizpersechini/Eduardo-Scrapping  
**Streamlit Cloud**: https://share.streamlit.io/  
**Documentation**: See README.md, SECURITY.md, CHANGELOG.md
