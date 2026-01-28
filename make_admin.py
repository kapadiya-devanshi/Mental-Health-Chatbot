"""
Script to make a user an admin.
Run this script to grant admin privileges to a user.
"""
from ChatbotWebsite import create_app, db
from ChatbotWebsite.models import User

app = create_app()

def make_user_admin(email=None, username=None):
    """
    Make a user an admin by email or username.
    
    Args:
        email: User's email address
        username: User's username
    """
    with app.app_context():
        user = None
        
        if email:
            user = User.query.filter_by(email=email).first()
            if not user:
                print(f"User with email '{email}' not found.")
                return False
        elif username:
            user = User.query.filter_by(username=username).first()
            if not user:
                print(f"User with username '{username}' not found.")
                return False
        else:
            print("Please provide either email or username.")
            print("\nUsage examples:")
            print("  make_user_admin(email='user@example.com')")
            print("  make_user_admin(username='john_doe')")
            return False
        
        # Make user admin
        user.is_admin = True
        db.session.commit()
        
        print(f"✓ Successfully made '{user.username}' ({user.email}) an admin!")
        return True

def list_all_users():
    """List all users and their admin status."""
    with app.app_context():
        users = User.query.all()
        if not users:
            print("No users found in the database.")
            return
        
        print("\n" + "="*60)
        print("All Users:")
        print("="*60)
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Admin':<10}")
        print("-"*60)
        for user in users:
            admin_status = "Yes" if user.is_admin else "No"
            print(f"{user.id:<5} {user.username:<20} {user.email:<30} {admin_status:<10}")
        print("="*60)

if __name__ == '__main__':
    import sys
    
    print("="*60)
    print("Admin User Management")
    print("="*60)
    
    # List all users first
    list_all_users()
    
    # Interactive mode
    print("\n" + "="*60)
    print("To make a user admin, choose an option:")
    print("="*60)
    print("1. Make admin by email")
    print("2. Make admin by username")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == '1':
        email = input("Enter user email: ").strip()
        make_user_admin(email=email)
    elif choice == '2':
        username = input("Enter username: ").strip()
        make_user_admin(username=username)
    elif choice == '3':
        print("Exiting...")
        sys.exit(0)
    else:
        print("Invalid choice. Exiting...")
        sys.exit(1)
    
    # Show updated list
    print("\n")
    list_all_users()

