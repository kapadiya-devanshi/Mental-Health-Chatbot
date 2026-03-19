# SoulMate - Mental Health Chatbot

SoulMate is a comprehensive web application built with Flask that serves as a mental health companion. It integrates a conversational AI model to provide support and chat interaction, alongside tools for personal reflection such as mood journaling.

## Features

- **User Authentication**: Secure user registration, login, and password reset functionalities using Flask-Login and Flask-Bcrypt.
- **AI Chatbot**: A mental health chatbot powered by a custom deep learning model (`chatbot-model.h5`) that interacts with users in real-time.
- **Mood Journal**: Users can log their daily moods and write journal entries to reflect on their mental well-being.
- **Feedback System**: A rating and feedback system allows users to share their thoughts. Admins can review, approve, and publish feedback on the platform.
- **Admin Dashboard**: Specialized administrative capabilities for managing users, reviewing user feedback, and monitoring the platform.

## Tech Stack

### Backend
- **Framework**: Flask
- **Database**: SQLite / MySQL (via SQLAlchemy & PyMySQL)
- **Machine Learning**: TensorFlow, Keras, NLTK, NumPy
- **Authentication**: Flask-Login, Flask-Bcrypt, itsdangerous
- **Other utilities**: Flask-Mail (for password resets), Flask-WTF (form handling)

### Frontend
- **HTML / CSS / JS**: Custom styling with an emotionally supportive, professional, and accessible user interface.
- Responsive design tailored for providing the best mental health support experience across devices.

## Installation & Setup

1. **Clone the repository or download the source code**.

2. **Navigate to the project directory**:
   ```bash
   cd SoulMate
   ```

3. **Create and activate a virtual environment** (recommended):
   ```bash
   python -m venv env
   # On Windows:
   env\Scripts\activate
   # On macOS/Linux:
   source env/bin/activate
   ```

4. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Database Initialization**:
   The application uses SQLite by default. The required database schemas will be created automatically upon the first run.

6. **Email Configuration**:
   Read the `EMAIL_SETUP.md` file to configure the necessary environment variables and settings for sending emails (required for the password reset functionality).

7. **Run the Application**:
   ```bash
   python run.py
   ```
   The application will start and be accessible at `http://127.0.0.1:5000/`.

## Project Structure Overview

- `run.py`: The entry point for starting the application.
- `ChatbotWebsite/`: The core Flask application package containing blueprints.
  - `models.py`: Database models (`User`, `ChatMessage`, `Journal`, `Feedback`).
  - `chatbot/`, `journal/`, `users/`, `admin/`, `main/`: Individual application modules defining routes and logic.
  - `templates/` & `static/`: HTML templates and static assets (CSS, JS, images).
- `chatbot-model.h5`: The trained deep learning model for the NLP chatbot.
- `data.pickle` & `users.db`: Serialized data and the SQLite database file.
- `make_admin.py` / `make_admin_simple.py`: Utility scripts to modify a user's admin status.
- `requirements.txt`: Required Python dependencies.

## Usage

- **For Regular Users**: Sign up for an account, write out your thoughts in the journal, or chat directly with the AI for active listening and support.
- **For Admins**: You can elevate an existing account to an admin using the included `make_admin_simple.py` script. Admin access unlocks a dedicated dashboard to control the application's feedback display and system monitoring.
