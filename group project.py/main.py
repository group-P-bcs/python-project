from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'
socketio = SocketIO(app)

# Dummy database for demonstration purposes
users = [
    {'username': 'admin', 'password': generate_password_hash('admin'), 'role': 'admin'},
    {'username': 'user1', 'password': generate_password_hash('password1'), 'role': 'student'},
    {'username': 'user2', 'password': generate_password_hash('password2'), 'role': 'student'}
]

candidates = [
    {'id': 1, 'name': 'Candidate 1', 'votes': 0},
    {'id': 2, 'name': 'Candidate 2', 'votes': 0}
]

def authenticate(username, password):
    user = next((u for u in users if u['username'] == username), None)
    if user and check_password_hash(user['password'], password):
        return user
    return None

def authorize(role):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if 'username' in session:
                user = next((u for u in users if u['username'] == session['username']), None)
                if user and user['role'] == role:
                    return func(*args, **kwargs)
            return redirect(url_for('login'))
        return wrapper
    return decorator

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = authenticate(username, password)
        if user:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        users.append({'username': username, 'password': password, 'role': 'student'})
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@authorize('student')
def dashboard():
    return render_template('dashboard.html', username=session['username'], candidates=candidates)

@app.route('/admin/dashboard')
@authorize('admin')
def admin_dashboard():
    return render_template('admin_dashboard.html', username=session['username'], candidates=candidates)

@app.route('/vote', methods=['POST'])
@authorize('student')
def vote():
    user = next((u for u in users if u['username'] == session['username']), None)
    if user and not user['voted']:
        candidate_id = int(request.form['candidate'])
        candidate = next((c for c in candidates if c['id'] == candidate_id), None)
        if candidate:
            candidate['votes'] += 1
            user['voted'] = True
            emit('vote_update', {'candidate_id': candidate_id, 'votes': candidate['votes']}, broadcast=True)
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    socketio.run(app, debug=True)
