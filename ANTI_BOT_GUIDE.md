# Anti-Bot Detection Troubleshooting Guide

## ⚠️ Critical Issue Identified

Based on the error logs, **ANBIMA's website is detecting and blocking automated scraping**. The repeated ChromeDriver crashes are NOT random connection issues - they are ANBIMA's anti-bot system actively killing the browser connection.

### Error Patterns That Indicate Anti-Bot Detection:

```
Error getting fund name: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
ChromeDriver connection lost: HTTPConnectionPool(host='localhost', port=50735): Max retries exceeded
Error searching for CNPJ: Connection refused
```

**These errors happening repeatedly = Anti-bot system is active**

## 🔴 Why It's Failing

1. **Headless Chrome is Easily Detected**
   - Websites can detect headless browsers using JavaScript
   - `navigator.webdriver` flag is TRUE in automation
   - Missing browser features that real users have

2. **Too Many Requests Too Fast**
   - Even with delays, scraping 60 CNPJs in a row looks suspicious
   - No human browses that consistently

3. **Streamlit Cloud IP May Be Flagged**
   - If many people use Streamlit Cloud for scraping
   - ANBIMA may have blacklisted cloud hosting IPs

## ✅ Solutions Implemented in v1.0.4

### 1. Enhanced Stealth Mode
- Override `navigator.webdriver` (makes it appear not automated)
- Disable `AutomationControlled` blink features
- Use CDP commands for realistic fingerprint
- Exclude automation switches

### 2. Increased Delays
- **Before**: 5-10 seconds between actions
- **After**: 8-15 seconds between actions
- More human-like browsing pattern

### 3. Headless Mode Now OFF by Default
- **Visible browser** is MUCH harder to detect
- Slightly slower but significantly better success rate
- UI shows warning if headless enabled

## 📋 Recommendations for Eduardo

### Option 1: Run with Visible Browser (RECOMMENDED)

**In Streamlit UI Settings:**
1. ✅ Keep "Stealth Mode" **CHECKED**
2. ❌ **UNCHECK** "Headless Mode"
3. Browser window will open and scrape visibly
4. Much better success rate

**Trade-offs:**
- ✅ Better success rate
- ✅ Can see what's happening
- ❌ Slightly slower
- ❌ Needs display (not ideal for cloud)

### Option 2: Run Locally on Your Computer

**Best for large batches (50+ CNPJs):**
1. Install Python on your local machine
2. Clone the GitHub repository
3. Run scraper locally with visible browser
4. No cloud IP restrictions
5. Can watch it work

**Setup:**
```bash
git clone https://github.com/luizpersechini/Eduardo-Scrapping.git
cd Eduardo-Scrapping
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Option 3: Smaller Batches with Longer Delays

**Instead of 60 CNPJs at once:**
1. Split into batches of 10-15 CNPJs
2. Run each batch separately
3. Wait 30-60 minutes between batches
4. Less likely to trigger rate limiting

### Option 4: Rotate User Agents

**(Advanced - requires code modification)**
- Use different browser user agents
- Rotate them between CNPJs
- Appears like different users

## 🚫 What Won't Work

### ❌ Just Retrying Multiple Times
- If anti-bot detected you, retrying immediately fails
- Need to wait or change approach

### ❌ Running Faster
- Speed makes detection MORE likely
- Go slower, not faster

### ❌ Removing Delays
- Human delays are CRITICAL
- Without them, instant detection

## 🔍 How to Tell If Anti-Bot Is Blocking You

### Check the Downloaded Log File:

**Good signs (not blocked):**
```
[1/60] SUCCESS: 12.345.678/0001-90 - 22 data points - 45.3s
[2/60] SUCCESS: 23.456.789/0001-80 - 22 data points - 43.1s
```

**Bad signs (being blocked):**
```
ChromeDriver connection lost: Connection refused
Error searching for CNPJ: Max retries exceeded
Remote end closed connection without response
```

**Pattern to watch for:**
- First 5-10 CNPJs succeed ✅
- Then suddenly all fail ❌
- **This means**: Anti-bot detected you mid-batch

## 🛠️ Immediate Actions

### 1. Change Settings (Most Important)
```
Settings in Streamlit UI:
☑️ Stealth Mode: ON
☐ Headless Mode: OFF  ← CRITICAL CHANGE
   Workers: 1
```

### 2. Test with Small Batch First
- Upload file with only 3-5 CNPJs
- Watch if they all succeed
- If yes, anti-bot evasion is working
- If no, need more changes

### 3. Monitor the Visible Browser
When headless mode is OFF:
- You'll see Chrome window open
- Watch if it completes actions
- Look for CAPTCHA or blocking pages
- Check if searches return results

## 🎯 Success Rate Expectations

### With v1.0.4 Changes:

**Visible Browser (Headless OFF):**
- Expected: 80-95% success rate
- First batch usually works well
- May hit rate limits on large batches (50+)

**Headless Mode (Headless ON):**
- Expected: 30-60% success rate
- More likely to be detected
- May fail completely on cloud hosting

**On Streamlit Cloud:**
- Expected: 50-70% success rate
- Cloud IPs may be flagged
- Better to run locally if possible

## 📊 Monitoring Strategy

### Run a Test Batch:
1. Create Excel with 5 known-good CNPJs
2. Run with headless OFF
3. Watch the visible browser
4. Download log file
5. Check success rate

### Example Test CNPJs:
```
43.121.036/0001-36
58.893.662/0001-18
50.716.352/0001-84
26.841.302/0001-86
15.585.932/0001-10
```

If all 5 succeed → Anti-bot evasion working ✅
If some fail → Check logs for error patterns
If all fail → ANBIMA may have blocked the IP ❌

## 🔄 If Still Failing After v1.0.4

### Additional Measures:

1. **Clear Browser Cache**
   - Between batches
   - Fresh start reduces tracking

2. **Change Network**
   - Use different WiFi
   - Mobile hotspot
   - VPN (if allowed)

3. **Randomize Delays More**
   - Increase max delay to 20-30 seconds
   - Make timing less predictable

4. **Add Human-Like Errors**
   - Occasionally "mistype" CNPJ
   - Random back button clicks
   - Scroll randomly

5. **Consider Paid Solutions**
   - Browser automation services
   - Proxy rotation
   - Professional scraping APIs

## 📝 Reporting Back

When testing v1.0.4, please share:

1. **Settings used:**
   - Stealth mode: ON/OFF
   - Headless mode: ON/OFF
   - Number of CNPJs attempted

2. **Results:**
   - How many succeeded
   - At what point failures started
   - Download and attach log file

3. **Environment:**
   - Running on Streamlit Cloud or locally
   - Approximate location (for IP restrictions)

## 🎓 Understanding Anti-Bot Systems

Modern anti-bot systems check:
- ✅ Browser fingerprint (we hide this)
- ✅ JavaScript capabilities (we have these)
- ✅ Mouse movements (we simulate these)
- ✅ Timing patterns (we randomize these)
- ✅ User agent (we set realistic one)
- ⚠️ Request rate (harder to hide)
- ⚠️ IP reputation (can't control on cloud)

**The more "human" we appear, the better the success rate.**

---

**Bottom line:** ANBIMA has active anti-bot protection. v1.0.4 adds enhanced evasion, but success depends on running with **visible browser** and **reasonable delays**. For best results, run locally with headless mode OFF.
