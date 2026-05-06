from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'nocturna_secret_key'

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nocturna.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Prevent caching so back button won't show logged in pages
@app.after_request
def add_no_cache(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

# Create tables
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/index')
def index():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/discover')
def discover():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('discover.html')

@app.route('/artists')
def artists():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('artists.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['fname']
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            error = 'Passwords do not match!'
        elif User.query.filter_by(username=username).first():
            error = 'Username already exists!'
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))

    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['fname']
        password = request.form['lpass']

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['username'] = user.username
            return redirect(url_for('index'))
        else:
            error = 'Invalid username or password!'

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)