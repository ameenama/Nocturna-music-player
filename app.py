from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'nocturna_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nocturna.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.after_request
def add_no_cache(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# ── Models ──

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(200), nullable=True)
    password = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(20), default='active')
    theme = db.Column(db.String(20), default='dark')
    is_artist = db.Column(db.Integer, default=0)
    artist_requested = db.Column(db.Integer, default=0)
    artist_name = db.Column(db.String(200), nullable=True)
    instagram = db.Column(db.String(300), nullable=True)
    twitter = db.Column(db.String(300), nullable=True)
    spotify = db.Column(db.String(300), nullable=True)
    youtube = db.Column(db.String(300), nullable=True)
    soundcloud = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist_name = db.Column(db.String(200), nullable=False)
    audio_url = db.Column(db.String(500), nullable=False)
    cover_url = db.Column(db.String(500), nullable=True)
    genre = db.Column(db.String(100), nullable=True)
    album = db.Column(db.String(200), nullable=True)
    release_date = db.Column(db.String(50), nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    approved = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

def admin_required():
    return session.get('username') == 'admin'

# ── Public routes ──

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
    tracks = Track.query.filter_by(approved=1).order_by(Track.created_at.desc()).all()
    return render_template('discover.html', uploaded_tracks=tracks)

@app.route('/artists')
def artists():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('artists.html')

@app.route('/releases')
def releases():
    if 'username' not in session:
        return redirect(url_for('home'))
    tracks = Track.query.filter_by(approved=1).order_by(Track.created_at.desc()).all()
    return render_template('releases.html', uploaded_tracks=tracks)

@app.route('/about')
def about():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        new_msg = ContactMessage(name=name, email=email, subject=subject, message=message)
        db.session.add(new_msg)
        db.session.commit()
        return render_template('contact.html', success=True)
    return render_template('contact.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

# ── Auth routes ──

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
            email = request.form.get('email')
            new_user = User(username=username, email=email, password=password)
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
            if user.status == 'banned':
                error = 'Your account has been suspended. Please contact support.'
            else:
                session['username'] = user.username
                if user.username == 'admin':
                    return redirect(url_for('admin'))
                return redirect(url_for('index'))
        else:
            error = 'Invalid username or password!'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

# ── Settings ──

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'username' not in session:
        return redirect(url_for('home'))
    user = User.query.filter_by(username=session['username']).first()
    success = None
    error = None
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'username':
            new_username = request.form.get('new_username', '').strip()
            if not new_username:
                error = 'Username cannot be empty.'
            elif User.query.filter_by(username=new_username).first():
                error = 'Username already taken.'
            else:
                user.username = new_username
                session['username'] = new_username
                db.session.commit()
                success = 'Username updated successfully.'
        elif action == 'email':
            new_email = request.form.get('new_email', '').strip()
            if not new_email:
                error = 'Email cannot be empty.'
            else:
                user.email = new_email
                db.session.commit()
                success = 'Email updated successfully.'
        elif action == 'password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            if user.password != current_password:
                error = 'Current password is incorrect.'
            elif not new_password:
                error = 'New password cannot be empty.'
            elif new_password != confirm_password:
                error = 'New passwords do not match.'
            else:
                user.password = new_password
                db.session.commit()
                success = 'Password updated successfully.'
        elif action == 'theme':
            new_theme = request.form.get('theme', 'dark')
            user.theme = new_theme
            db.session.commit()
            success = 'Appearance updated successfully.'
        elif action == 'delete':
            confirm_delete = request.form.get('confirm_delete', '')
            if confirm_delete != user.username:
                error = 'Please type your username correctly to confirm deletion.'
            else:
                db.session.delete(user)
                db.session.commit()
                session.pop('username', None)
                return redirect(url_for('home'))
    return render_template('settings.html', user=user, success=success, error=error)

# ── Artist routes ──

@app.route('/request-artist', methods=['GET', 'POST'])
def request_artist():
    if 'username' not in session:
        return redirect(url_for('home'))
    user = User.query.filter_by(username=session['username']).first()
    success = None
    error = None
    if request.method == 'POST':
        if user.is_artist:
            error = 'You are already an approved artist.'
        elif user.artist_requested:
            error = 'You have already submitted an application. Please wait for admin approval.'
        else:
            artist_name = request.form.get('artist_name', '').strip()
            genre = request.form.get('genre', '').strip()
            cover_url = request.form.get('cover_url', '').strip()
            album_title = request.form.get('album_title', '').strip()
            release_date = request.form.get('release_date', '').strip()

            if not artist_name or not genre or not album_title or not cover_url:
                error = 'Artist name, genre, album title and cover art are required.'
            else:
                # Save social links
                user.artist_name = artist_name
                user.instagram = request.form.get('instagram', '').strip() or None
                user.twitter = request.form.get('twitter', '').strip() or None
                user.spotify = request.form.get('spotify', '').strip() or None
                user.youtube = request.form.get('youtube', '').strip() or None
                user.soundcloud = request.form.get('soundcloud', '').strip() or None
                user.artist_requested = 1

                # Save tracks
                track_titles = request.form.getlist('track_title[]')
                track_urls = request.form.getlist('track_url[]')

                for title, audio_url in zip(track_titles, track_urls):
                    title = title.strip()
                    audio_url = audio_url.strip()
                    if title and audio_url:
                        track = Track(
                            title=title,
                            artist_name=artist_name,
                            audio_url=audio_url,
                            cover_url=cover_url or None,
                            genre=genre or None,
                            album=album_title or None,
                            release_date=release_date or None,
                            uploaded_by=user.id,
                            approved=0
                        )
                        db.session.add(track)

                db.session.commit()
                success = True

    return render_template('request_artist.html', user=user, success=success, error=error)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('home'))
    user = User.query.filter_by(username=session['username']).first()
    if not user.is_artist:
        return redirect(url_for('request_artist'))
    success = None
    error = None
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        artist_name = request.form.get('artist_name', '').strip()
        audio_url = request.form.get('audio_url', '').strip()
        cover_url = request.form.get('cover_url', '').strip()
        genre = request.form.get('genre', '').strip()
        album = request.form.get('album', '').strip()
        if not title or not artist_name or not audio_url:
            error = 'Title, artist name and audio URL are required.'
        else:
            track = Track(
                title=title,
                artist_name=artist_name,
                audio_url=audio_url,
                cover_url=cover_url or None,
                genre=genre or None,
                album=album or None,
                uploaded_by=user.id,
                approved=0
            )
            db.session.add(track)
            db.session.commit()
            success = 'Track submitted for admin approval. It will appear on Discover once approved.'
    my_tracks = Track.query.filter_by(uploaded_by=user.id).order_by(Track.created_at.desc()).all()
    return render_template('upload.html', user=user, success=success, error=error, my_tracks=my_tracks)

# ── Admin routes ──

@app.route('/admin')
def admin():
    if not admin_required():
        return redirect(url_for('home'))
    search = request.args.get('search', '')
    status_filter = request.args.get('status', 'all')
    query = User.query.filter(User.username != 'admin')
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    users = query.order_by(User.created_at.desc()).all()
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    artist_requests = User.query.filter_by(artist_requested=1, is_artist=0).filter(User.username != 'admin').all()
    pending_tracks = Track.query.filter_by(approved=0).order_by(Track.created_at.desc()).all()
    approved_tracks = Track.query.filter_by(approved=1).order_by(Track.created_at.desc()).all()
    week_ago = datetime.utcnow() - timedelta(days=7)
    total_users = User.query.filter(User.username != 'admin').count()
    total_messages = ContactMessage.query.count()
    new_this_week = User.query.filter(User.created_at >= week_ago, User.username != 'admin').count()
    return render_template('admin.html',
        users=users, messages=messages,
        artist_requests=artist_requests,
        pending_tracks=pending_tracks,
        approved_tracks=approved_tracks,
        total_users=total_users, total_messages=total_messages,
        new_this_week=new_this_week,
        search=search, status_filter=status_filter
    )

@app.route('/admin/edit/<int:user_id>', methods=['GET', 'POST'])
def admin_edit_user(user_id):
    if not admin_required():
        return redirect(url_for('home'))
    user = User.query.get_or_404(user_id)
    error = None
    if request.method == 'POST':
        new_username = request.form.get('username')
        new_email = request.form.get('email')
        existing = User.query.filter_by(username=new_username).first()
        if existing and existing.id != user.id:
            error = 'Username already taken.'
        else:
            user.username = new_username
            user.email = new_email
            db.session.commit()
            return redirect(url_for('admin'))
    return render_template('admin_edit.html', user=user, error=error)

@app.route('/admin/delete/<int:user_id>')
def admin_delete_user(user_id):
    if not admin_required():
        return redirect(url_for('home'))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/ban/<int:user_id>')
def admin_ban_user(user_id):
    if not admin_required():
        return redirect(url_for('home'))
    user = User.query.get_or_404(user_id)
    user.status = 'banned' if user.status == 'active' else 'active'
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/delete_message/<int:msg_id>')
def admin_delete_message(msg_id):
    if not admin_required():
        return redirect(url_for('home'))
    msg = ContactMessage.query.get_or_404(msg_id)
    db.session.delete(msg)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/approve-artist/<int:user_id>')
def admin_approve_artist(user_id):
    if not admin_required():
        return redirect(url_for('home'))
    user = User.query.get_or_404(user_id)
    user.is_artist = 1
    user.artist_requested = 0
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/reject-artist/<int:user_id>')
def admin_reject_artist(user_id):
    if not admin_required():
        return redirect(url_for('home'))
    user = User.query.get_or_404(user_id)
    user.artist_requested = 0
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/approve-track/<int:track_id>')
def admin_approve_track(track_id):
    if not admin_required():
        return redirect(url_for('home'))
    track = Track.query.get_or_404(track_id)
    track.approved = 1
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/delete-track/<int:track_id>')
def admin_delete_track(track_id):
    if not admin_required():
        return redirect(url_for('home'))
    track = Track.query.get_or_404(track_id)
    db.session.delete(track)
    db.session.commit()
    return redirect(url_for('admin'))

import requests
import json

JIOSAAVN_BASE = 'https://www.jiosaavn.com/api.php'

def jiosaavn_search_songs(query, limit=12):
    params = {
        '__call': 'search.getResults',
        '_format': 'json',
        '_marker': '0',
        'api_version': '4',
        'ctx': 'web6dot0',
        'query': query,
        'n': limit,
        'p': 1
    }
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(JIOSAAVN_BASE, params=params, headers=headers, timeout=10)
    return res.json()

def jiosaavn_get_song_url(encrypted_url):
    import base64
    try:
        from pyDes import des, CBC, PAD_PKCS5
        key = b'38346591'
        iv = b'00000000'
        c = des(key, CBC, iv, pad=None, padmode=PAD_PKCS5)
        enc = base64.b64decode(encrypted_url.strip())
        dec = c.decrypt(enc, padmode=PAD_PKCS5)
        url = dec.decode('utf-8').replace('http://', 'https://')
        url = url.replace('96.mp4', '320.mp4')
        return url
    except:
        return ''

@app.route('/api/search/songs')
def search_songs():
    query = request.args.get('query', 'top hits')
    limit = int(request.args.get('limit', 12))
    try:
        data = jiosaavn_search_songs(query, limit)
        results = []
        songs = data.get('results', [])
        for song in songs:
            audio_url = jiosaavn_get_song_url(song.get('encrypted_media_url', ''))
            results.append({
                'name': song.get('song', ''),
                'artists': {'primary': [{'name': song.get('singers', '—')}]},
                'image': [{'url': song.get('image', '').replace('150x150', '500x500')}],
                'downloadUrl': [{'url': audio_url}],
                'id': song.get('id', '')
            })
        return {'data': {'results': results}}
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/api/search/albums')
def search_albums():
    query = request.args.get('query', 'top albums')
    limit = int(request.args.get('limit', 5))
    try:
        params = {
            '__call': 'search.getAlbumResults',
            '_format': 'json',
            '_marker': '0',
            'api_version': '4',
            'ctx': 'web6dot0',
            'query': query,
            'n': limit,
            'p': 1
        }
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(JIOSAAVN_BASE, params=params, headers=headers, timeout=10)
        data = res.json()
        results = []
        for album in data.get('results', []):
            results.append({
                'name': album.get('title', ''),
                'artists': {'primary': [{'name': album.get('music', '—')}]},
                'image': [{'url': album.get('image', '').replace('150x150', '500x500')}],
                'id': album.get('albumid', '')
            })
        return {'data': {'results': results}}
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/api/search/artists')
def search_artists():
    query = request.args.get('query', 'popular')
    limit = int(request.args.get('limit', 20))
    try:
        params = {
            '__call': 'search.getArtistResults',
            '_format': 'json',
            '_marker': '0',
            'api_version': '4',
            'ctx': 'web6dot0',
            'query': query,
            'n': limit,
            'p': 1
        }
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(JIOSAAVN_BASE, params=params, headers=headers, timeout=10)
        data = res.json()
        results = []
        for artist in data.get('results', []):
            results.append({
                'name': artist.get('name', ''),
                'image': [{'url': artist.get('image', '').replace('150x150', '500x500')}],
                'id': artist.get('id', '')
            })
        return {'data': {'results': results}}
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/api/albums')
def get_album():
    album_id = request.args.get('id', '')
    try:
        params = {
            '__call': 'content.getAlbumDetails',
            '_format': 'json',
            '_marker': '0',
            'api_version': '4',
            'ctx': 'web6dot0',
            'albumid': album_id
        }
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(JIOSAAVN_BASE, params=params, headers=headers, timeout=10)
        data = res.json()
        songs = []
        for song in data.get('list', []):
            audio_url = jiosaavn_get_song_url(song.get('encrypted_media_url', ''))
            songs.append({
                'name': song.get('song', ''),
                'artists': {'primary': [{'name': song.get('singers', '—')}]},
                'image': [{'url': song.get('image', '').replace('150x150', '500x500')}],
                'downloadUrl': [{'url': audio_url}]
            })
        return {'data': {'songs': songs}}
    except Exception as e:
        return {'error': str(e)}, 500
        
# -------------------- Jamendo Proxy (server-side)

# Hides JAMENDO client_id from frontend and centralizes requests.
import os
import requests

JAMENDO_BASE = 'https://api.jamendo.com/v3.0'


def _load_env_value_from_dotenv(key: str, dotenv_path: str) -> str | None:
    """
    Minimal .env loader (avoids extra dependencies).
    Only supports simple KEY=VALUE lines (ignores comments/blank lines).
    """
    try:
        if not os.path.exists(dotenv_path):
            return None

        with open(dotenv_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k == key:
                    return v
    except Exception:
        return None
    return None


def _jamendo_client_id():
    # Use OS env var first; fall back to Flask project's .env file.
    client_id = os.environ.get('JAMENDO_CLIENT_ID')
    if client_id:
        return client_id

    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    client_id = _load_env_value_from_dotenv("JAMENDO_CLIENT_ID", dotenv_path)
    if client_id:
        # Cache it in-process so subsequent calls don't re-read the file.
        os.environ["JAMENDO_CLIENT_ID"] = client_id
    return client_id


@app.route('/api/jamendo/tracks')
def jamendo_tracks():
    client_id = _jamendo_client_id()
    if not client_id:
        return {'error': 'JAMENDO_CLIENT_ID env var not set'}, 500

    try:
        limit = int(request.args.get('limit', 12))
    except ValueError:
        limit = 12

    tags = request.args.get('tags')
    order = request.args.get('order')
    include = request.args.get('include', 'musicinfo')
    audioformat = request.args.get('audioformat', 'mp32')

    params = {
        'client_id': client_id,
        'format': 'json',
        'limit': limit,
        'include': include,
        'audioformat': audioformat,
    }
    if tags:
        params['tags'] = tags
    if order:
        params['order'] = order

    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(f'{JAMENDO_BASE}/tracks/', params=params, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()

    results = []
    for t in data.get('results', []):
        results.append({
            'audio': t.get('audio'),
            'name': t.get('name'),
            'artist_name': t.get('artist_name'),
            'album_image': t.get('album_image'),
        })

    return {'results': results}


@app.route('/api/jamendo/albums')
def jamendo_albums():
    client_id = _jamendo_client_id()
    if not client_id:
        return {'error': 'JAMENDO_CLIENT_ID env var not set'}, 500

    try:
        limit = int(request.args.get('limit', 5))
    except ValueError:
        limit = 5

    order = request.args.get('order')

    params = {
        'client_id': client_id,
        'format': 'json',
        'limit': limit,
    }
    if order:
        params['order'] = order

    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(f'{JAMENDO_BASE}/albums/', params=params, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()

    results = []
    for a in data.get('results', []):
        results.append({
            'image': a.get('image') or a.get('album_image'),
            'name': a.get('name'),
            'artist_name': a.get('artist_name'),
        })

    return {'results': results}




if __name__ == '__main__':
    app.run(debug=True)

