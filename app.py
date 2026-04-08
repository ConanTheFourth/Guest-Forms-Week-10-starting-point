from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'top-secret'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///guestlist.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    quan = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text)
    rel = db.Column(db.String(50), nullable=False)
    accommodations = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()


@app.route('/')
def index():
    return redirect(url_for('profile'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        quan = request.form.get('quan', '').strip()
        comments = request.form.get('comments', '').strip()
        rel = request.form.get('rel', '').strip()
        accommodations = request.form.get('accommodations') == "yes"  # True if checked
        
        # Validation
        if not name or not email or not quan or not rel:
            error = "Please fill in all required fields"
            return render_template('profileForm.html', error=error)
        
        # Create new profile in database
        try:
            new_profile = Profile(
                name=name,
                email=email,
                quan=int(quan),
                comments=comments,
                rel=rel,
                accommodations=accommodations
            )
            db.session.add(new_profile)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            error = "An error occurred while saving your profile. Please try again."
            return render_template('profileForm.html', error=error)
        
        return render_template(
            'profileSuccess.html',
            name=name,
            email=email,
            quan=quan,
            comments=comments,
            rel=rel,
            accommodations=accommodations
        )
    
    # This handles GET requests - moved outside the POST block
    return render_template('profileForm.html')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        rating = request.form.get('rating', '').strip()
        feedback = request.form.get('feedback', '').strip()

        if not rating:
            error = "Please provide a rating"
            return render_template('feedbackForm.html', error=error)

        # Create new feedback in database
        try:
            new_feedback = Feedback(
                rating=int(rating),
                feedback=feedback
            )
            db.session.add(new_feedback)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            error = "An error occurred while saving your feedback. Please try again."
            return render_template('feedbackForm.html', error=error)

        return render_template(
            'feedbackSuccess.html',
            rating=rating,
            feedback=feedback
        )

    return render_template('feedbackForm.html')

    # Create new profile in database
    try:
        new_profile = Profile(
            name=name,
            email=email,
            quan=int(quan),
            comments=comments,
            rel=rel,
            accommodations=accommodations
        )
        db.session.add(new_profile)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        error = "An error occurred while saving your profile. Please try again."
        return render_template('profileForm.html', error=error)

    return render_template('feedbackForm.html')

@app.route('/admin/profiles')
def admin_profiles():
    profiles = Profile.query.all()
    return render_template('admin_profiles.html', profiles=profiles)

@app.route('/admin/feedback')
def admin_feedback():
    feedbacks = Feedback.query.all()
    return render_template('admin_feedback.html', feedbacks=feedbacks)

