from functools import wraps

from flask import Blueprint, abort, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required

from ChatbotWebsite import db
from ChatbotWebsite.models import User, ChatMessage, Journal, Feedback, PremiumSubscription
from ChatbotWebsite.users.utils import analyze_user_activity
from io import BytesIO
from datetime import datetime
from sqlalchemy import extract
from flask import send_file

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


@admin.route("/user/<int:user_id>/analyze", methods=["GET"])
@admin_required
def analyze_user(user_id: int):
    """Admin view of a user's mood & activity analysis."""
    user = User.query.get_or_404(user_id)
    messages = (
        ChatMessage.query.filter_by(user_id=user.id)
        .order_by(ChatMessage.timestamp.desc())
        .limit(500)
        .all()
    )
    journals = (
        Journal.query.filter_by(user_id=user.id)
        .order_by(Journal.timestamp.desc())
        .limit(200)
        .all()
    )

    try:
        report = analyze_user_activity(user, messages, journals, None)
    except Exception as e:
        flash(
            "Failed to analyze this user's activity. Please try again later.",
            "danger",
        )
        current_app = admin.import_name  # type: ignore[assignment]
        return redirect(url_for("admin.user_details", user_id=user_id))

    return render_template(
        "analysis_report.html",
        title=f"Mood & Activity Report - {user.username}",
        report=report,
        is_admin_view=True,
    )


@admin.route("/user/<int:user_id>/analyze/pdf", methods=["GET"])
@admin_required
def analyze_user_pdf(user_id: int):
    """Admin PDF download of a user's mood & activity analysis."""
    user = User.query.get_or_404(user_id)
    messages = (
        ChatMessage.query.filter_by(user_id=user.id)
        .order_by(ChatMessage.timestamp.desc())
        .limit(500)
        .all()
    )
    journals = (
        Journal.query.filter_by(user_id=user.id)
        .order_by(Journal.timestamp.desc())
        .limit(200)
        .all()
    )

    try:
        report = analyze_user_activity(user, messages, journals, None)
    except Exception as e:
        flash(
            "Failed to analyze this user's activity. Please try again later.",
            "danger",
        )
        return redirect(url_for("admin.user_details", user_id=user_id))

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        flash(
            "PDF generation is not configured on this server. Please contact the administrator.",
            "warning",
        )
        return redirect(url_for("admin.analyze_user", user_id=user_id))

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "Mood & Activity Report (Admin View)")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(
        40,
        y,
        f"User: {report.get('username', '')} (ID: {report.get('user_id', '')})  |  Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
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

    write_line(f"  Positive: {sentiment.get('positive_score', 0.0) * 100:.2f}%")
    write_line(f"  Negative: {sentiment.get('negative_score', 0.0) * 100:.2f}%")
    write_line(f"  Neutral:  {sentiment.get('neutral_score', 0.0) * 100:.2f}%")
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

    filename = f"mood_report_user_{user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf",
    )


@admin.route("/feedbacks")
@admin_required
def feedbacks():
    pending_feedbacks = Feedback.query.filter_by(is_approved=False).order_by(Feedback.timestamp.desc()).all()
    approved_feedbacks = Feedback.query.filter_by(is_approved=True).order_by(Feedback.timestamp.desc()).all()
    return render_template(
        "admin/feedbacks.html",
        title="Feedback Management",
        pending_feedbacks=pending_feedbacks,
        approved_feedbacks=approved_feedbacks,
    )


@admin.route("/feedback/<int:feedback_id>/approve", methods=["POST"])
@admin_required
def approve_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    feedback.is_approved = True
    db.session.commit()
    flash(f"Feedback from {feedback.user.username if feedback.user else 'Anonymous'} has been approved!", "success")
    return redirect(url_for("admin.feedbacks"))


@admin.route("/feedback/<int:feedback_id>/publish", methods=["POST"])
@admin_required
def publish_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    if not feedback.is_approved:
        flash("Feedback must be approved before publishing!", "warning")
        return redirect(url_for("admin.feedbacks"))
    feedback.is_published = True
    db.session.commit()
    flash(f"Feedback from {feedback.user.username if feedback.user else 'Anonymous'} has been published!", "success")
    return redirect(url_for("admin.feedbacks"))


@admin.route("/feedback/<int:feedback_id>/unpublish", methods=["POST"])
@admin_required
def unpublish_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    feedback.is_published = False
    db.session.commit()
    flash(f"Feedback from {feedback.user.username if feedback.user else 'Anonymous'} has been unpublished!", "success")
    return redirect(url_for("admin.feedbacks"))


@admin.route("/feedback/<int:feedback_id>/reject", methods=["POST"])
@admin_required
def reject_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    db.session.delete(feedback)
    db.session.commit()
    flash("Feedback has been rejected and deleted!", "success")
    return redirect(url_for("admin.feedbacks"))


@admin.route("/premium-subscribers")
@admin_required
def premium_subscribers():
    """View all premium subscribers."""
    # Get all active subscriptions with user info
    active_subscriptions = PremiumSubscription.query.filter_by(
        is_active=True
    ).order_by(PremiumSubscription.start_date.desc()).all()
    
    # Get expired/cancelled subscriptions
    inactive_subscriptions = PremiumSubscription.query.filter_by(
        is_active=False
    ).order_by(PremiumSubscription.end_date.desc()).limit(50).all()
    
    # Calculate statistics
    total_revenue = db.session.query(db.func.sum(PremiumSubscription.amount_paid)).filter(
        PremiumSubscription.is_active == True
    ).scalar() or 0
    
    plus_count = PremiumSubscription.query.filter_by(
        plan_type='plus', is_active=True
    ).count()
    
    pro_count = PremiumSubscription.query.filter_by(
        plan_type='pro', is_active=True
    ).count()
    
    # Monthly revenue (subscriptions started this month)
    current_month = datetime.now().month
    current_year = datetime.now().year
    monthly_revenue = db.session.query(db.func.sum(PremiumSubscription.amount_paid)).filter(
        extract('month', PremiumSubscription.start_date) == current_month,
        extract('year', PremiumSubscription.start_date) == current_year
    ).scalar() or 0
    
    return render_template(
        "admin/premium_subscribers.html",
        title="Premium Subscribers",
        active_subscriptions=active_subscriptions,
        inactive_subscriptions=inactive_subscriptions,
        total_revenue=total_revenue,
        monthly_revenue=monthly_revenue,
        plus_count=plus_count,
        pro_count=pro_count,
        total_subscribers=plus_count + pro_count,
        datetime=datetime
    )


@admin.route("/subscription/<int:sub_id>/cancel", methods=["POST"])
@admin_required
def admin_cancel_subscription(sub_id):
    """Admin can cancel a user's subscription."""
    subscription = PremiumSubscription.query.get_or_404(sub_id)
    subscription.is_active = False
    db.session.commit()
    flash(f"Subscription for {subscription.user.username} has been cancelled!", "success")
    return redirect(url_for("admin.premium_subscribers"))


# AI Learning Dashboard
@admin.route("/learning")
@admin_required
def learning_dashboard():
    """AI Learning Dashboard - View and manage self-learning system"""
    try:
        from ChatbotWebsite.chatbot.self_learning import learning_engine
        from ChatbotWebsite.chatbot.train_model import ChatbotTrainer
        import json
        import os
        
        # Get intents analysis
        stats = learning_engine.analyze_intents()
        
        # Get learning stats
        learning_stats = learning_engine.get_learning_report().get("learning_stats", {})
        
        # Get suggestions
        suggestions = learning_engine.learning_data.get("pending_suggestions", [])
        
        # Load training info
        training_info = {}
        try:
            info_file = os.path.join(os.path.dirname(__file__), "..", "static", "data", "training_info.json")
            with open(info_file, 'r') as f:
                training_info = json.load(f)
        except FileNotFoundError:
            pass
        
        return render_template(
            "admin/learning_dashboard.html",
            title="AI Learning Dashboard",
            stats=stats,
            learning_stats=learning_stats,
            suggestions=suggestions,
            training_info=training_info
        )
    except Exception as e:
        flash(f"Error loading learning dashboard: {str(e)}", "danger")
        return redirect(url_for("admin.dashboard"))


@admin.route("/learning/analyze", methods=["POST"])
@admin_required
def analyze_learning():
    """Run learning analysis on user chats"""
    try:
        from ChatbotWebsite.chatbot.self_learning import analyze_and_learn
        
        # Run analysis
        report = analyze_and_learn(auto_update=False)
        
        flash(f"Learning analysis complete! Found {len(report.get('latest_updates', {}).get('suggestions', []))} suggestions.", "success")
        return redirect(url_for("admin.learning_dashboard"))
    except Exception as e:
        flash(f"Error running learning analysis: {str(e)}", "danger")
        return redirect(url_for("admin.learning_dashboard"))


@admin.route("/learning/train", methods=["POST"])
@admin_required
def train_model():
    """Train the chatbot model"""
    try:
        from ChatbotWebsite.chatbot.train_model import train_model, quick_train
        import threading
        
        mode = request.form.get("mode", "quick")
        
        # Run training in background
        def run_training():
            try:
                if mode == "quick":
                    quick_train()
                elif mode == "full":
                    train_model(epochs=200)
                elif mode == "auto":
                    train_model(epochs=150, auto=True)
            except Exception as e:
                print(f"Training error: {e}")
        
        # Start training thread
        training_thread = threading.Thread(target=run_training)
        training_thread.daemon = True
        training_thread.start()
        
        flash(f"Model training started in {mode} mode! This may take a few minutes.", "success")
        return redirect(url_for("admin.learning_dashboard"))
    except Exception as e:
        flash(f"Error starting model training: {str(e)}", "danger")
        return redirect(url_for("admin.learning_dashboard"))


@admin.route("/learning/approve", methods=["POST"])
@admin_required
def approve_suggestion():
    """Approve or reject a learning suggestion"""
    try:
        from ChatbotWebsite.chatbot.self_learning import add_pattern_with_approval, add_response_with_approval
        
        suggestion_index = int(request.form.get("suggestion_index", 0))
        action = request.form.get("action", "reject")
        
        # Get suggestion from learning data
        from ChatbotWebsite.chatbot.self_learning import learning_engine
        suggestions = learning_engine.learning_data.get("pending_suggestions", [])
        
        if suggestion_index < len(suggestions):
            suggestion = suggestions[suggestion_index]
            
            if action == "approve":
                if suggestion.get("type") == "add_pattern":
                    add_pattern_with_approval(suggestion["intent"], suggestion["pattern"])
                    flash(f"Pattern added to {suggestion['intent']} intent!", "success")
                elif suggestion.get("type") == "add_response":
                    add_response_with_approval(suggestion["intent"], suggestion["response"])
                    flash(f"Response added to {suggestion['intent']} intent!", "success")
            else:
                flash("Suggestion rejected.", "info")
            
            # Remove from pending
            suggestions.pop(suggestion_index)
            learning_engine._save_learning_data()
        
        return redirect(url_for("admin.learning_dashboard"))
    except Exception as e:
        flash(f"Error processing suggestion: {str(e)}", "danger")
        return redirect(url_for("admin.learning_dashboard"))


