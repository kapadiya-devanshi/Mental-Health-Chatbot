from functools import wraps

from flask import Blueprint, abort, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required

from ChatbotWebsite import db
from ChatbotWebsite.models import User, ChatMessage, Journal

admin = Blueprint("admin", __name__, url_prefix="/admin")


def _log_admin_check(allowed: bool):
    # #region agent log
    try:
        import os, json, time  # type: ignore
        log_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".cursor", "debug.log"
        )
        payload = {
            "sessionId": "debug-session",
            "runId": "admin-403-pre-fix",
            "hypothesisId": "H2",
            "location": "admin.admin_required",
            "message": "Admin access check",
            "data": {
                "user_id": getattr(current_user, "id", None),
                "user_email": getattr(current_user, "email", None),
                "is_admin_attr": getattr(current_user, "is_admin", None),
                "is_authenticated": getattr(current_user, "is_authenticated", False),
                "allowed": allowed,
            },
            "timestamp": int(time.time() * 1000),
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass
    # #endregion agent log


def admin_required(func):
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        is_admin_flag = getattr(current_user, "is_admin", False)
        if not is_admin_flag or is_admin_flag is None:
            _log_admin_check(False)
            abort(403)
        _log_admin_check(True)
        return func(*args, **kwargs)

    return wrapper


@admin.route("/dashboard")
@admin_required
def dashboard():
    users = User.query.all()

    # Aggregate simple activity info for each user without heavy queries.
    user_activity = []
    for user in users:
        message_count = ChatMessage.query.filter_by(user_id=user.id).count()
        journal_count = Journal.query.filter_by(user_id=user.id).count()
        last_message = (
            ChatMessage.query.filter_by(user_id=user.id)
            .order_by(ChatMessage.timestamp.desc())
            .first()
        )
        last_journal = (
            Journal.query.filter_by(user_id=user.id)
            .order_by(Journal.timestamp.desc())
            .first()
        )
        last_activity = None
        if last_message and last_journal:
            last_activity = max(last_message.timestamp, last_journal.timestamp)
        elif last_message:
            last_activity = last_message.timestamp
        elif last_journal:
            last_activity = last_journal.timestamp

        user_activity.append(
            {
                "user": user,
                "message_count": message_count,
                "journal_count": journal_count,
                "last_activity": last_activity,
            }
        )

    return render_template(
        "admin/dashboard.html",
        title="Admin Dashboard",
        user_activity=user_activity,
    )


@admin.route("/user/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        flash("You cannot delete your own account!", "danger")
        return redirect(url_for("admin.dashboard"))
    
    # Delete all user messages
    ChatMessage.query.filter_by(user_id=user.id).delete()
    # Delete all user journals
    Journal.query.filter_by(user_id=user.id).delete()
    # Delete the user
    db.session.delete(user)
    db.session.commit()
    
    flash(f"User {user.username} has been deleted successfully!", "success")
    return redirect(url_for("admin.dashboard"))


@admin.route("/user/<int:user_id>/toggle_admin", methods=["POST"])
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from removing their own admin status
    if user.id == current_user.id:
        flash("You cannot remove your own admin privileges!", "danger")
        return redirect(url_for("admin.dashboard"))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = "granted" if user.is_admin else "revoked"
    flash(f"Admin privileges {status} for {user.username}!", "success")
    return redirect(url_for("admin.dashboard"))


@admin.route("/user/<int:user_id>/details")
@admin_required
def user_details(user_id):
    user = User.query.get_or_404(user_id)
    messages = ChatMessage.query.filter_by(user_id=user.id).order_by(ChatMessage.timestamp.desc()).limit(50).all()
    journals = Journal.query.filter_by(user_id=user.id).order_by(Journal.timestamp.desc()).limit(50).all()
    
    return render_template(
        "admin/user_details.html",
        title=f"User Details - {user.username}",
        user=user,
        messages=messages,
        journals=journals,
    )


@admin.route("/user/<int:user_id>/delete_messages", methods=["POST"])
@admin_required
def delete_user_messages(user_id):
    user = User.query.get_or_404(user_id)
    ChatMessage.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    flash(f"All messages for {user.username} have been deleted!", "success")
    return redirect(url_for("admin.user_details", user_id=user_id))


@admin.route("/user/<int:user_id>/delete_journals", methods=["POST"])
@admin_required
def delete_user_journals(user_id):
    user = User.query.get_or_404(user_id)
    Journal.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    flash(f"All journals for {user.username} have been deleted!", "success")
    return redirect(url_for("admin.user_details", user_id=user_id))


