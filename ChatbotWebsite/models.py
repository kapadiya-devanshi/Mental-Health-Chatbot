from datetime import datetime
from ChatbotWebsite import db, login_manager
from flask_login import UserMixin
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from flask import current_app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# User class for the database


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    profile_image = db.Column(
        db.String(20), nullable=False, default='default.jpg')
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    # Backref One to many relationship with ChatMessage Class
    messages = db.relationship('ChatMessage', backref='user', lazy=True)
    # Backref One to many relationship with Journal Class
    journals = db.relationship('Journal', backref='user', lazy=True)
    # Backref One to many relationship with Feedback Class
    feedbacks = db.relationship('Feedback', backref='user', lazy=True)

    # Reset password token
    def get_reset_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        token = s.dumps({'user_id': self.id})
        return token

    # Verify reset password token
    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=1800)['user_id']
        except:
            return None
        return User.query.get(user_id)

    # String representation of the user
    def __repr__(self):
        return f'User({self.username}, {self.email})'

# ChatMessage class for the database


class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(5), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    message = db.Column(db.String(3000), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.id'), nullable=False)  # Foreign key to User Class

    # String representation of the chat message
    def __repr__(self):
        return f'ChatMessage({self.sender}, {self.timestamp}, {self.message})'

# Journal class for the database


class Journal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    mood = db.Column(db.String(30), nullable=False)
    content = db.Column(db.String(3000), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.id'), nullable=False)  # Foreign key to User Class

    # String representation of the journal
    def __repr__(self):
        return f'Journal({self.timestamp}, {self.mood}, {self.content})'

# Feedback class for the database


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    rating = db.Column(db.Integer, nullable=False)  # Star rating (1-5)
    notes = db.Column(db.String(3000), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.id'), nullable=False)  # Foreign key to User Class
    is_approved = db.Column(db.Boolean, nullable=False, default=False)  # Admin approval status
    is_published = db.Column(db.Boolean, nullable=False, default=False)  # Published on desktop

    # String representation of the feedback
    def __repr__(self):
        return f'Feedback({self.timestamp}, {self.rating}, {self.is_approved})'


# Premium Subscription class for the database


class PremiumSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_type = db.Column(db.String(20), nullable=False)  # 'plus' or 'pro'
    amount_paid = db.Column(db.Float, nullable=False)  # Amount in INR
    billing_cycle = db.Column(db.String(20), nullable=False, default='monthly')  # 'monthly' or 'annual'
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    payment_method = db.Column(db.String(50), nullable=True)
    transaction_id = db.Column(db.String(100), nullable=True)
    
    # Relationship with User
    user = db.relationship('User', backref='subscriptions', lazy=True)
    
    def is_valid(self):
        """Check if subscription is still valid"""
        return self.is_active and datetime.now() < self.end_date
    
    def __repr__(self):
        return f'PremiumSubscription({self.user.username}, {self.plan_type}, ₹{self.amount_paid})'
