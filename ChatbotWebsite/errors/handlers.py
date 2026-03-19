from flask import Blueprint, render_template
import traceback

errors = Blueprint("errors", __name__)


# 404 Error Page
@errors.app_errorhandler(404)
def error_404(error):
    return render_template("errors/404.html"), 404


# 403 Error Page
@errors.app_errorhandler(403)
def error_403(error):
    return render_template("errors/403.html"), 403


# 500 Error Page
@errors.app_errorhandler(500)
def error_500(error):
    # Log the error for debugging
    print(f"Internal Server Error: {error}")
    print(traceback.format_exc())
    return render_template("errors/500.html"), 500
