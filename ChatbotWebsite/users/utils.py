from flask import url_for, current_app
from flask_mail import Message
import secrets
import os
from PIL import Image
from ChatbotWebsite import mail


# function to save the user profile picture
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(
        current_app.root_path, "static/profile_images", picture_fn
    )
    output_size = (190, 190)
    image = Image.open(form_picture).convert("RGB")
    image.thumbnail(output_size)
    image.save(picture_path)

    return picture_fn


# function to send the reset password email
def send_reset_email(user):
    if user is None:
        raise ValueError("Cannot send reset email: user is None")
    
    token = user.get_reset_token()
    reset_url = url_for('users.reset_token', token=token, _external=True)
    
    # Check if we should use console mode (for development)
    use_console = current_app.config.get('MAIL_USE_CONSOLE', False)
    
    if use_console:
        # Print to console for development
        print("\n" + "="*70)
        print("PASSWORD RESET LINK (Development Mode - Email not sent)")
        print("="*70)
        print(f"User: {user.username} ({user.email})")
        print(f"Reset Link: {reset_url}")
        print("="*70 + "\n")
        # Return the URL so it can be displayed on the page
        return reset_url
    
    # Try to send actual email
    try:
        msg = Message(
            "Password Reset Request", 
            sender=current_app.config.get('MAIL_USERNAME', 'noreply@chatbot.com'), 
            recipients=[user.email]
        )
        msg.body = f"""To reset your password, visit the following link:
{reset_url}
Please do not reply to this email and share this email with anyone.
    
If you did not make this request then simply ignore this email and no changes will be made.
"""
        mail.send(msg)
        return None  # Email sent successfully, no URL to display
    except Exception as e:
        # If email sending fails, fall back to console mode
        current_app.logger.warning(f"Failed to send email, using console mode: {e}")
        print("\n" + "="*70)
        print("PASSWORD RESET LINK (Email sending failed - using console)")
        print("="*70)
        print(f"User: {user.username} ({user.email})")
        print(f"Reset Link: {reset_url}")
        print("="*70 + "\n")
        # Return the URL so it can be displayed on the page as fallback
        return reset_url
