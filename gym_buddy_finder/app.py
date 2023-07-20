from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_googlemaps import GoogleMaps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'This is our secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

app.config['GOOGLEMAPS_KEY'] = 'AIzaSyDWGUj5K9NHq_MSoCpJDc-4J0Ud-qHNVLY'
GoogleMaps(app)

chat_bp = Blueprint("chat", __name__)

login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'signin'


class User(UserMixin, db.Model):
    """User model."""
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    profile_picture = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    address = db.Column(db.String(200))
    latitude = db.Column(db.String(20))
    longitude = db.Column(db.String(20))
    exercise_preferences = db.Column(db.JSON)

    def get_id(self):
        """Fetch user_id."""
        return str(self.id)


class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def landing():
    """Landing page."""
    return render_template('landing.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Creates user."""
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return render_template("signup.html", error="Passwords don't match")

        user = User(first_name=first_name, last_name=last_name, email=email, password=password)

        db.session.add(user)
        db.session.commit()

        flash('Sign up successful! Please log in.')
        return redirect(url_for('signin'))

    return render_template('signup.html')


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    """Signin users."""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and user.password == password:
            login_user(user)
            return redirect(url_for('dashboard'))

        flash('Invalid email or password. Please try again.')

    return render_template('signin.html')


@app.route('/signout')
@login_required
def signout():
    """Log out the user."""
    logout_user()
    return redirect(url_for('landing'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        address = request.form['address']
        selected_exercises = request.form.getlist('exercises')

        current_user.phone_number = phone_number
        current_user.address = address
        current_user.exercise_preferences = selected_exercises

        db.session.commit()

        flash('Profile updated successfully!')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=current_user)


def geocode_address(address):
    import requests
    response = requests.get(f'https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json?access_token=pk.eyJ1Ijoia2Vub2JpZXplIiwiYSI6ImNsa2IxbDB0aTA5djEzb28wbHl5NWJvemoifQ.OErQrPGpsGgJ8VyB6sJz8Q')
    data = response.json()
    longitude = data['features'][0]['center'][0]
    latitude = data['features'][0]['center'][1]
    return longitude, latitude

@app.route("/matching")
@login_required
def matching():
    address = current_user.address
    longitude, latitude = geocode_address(address)

    users = User.query.all()

    marker_info = []

    for user in users:
        if user.id == current_user.id:
            continue

        marker_info.append({
            "location": {"lat": user.latitude, "lng": user.longitude},
            "title": user.first_name,
            "snippet": user.last_name,
            "address": user.address,
            "phone": user.phone_number,
            "profile_picture": user.profile_picture
        })

    return render_template("matching.html", marker_info=marker_info)

@app.route("/buddy_up/<int:user_id>")
@login_required
def buddy_up(user_id):
    sender_id = current_user.id
    receiver_id = user_id
    notification = Notification(sender_id=sender_id, receiver_id=receiver_id, type="buddy_up")
    db.session.add(notification)
    db.session.commit()
    return {"success": True}


@app.route('/chat')
@login_required
def chat():
    chat_id = request.args.get('chat_id')
    
    chat = ChatMessage.query.filter((ChatMessage.sender_id == current_user.id) | (ChatMessage.receiver_id == current_user.id),
                             ChatMessage.id == chat_id).first()
    if not chat:
        return "Chat not found or you are not authorized to access it.", 403

    return render_template('chat.html', chat=chat)

@app.route('/notifications')
@login_required
def notifications():
    return render_template('notifications.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
