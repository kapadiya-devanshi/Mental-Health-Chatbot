from flask import (
    current_app,
    Blueprint,
    render_template,
    request,
    jsonify,
    url_for,
    flash,
    redirect,
    send_file,
)
from flask_login import login_user, current_user, logout_user, login_required

from ChatbotWebsite import db, bcrypt
from ChatbotWebsite.models import User, ChatMessage, Journal
from ChatbotWebsite.users.forms import (
    RegistrationForm,
    LoginForm,
    UpdateAccountForm,
    RequestResetForm,
    ResetPasswordForm,
)
from ChatbotWebsite.users.utils import (
    save_picture,
    send_reset_email,
    analyze_user_activity,
)
import os
from io import BytesIO
from datetime import datetime

users = Blueprint("users", __name__)


# register page/route
@users.route("/register", methods=["GET", "POST"])
def register():
    if (
        current_user.is_authenticated
    ):  # if user is already logged in, redirect to home page
        return redirect(url_for("main.home"))
    form = RegistrationForm()  # create registration form
    if (
        form.validate_on_submit()
    ):  # if form is submitted, create new user and add to database
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        new_user = User(
            username=form.username.data, email=form.email.data, password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Your account has been created! You are now able to log in.", "success")
        return redirect(url_for("users.login"))
    return render_template("register.html", title="Register", form=form)


# login page/route
@users.route("/login", methods=["GET", "POST"])
def login():
    if (
        current_user.is_authenticated
    ):  # if user is already logged in, redirect to home page
        return redirect(url_for("main.home"))
    form = LoginForm()  # create login form
    if (
        form.validate_on_submit()
    ):  # if form is submitted, check if user exists and password is correct
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash("You have been logged in!", "success")
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("main.home"))
        else:
            flash("Login Unsuccessful. Please check email and password!", "danger")
    return render_template("login.html", title="Login", form=form)


# account page/route
@users.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = UpdateAccountForm()  # form to update account
    if form.validate_on_submit():
        if form.picture.data:
            old_picture = current_user.profile_image
            picture_file = save_picture(form.picture.data)
            current_user.profile_image = picture_file
            if old_picture != "download.jpg":
                os.remove(
                    os.path.join(
                        current_app.root_path, "static/profile_images", old_picture
                    )
                )
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your account has been updated!", "success")
        return redirect(url_for("users.account"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template("account.html", title="Account", form=form)


@users.route("/account/analyze", methods=["GET"])
@login_required
def analyze_account():
    """Analyze current user's activity and render an HTML report."""
    # Limit the amount of data we scan to keep things responsive.
    messages = (
        ChatMessage.query.filter_by(user_id=current_user.id)
        .order_by(ChatMessage.timestamp.desc())
        .limit(500)
        .all()
    )
    journals = (
        Journal.query.filter_by(user_id=current_user.id)
        .order_by(Journal.timestamp.desc())
        .limit(200)
        .all()
    )

    voice_note = request.args.get("voice_note", "", type=str)

    try:
        report = analyze_user_activity(current_user, messages, journals, voice_note)
    except Exception as e:
        current_app.logger.error(f"Error during user activity analysis: {e}")
        flash(
            "Sorry, something went wrong while analyzing your activity. Please try again later.",
            "danger",
        )
        return redirect(url_for("users.account"))

    return render_template(
        "analysis_report.html",
        title="My Mood & Activity Report",
        report=report,
        is_admin_view=False,
    )


@users.route("/account/analyze/pdf", methods=["GET"])
@login_required
def analyze_account_pdf():
    """Generate a PDF report of the current user's activity analysis."""
    messages = (
        ChatMessage.query.filter_by(user_id=current_user.id)
        .order_by(ChatMessage.timestamp.desc())
        .limit(500)
        .all()
    )
    journals = (
        Journal.query.filter_by(user_id=current_user.id)
        .order_by(Journal.timestamp.desc())
        .limit(200)
        .all()
    )

    voice_note = request.args.get("voice_note", "", type=str)

    try:
        report = analyze_user_activity(current_user, messages, journals, voice_note)
    except Exception as e:
        current_app.logger.error(f"Error during user activity analysis (PDF): {e}")
        flash(
            "Sorry, something went wrong while analyzing your activity. Please try again later.",
            "danger",
        )
        return redirect(url_for("users.account"))

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        current_app.logger.error("reportlab is not installed; cannot generate PDF.")
        flash(
            "PDF generation is not configured on this server. Please contact the administrator.",
            "warning",
        )
        return redirect(url_for("users.analyze_account"))

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "Mood & Activity Report")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(
        40,
        y,
        f"User: {report.get('username', '')}  |  Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
    )
    y -= 30

    def write_line(text: str):
        nonlocal y
        if y < 60:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)
        c.drawString(40, y, text[:120])
        y -= 14

    write_line(f"Mental state summary: {report.get('mental_state_summary', '')}")
    write_line(f"Estimated risk level: {report.get('risk_level', 'unknown').title()}")
    write_line(
        f"Messages analyzed: {report.get('message_count', 0)}, Journals analyzed: {report.get('journal_count', 0)}"
    )
    write_line("")

    sentiment = report.get("sentiment", {})
    write_line("Sentiment indicators (approximate):")
    write_line(f"  Positive: {sentiment.get('positive_score', 0.0):.3f}")
    write_line(f"  Negative: {sentiment.get('negative_score', 0.0):.3f}")
    write_line(f"  Neutral:  {sentiment.get('neutral_score', 0.0):.3f}")
    write_line("")

    mood_counts = report.get("journal_mood_counts", {}) or {}
    if mood_counts:
        write_line("Journal moods:")
        for mood, count in sorted(mood_counts.items(), key=lambda kv: kv[1], reverse=True):
            write_line(f"  {mood}: {count}")
        write_line("")

    suggestions = report.get("suggestions", []) or []
    if suggestions:
        write_line("Supportive suggestions:")
        for idx, s in enumerate(suggestions, start=1):
            write_line(f"  {idx}. {s}")

    c.showPage()
    c.save()
    buffer.seek(0)

    filename = f"mood_report_user_{current_user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf",
    )

# history route to display user chat history
@users.route("/history")
@login_required
def history():
    messages = ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.timestamp.asc()).all()
    return render_template("history.html", title="History", messages=messages)

# logout route
@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.home"))


# delete conversation route
@users.route("/delete_conversation", methods=["POST"])
def delete_conversation():
    if current_user.is_authenticated:
        messages = ChatMessage.query.filter_by(user_id=current_user.id).all()
        for message in messages:
            db.session.delete(message)
        db.session.commit()
        flash("Your conversation has been deleted!", "success")
    return redirect(url_for("users.account"))


# delete account route
@users.route("/delete_account", methods=["POST"])
def delete_account():
    if current_user.is_authenticated:
        messages = ChatMessage.query.filter_by(user_id=current_user.id).all()
        for message in messages:
            db.session.delete(message)
        journals = Journal.query.filter_by(user_id=current_user.id).all()
        for journal in journals:
            db.session.delete(journal)
        db.session.delete(current_user)
        db.session.commit()
        flash("Your account has been deleted!", "success")
    return redirect(url_for("users.logout"))


# reset password route to request a password reset token
@users.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    if (
        current_user.is_authenticated
    ):  # if user is already logged in, redirect to home page
        return redirect(url_for("main.home"))
    form = RequestResetForm()  # create request reset form
    if form.validate_on_submit():  # if form is submitted, send email with reset token
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            try:
                reset_url = send_reset_email(user)
                # Check if using console mode (reset_url will be returned in console mode)
                use_console = current_app.config.get('MAIL_USE_CONSOLE', False)
                if use_console and reset_url:
                    # Store the reset URL in session to display on the page
                    from flask import session
                    session['reset_link'] = reset_url
                    session['reset_email'] = user.email
                    flash(
                        "Password reset link has been generated below.", "info"
                    )
                    return render_template("reset_request.html", title="Reset Password", form=form, reset_link=reset_url, user_email=user.email)
                else:
                    flash(
                        "An email has been sent with instructions to reset your password.", "info"
                    )
            except Exception as e:
                # Log the error for debugging
                current_app.logger.error(f"Error sending reset email: {e}")
                # If we get here, something went wrong - try to generate link as fallback
                use_console = current_app.config.get('MAIL_USE_CONSOLE', False)
                if use_console:
                    try:
                        # Generate token and URL as fallback
                        token = user.get_reset_token()
                        reset_url = url_for('users.reset_token', token=token, _external=True)
                        flash(
                            "Password reset link has been generated below.", "info"
                        )
                        return render_template("reset_request.html", title="Reset Password", form=form, reset_link=reset_url, user_email=user.email)
                    except Exception as e2:
                        current_app.logger.error(f"Error generating fallback reset link: {e2}")
                        flash(
                            "An error occurred. Please check the console/terminal for the reset link or try again.", "warning"
                        )
                else:
                    flash(
                        "An error occurred while sending the email. Please check your email configuration or contact support.", "warning"
                    )
        else:
            # For security, show the same message even if user doesn't exist
            flash(
                "If an account with that email exists, an email has been sent with instructions to reset your password.", "info"
            )
        return redirect(url_for("users.login"))
    return render_template("reset_request.html", title="Reset Password", form=form)


# reset password route to reset password
@users.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    if (
        current_user.is_authenticated
    ):  # if user is already logged in, redirect to home page
        return redirect(url_for("main.home"))
    
    try:
        user = User.verify_reset_token(token)
    except Exception as e:
        current_app.logger.error(f"Error verifying reset token: {e}")
        flash("That is an invalid or expired token", "warning")
        return redirect(url_for("users.reset_request"))
    
    if user is None:
        flash("That is an invalid or expired token", "warning")
        return redirect(url_for("users.reset_request"))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        try:
            if bcrypt.check_password_hash(user.password, form.password.data):
                flash(
                    "Your new password must be unique and different from your old password.",
                    "warning",
                )
                return redirect(url_for("users.reset_token", token=token, _external=True))
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
                "utf-8"
            )
            user.password = hashed_password
            db.session.commit()
            flash("Your password has been updated!", "success")
            return redirect(url_for("users.login"))
        except Exception as e:
            current_app.logger.error(f"Error updating password: {e}")
            db.session.rollback()
            flash("An error occurred while updating your password. Please try again.", "danger")
    
    return render_template("reset_token.html", title="Reset Password", form=form)
