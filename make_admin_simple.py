"""
Simple script to make a user an admin.
Edit the email or username below and run this script.
"""
from ChatbotWebsite import create_app, db
from ChatbotWebsite.models import User

app = create_app()

# ============================================
# EDIT THIS: Set the email or username here
# ============================================
USER_EMAIL = ""  # Change this to your user's email
# OR use username instead:


def make_admin():
    with app.app_context():
        # Find user by email or username
        if 'USER_EMAIL' in globals() and USER_EMAIL:
            user = User.query.filter_by(email=USER_EMAIL).first()
            identifier = f"email '{USER_EMAIL}'"
        elif 'USERNAME' in globals() and USERNAME:
            user = User.query.filter_by(username=USERNAME).first()
            identifier = f"username '{USERNAME}'"
        else:
            print("Error: Please set either USER_EMAIL or USERNAME in the script.")
            return
        
        if not user:
            print(f"User with {identifier} not found.")
            print("\nAvailable users:")
            all_users = User.query.all()
            for u in all_users:
                print(f"  - {u.username} ({u.email})")
            return
        
        # Make user admin
        user.is_admin = True
        db.session.commit()
        
        print(f"Successfully made '{user.username}' ({user.email}) an admin!")
        print(f"\nYou can now:")
        print(f"  1. Log in as {user.email}")
        print(f"  2. Go to the home page")
        print(f"  3. Click the 'ADMIN DASHBOARD' button")

if __name__ == '__main__':
    make_admin()



