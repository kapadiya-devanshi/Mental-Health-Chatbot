from ChatbotWebsite import create_app , db

# Create the app
app = create_app()
with app.app_context():
    db.create_all()
# Run the app
if __name__ == '__main__':
    app.run()
    # app.run(debug=True)
