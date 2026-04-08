from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func, or_


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

        # Append reminder for 5-star feedbacks when feedback text is provided
        reminder = "\n\nReminder: Send a thank you message."
        feedback_text = feedback
        if rating == '5' and feedback_text and reminder not in feedback_text:
            feedback_text = feedback_text + reminder

        # Create new feedback in database
        try:
            new_feedback = Feedback(
                rating=int(rating),
                feedback=feedback_text
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
            feedback=feedback_text
        )

    return render_template('feedbackForm.html')

@app.route('/admin/profiles')
def admin_profiles():
    profiles = Profile.query.all()
    return render_template('admin_profiles.html', profiles=profiles) + admin_nav_html()

@app.route('/admin/profiles/siblings')
def admin_sibling_profiles():
    # Return profiles with relationship 'sibling', quantity less than 3, and no accommodations
    profiles = Profile.query.filter(
        Profile.rel == 'sibling',
        Profile.quan < 3,
        Profile.accommodations == False
    ).all()
    return render_template('admin_profiles.html', profiles=profiles) + admin_nav_html()

@app.route('/admin/profiles/high_capacity_or_accommodations')
def admin_profiles_high_capacity_or_accommodations():
    # Profiles with quantity >= 5 OR accommodations requested
    profiles = Profile.query.filter(
        or_(
            Profile.quan >= 5,
            Profile.accommodations == True
        )
    ).all()
    return render_template('admin_profiles.html', profiles=profiles) + admin_nav_html()

@app.route('/admin/profiles/non_related')
def admin_non_related_profiles():
    # Profiles indicating non-related guests: coworkers or non-family members
    profiles = Profile.query.filter(
        or_(
            Profile.rel.ilike('%cowork%'),
            Profile.rel.ilike('%non%family%'),
            Profile.rel.ilike('%non family%'),
            Profile.rel.ilike('%non-family%')
        )
    ).all()
    return render_template('admin_profiles.html', profiles=profiles) + admin_nav_html()

@app.route('/admin')
def admin_index():
    links = [
        ('All Profiles','/admin/profiles'),
        ('Sibling (<3)','/admin/profiles/siblings'),
        ('High capacity or accommodations','/admin/profiles/high_capacity_or_accommodations'),
        ('Non-related (coworkers/non-family)','/admin/profiles/non_related'),
        ('Feedback','/admin/feedback'),
    ]
    html = '<h1>Admin Directory</h1><ul>'
    for name,url in links:
        html += f'<li><a href="{url}">{name}</a></li>'
    html += '</ul>'
    html += '<p><a href="/admin/profiles">Main database page</a></p>'
    html += admin_nav_html()
    return html


def admin_nav_html():
    return ("<hr><div>Admin Directory: "
            "<a href=\"/admin\">Directory</a> | "
            "<a href=\"/admin/profiles\">All Profiles</a> | "
            "<a href=\"/admin/profiles/siblings\">Sibling (&lt;3)</a> | "
            "<a href=\"/admin/profiles/high_capacity_or_accommodations\">High capacity or accommodations</a> | "
            "<a href=\"/admin/profiles/non_related\">Non-related (coworkers/non-family)</a> | "
            "<a href=\"/admin/feedback\">Feedback</a>"
            "</div>")

@app.route('/admin/feedback')
def admin_feedback():
    # Delete feedbacks where no feedback text was provided (null, empty, or whitespace)
    try:
        Feedback.query.filter((Feedback.feedback == None) | (func.length(func.trim(Feedback.feedback)) == 0)).delete(synchronize_session=False)
        db.session.commit()
    except Exception:
        db.session.rollback()

    feedbacks = Feedback.query.all()
    # Ensure all 5-star feedbacks with text include reminder and save changes to DB
    reminder = "\n\nReminder: Send a thank you message."
    updated = False
    for f in feedbacks:
        if f.rating == 5 and f.feedback and reminder not in f.feedback:
            f.feedback = f.feedback + reminder
            updated = True
    if updated:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
    return render_template('admin_feedback.html', feedbacks=feedbacks) + admin_nav_html()

