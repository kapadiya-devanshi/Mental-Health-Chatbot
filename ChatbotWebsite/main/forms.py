from flask_wtf import FlaskForm
from wtforms import HiddenField, TextAreaField, SubmitField, IntegerField
from wtforms.validators import DataRequired, NumberRange, Length, Optional, ValidationError


def validate_rating(form, field):
    """Custom validator for rating"""
    if not field.data:
        raise ValidationError("Please select a rating")
    try:
        rating = int(field.data)
        if not (1 <= rating <= 5):
            raise ValidationError("Rating must be between 1 and 5")
    except (ValueError, TypeError):
        raise ValidationError("Please select a valid rating")


# Feedback Form
class FeedbackForm(FlaskForm):
    rating = HiddenField(
        "Rating",
        validators=[DataRequired(message="Please select a rating"), validate_rating]
    )
    notes = TextAreaField(
        "Additional Notes (Optional)",
        validators=[Optional(), Length(max=2000)]
    )
    submit = SubmitField("Submit Feedback")

