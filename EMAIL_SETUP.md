# Email Configuration Guide

## Current Setup (Development Mode)

By default, the application is configured to **print password reset links to the console** instead of sending emails. This is perfect for development and testing.

### How it works:
1. When a user requests a password reset, the reset link will be printed to your terminal/console
2. Copy the link from the console and use it to reset the password
3. No email configuration needed for development!

### Example Console Output:
```
======================================================================
PASSWORD RESET LINK (Development Mode - Email not sent)
======================================================================
User: John Doe (john@example.com)
Reset Link: http://localhost:5000/reset_password/eyJ0eXAiOiJKV1QiLCJhbGc...
======================================================================
```

## Setting Up Email for Production

If you want to send actual emails (for production), you need to:

### 1. Configure Gmail App Password

Gmail requires an **App Password** (not your regular password) for SMTP:

1. Go to your Google Account: https://myaccount.google.com/
2. Enable 2-Step Verification (required for App Passwords)
3. Go to Security → App Passwords
4. Generate a new App Password for "Mail"
5. Copy the 16-character password

### 2. Update Configuration

Edit `ChatbotWebsite/config.py` or set environment variables:

**Option A: Edit config.py directly**
```python
MAIL_USERNAME = "your-email@gmail.com"
MAIL_PASSWORD = "your-16-char-app-password"  # The App Password from Google
MAIL_USE_CONSOLE = False  # Set to False to send actual emails
```

**Option B: Use Environment Variables (Recommended)**
```bash
# Windows PowerShell
$env:MAIL_USERNAME="your-email@gmail.com"
$env:MAIL_PASSWORD="your-16-char-app-password"
$env:MAIL_USE_CONSOLE="False"

# Linux/Mac
export MAIL_USERNAME="your-email@gmail.com"
export MAIL_PASSWORD="your-16-char-app-password"
export MAIL_USE_CONSOLE="False"
```

### 3. Alternative Email Providers

If you don't want to use Gmail, you can configure other SMTP servers:

**For Outlook/Hotmail:**
```python
MAIL_SERVER = "smtp-mail.outlook.com"
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
```

**For Yahoo:**
```python
MAIL_SERVER = "smtp.mail.yahoo.com"
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
```

**For Custom SMTP:**
```python
MAIL_SERVER = "smtp.yourdomain.com"
MAIL_PORT = 587  # or 465 for SSL
MAIL_USE_TLS = True  # Use True for port 587
MAIL_USE_SSL = False  # Use True for port 465
```

## Troubleshooting

### Error: "An error occurred while sending the email"
- **Solution**: The app will automatically fall back to console mode and print the reset link
- Check your console/terminal for the reset link
- For production, verify your email credentials are correct

### Error: "Authentication failed"
- Make sure you're using an **App Password**, not your regular Gmail password
- Verify 2-Step Verification is enabled on your Google account
- Check that the App Password is correct (16 characters, no spaces)

### Error: "Connection refused"
- Check your firewall settings
- Verify the SMTP server and port are correct
- Some networks block SMTP ports (587, 465)

## Quick Test

To test if email is working:

1. Set `MAIL_USE_CONSOLE = False` in config.py
2. Request a password reset
3. Check if you receive the email
4. If not, check the console for the reset link (fallback mode)

## Security Notes

- **Never commit** your email password to version control
- Use environment variables for sensitive credentials
- App Passwords are safer than regular passwords
- Consider using a dedicated email account for your application

