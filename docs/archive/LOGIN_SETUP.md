# Login Setup Instructions

## Current Login Credentials

**Username:** `eduardo`
**Password:** `password` ⚠️ **CHANGE THIS IMMEDIATELY!**

---

## How to Change the Password

### Option 1: Using Python (Recommended)

1. Open a terminal/command prompt
2. Run this Python command to generate a new password hash:

```python
python3 -c "import hashlib; print('Your password hash:', hashlib.sha256('YOUR_NEW_PASSWORD_HERE'.encode()).hexdigest())"
```

**Example:**
```bash
python3 -c "import hashlib; print('Your password hash:', hashlib.sha256('MySecurePass123'.encode()).hexdigest())"
```

3. Copy the hash that appears (it's a long string of letters and numbers)
4. Open `streamlit_app.py`
5. Find line 27 that says:
   ```python
   PASSWORD_HASH = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
   ```
6. Replace the hash with your new hash:
   ```python
   PASSWORD_HASH = "your_new_hash_here"
   ```
7. Save the file
8. Commit and push to GitHub:
   ```bash
   git add streamlit_app.py
   git commit -m "chore: Update password"
   git push
   ```

Streamlit Cloud will automatically redeploy with the new password.

---

### Option 2: Using Online Tool

1. Go to: https://emn178.github.io/online-tools/sha256.html
2. Enter your new password
3. Click "Hash"
4. Copy the resulting hash
5. Follow steps 4-8 from Option 1 above

---

## Changing the Username

To change the username from "eduardo" to something else:

1. Open `streamlit_app.py`
2. Find line 26:
   ```python
   USERNAME = "eduardo"
   ```
3. Change to your desired username:
   ```python
   USERNAME = "your_new_username"
   ```
4. Save, commit, and push

---

## Security Notes

- ✅ Passwords are hashed using SHA-256 (not stored in plain text)
- ✅ Session-based authentication (stays logged in until you logout)
- ⚠️ Change the default password immediately
- ⚠️ Use a strong password (mix of letters, numbers, symbols)
- ⚠️ Don't share your password with others

---

## Testing the New Password

1. Visit your Streamlit app URL
2. Enter username and new password
3. Click "Login"
4. If it doesn't work, double-check the hash in `streamlit_app.py`

---

**Need help?** Contact your developer or check the GitHub repository.
