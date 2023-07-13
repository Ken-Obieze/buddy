from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required

app = Flask(__name__)
app.config['SECRET_KEY'] = 'This is our secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

login_manager = LoginManager(app)
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
    current_year = date.today().year
    user_avatar = get_user_avatar(current_user)
    return render_template('dashboard.html', user=current_user, current_year=current_year, user_avatar=user_avatar)


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


if __name__ == '__main__':
    app.run(debug=True)
