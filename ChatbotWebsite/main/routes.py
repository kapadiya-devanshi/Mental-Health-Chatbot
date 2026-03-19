from flask import render_template, request, flash, redirect, url_for, jsonify
from flask import Blueprint
from flask_login import current_user, login_required
from datetime import datetime, timedelta
from ChatbotWebsite import db
from ChatbotWebsite.models import Feedback, PremiumSubscription

main = Blueprint("main", __name__)


# Home Page
@main.route("/")
def home():
    try:
        # Get approved and published feedbacks for display
        published_feedbacks = Feedback.query.filter_by(is_approved=True, is_published=True).order_by(Feedback.timestamp.desc()).limit(10).all()
        return render_template("home.html", title="Mental Health Chatbot", published_feedbacks=published_feedbacks)
    except Exception as e:
        # Log the error and return template without feedbacks
        print(f"Error loading feedbacks: {e}")
        return render_template("home.html", title="Mental Health Chatbot", published_feedbacks=[])


# About Page
@main.route("/about")
def about():
    return render_template("about.html", title="About")


# SOS Page
@main.route("/sos")
def sos():
    return render_template("sos.html", title="SOS")


# Feedback Page
@main.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    try:
        if request.method == "POST":
            rating = request.form.get("rating")
            notes = request.form.get("notes", "")
            
            if not rating:
                flash("Please provide a rating", "danger")
                return redirect(url_for("main.feedback"))
            
            try:
                new_feedback = Feedback(
                    rating=int(rating),
                    notes=notes,
                    user_id=current_user.id,
                    is_approved=False,
                    is_published=False
                )
                db.session.add(new_feedback)
                db.session.commit()
                flash("Thank you for your feedback! It has been submitted for admin review.", "success")
                return redirect(url_for("main.feedback"))
            except Exception as e:
                db.session.rollback()
                print(f"Error submitting feedback: {e}")
                flash("An error occurred while submitting your feedback. Please try again.", "danger")
                return redirect(url_for("main.feedback"))
        
        # Get approved and published feedbacks for display
        published_feedbacks = Feedback.query.filter_by(is_approved=True, is_published=True).order_by(Feedback.timestamp.desc()).limit(10).all()
        return render_template("feedback.html", title="Feedback", published_feedbacks=published_feedbacks)
    except Exception as e:
        print(f"Error in feedback route: {e}")
        flash("An error occurred. Please try again later.", "danger")
        return render_template("feedback.html", title="Feedback", published_feedbacks=[])


# Premium Page
@main.route("/premium")
@login_required
def premium():
    # Get user's current subscription if any
    current_subscription = PremiumSubscription.query.filter_by(
        user_id=current_user.id, 
        is_active=True
    ).order_by(PremiumSubscription.end_date.desc()).first()
    
    # Check if subscription is still valid
    has_active_subscription = False
    subscription_type = None
    if current_subscription and current_subscription.is_valid():
        has_active_subscription = True
        subscription_type = current_subscription.plan_type
    
    return render_template("premium.html", 
                         title="Premium Plans",
                         has_active_subscription=has_active_subscription,
                         subscription_type=subscription_type,
                         current_subscription=current_subscription)


# Subscribe to Premium Plan
@main.route("/subscribe", methods=["POST"])
@login_required
def subscribe():
    try:
        plan_type = request.form.get("plan_type")
        billing_cycle = request.form.get("billing_cycle", "monthly")
        
        if plan_type not in ["plus", "pro"]:
            flash("Invalid plan selected.", "danger")
            return redirect(url_for("main.premium"))
        
        # Check if user already has an active subscription
        existing_sub = PremiumSubscription.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if existing_sub and existing_sub.is_valid():
            flash("You already have an active subscription!", "info")
            return redirect(url_for("main.premium"))
        
        # Calculate amount and duration
        if plan_type == "plus":
            amount = 2870 if billing_cycle == "annual" else 299
            duration_days = 365 if billing_cycle == "annual" else 30
        else:  # pro
            amount = 7670 if billing_cycle == "annual" else 799
            duration_days = 365 if billing_cycle == "annual" else 30
        
        # Create new subscription
        new_subscription = PremiumSubscription(
            user_id=current_user.id,
            plan_type=plan_type,
            amount_paid=amount,
            billing_cycle=billing_cycle,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=duration_days),
            is_active=True,
            payment_method="Demo Payment",
            transaction_id=f"DEMO_{datetime.now().strftime('%Y%m%d%H%M%S')}_{current_user.id}"
        )
        
        db.session.add(new_subscription)
        db.session.commit()
        
        flash(f"Successfully subscribed to {plan_type.title()} plan! Thank you for supporting SoulMate.", "success")
        return redirect(url_for("main.premium"))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in subscription: {e}")
        flash("An error occurred while processing your subscription. Please try again.", "danger")
        return redirect(url_for("main.premium"))


# Cancel Subscription
@main.route("/cancel-subscription", methods=["POST"])
@login_required
def cancel_subscription():
    try:
        subscription = PremiumSubscription.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if subscription:
            subscription.is_active = False
            db.session.commit()
            flash("Your subscription has been cancelled. You will have access until the end of your billing period.", "info")
        else:
            flash("No active subscription found.", "warning")
            
        return redirect(url_for("main.premium"))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error cancelling subscription: {e}")
        flash("An error occurred. Please try again.", "danger")
        return redirect(url_for("main.premium"))


# Get published feedbacks (API endpoint for desktop display)
@main.route("/api/feedbacks")
def get_feedbacks():
    try:
        published_feedbacks = Feedback.query.filter_by(is_approved=True, is_published=True).order_by(Feedback.timestamp.desc()).all()
        feedbacks_data = []
        for feedback in published_feedbacks:
            feedbacks_data.append({
                "id": feedback.id,
                "rating": feedback.rating,
                "notes": feedback.notes,
                "timestamp": feedback.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "username": feedback.user.username if feedback.user else "Anonymous"
            })
        return jsonify(feedbacks_data)
    except Exception as e:
        print(f"Error in get_feedbacks API: {e}")
        return jsonify([]), 500
