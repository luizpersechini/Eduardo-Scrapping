# Security Policy

## 🔒 Security Overview

This document outlines security measures and best practices for the ANBIMA Fund Data Scraper.

---

## ⚠️ IMMEDIATE ACTION REQUIRED

### 1. Change Default Password

The application ships with a default password that **MUST** be changed immediately:

**Current:** `password` (username: `eduardo`)

**How to change:** See `LOGIN_SETUP.md` for detailed instructions.

---

## 🛡️ Security Features

### Authentication
- ✅ SHA-256 hashed passwords (not stored in plain text)
- ✅ Session-based authentication
- ✅ Login required for all scraping operations
- ✅ Logout functionality

### Data Protection
- ✅ No PII (Personally Identifiable Information) collected
- ✅ Only CNPJ (public business identifiers) processed
- ✅ Data stored only in browser session (not persisted)
- ✅ Results downloadable by user only

### API Security
- ✅ API keys removed from code
- ✅ Environment variable-based configuration
- ✅ Parse.bot integration disabled by default

---

## 🔐 Secrets Management

### Streamlit Cloud Deployment

1. **Never commit secrets to Git**
2. **Use Streamlit Cloud Secrets:**
   - Go to: App Settings > Secrets
   - Add secrets in TOML format:
   ```toml
   # Only needed if you enable Parse.bot
   PARSE_BOT_API_KEY = "your_actual_key_here"
   PARSE_BOT_SCRAPER_ID = "your_actual_id_here"
   ```

### Local Development

1. **Copy `.env.example` to `.env`**
2. **Fill in actual values** (never commit .env!)
3. **Load environment variables** before running

---

## 📊 Data Privacy

### What Data is Collected?
- **CNPJs:** Business tax IDs (public information)
- **Fund data:** Publicly available from ANBIMA website
- **Session data:** Stored only in browser session (temporary)

### What Data is NOT Collected?
- ❌ Personal information
- ❌ Email addresses
- ❌ Payment information
- ❌ User tracking/analytics
- ❌ IP addresses (beyond Streamlit Cloud defaults)

### Data Retention
- **Browser session only** - data cleared on logout or session end
- **No database** - no long-term storage
- **User downloads** - Excel files generated on-demand only

---

## 🚨 Known Risks & Mitigations

### 1. Weak Default Password
**Risk:** Unauthorized access if not changed
**Mitigation:** Mandatory password change instructions
**Status:** User action required

### 2. Session Hijacking
**Risk:** Session token theft
**Mitigation:** HTTPS enforced on Streamlit Cloud, session timeout
**Status:** Mitigated

### 3. Rate Limiting Bypass
**Risk:** ANBIMA anti-spam detection
**Mitigation:** Built-in delays, stealth mode, conservative settings
**Status:** Mitigated

---

## 🔧 Security Best Practices

### For Administrators

1. **Change default password immediately**
2. **Use strong passwords** (12+ characters, mixed case, numbers, symbols)
3. **Don't share credentials**
4. **Monitor access logs** (Streamlit Cloud provides basic analytics)
5. **Review deployed code** periodically

### For Developers

1. **Never commit secrets** to version control
2. **Use `.env` files** for local secrets (already in .gitignore)
3. **Review dependencies** for vulnerabilities
4. **Keep packages updated**
5. **Follow principle of least privilege**

---

## 🐛 Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** open a public GitHub issue
2. **Email:** [Your contact email]
3. **Provide:** Description, steps to reproduce, impact assessment
4. **Allow:** 90 days for patching before public disclosure

---

## ✅ Security Checklist

Before deployment:
- [ ] Changed default password
- [ ] Reviewed all code for hardcoded secrets
- [ ] Configured Streamlit Cloud secrets (if needed)
- [ ] Tested authentication
- [ ] Verified HTTPS enabled
- [ ] Reviewed .gitignore
- [ ] Confirmed no sensitive data in repository

---

## 📜 Compliance

### LGPD/GDPR Compliance
- **Public data only:** CNPJs are public business identifiers
- **No personal data:** No names, emails, or personal information collected
- **Data minimization:** Only scraping what's requested
- **User control:** User initiates all scraping, downloads own data

### Web Scraping Ethics
- ✅ Respects robots.txt
- ✅ Rate limiting and delays
- ✅ Stealth mode to avoid detection
- ✅ Public data only
- ✅ No credential stuffing or unauthorized access

---

## 🔄 Updates

This security policy is reviewed and updated regularly. Last update: 2026-01-27

---

**Questions?** See `LOGIN_SETUP.md` for password management or contact the repository owner.
