import os
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Configure session cookies
app.config['SESSION_COOKIE_NAME'] = 'login_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

users = {
    'admin': {
        'password': 'admin123',
        'email': 'admin@example.com',
        'name': 'Administrator'
    },
    'testuser': {
        'password': 'password123',
        'email': 'test@example.com',
        'name': 'Test User'
    }
}

remember_tokens = {}

def create_remember_token(username):
    token = secrets.token_urlsafe(32)
    remember_tokens[token] = {
        'username': username,
        'created': datetime.now()
    }
    return token

def verify_remember_token(token):
    if token in remember_tokens:
        token_data = remember_tokens[token]
        if datetime.now() - token_data['created'] < timedelta(days=30):
            return token_data['username']
        else:
            del remember_tokens[token]
    return None

@app.before_request
def check_remember_me():
    if 'username' not in session:
        remember_token = request.cookies.get('remember_token')
        if remember_token:
            username = verify_remember_token(remember_token)
            if username:
                session['username'] = username
                session['logged_in_at'] = datetime.now().isoformat()
                session.permanent = True

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('welcome'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') == 'on'
        
        if username in users and users[username]['password'] == password:
            session['username'] = username
            session['user_email'] = users[username]['email']
            session['user_name'] = users[username]['name']
            session['logged_in_at'] = datetime.now().isoformat()
            
            if remember_me:
                session.permanent = True
                token = create_remember_token(username)
                response = make_response(redirect(url_for('welcome')))
                response.set_cookie(
                    'remember_token',
                    token,
                    max_age=30*24*60*60,
                    httponly=True,
                    samesite='Lax'
                )
                return response
            else:
                session.permanent = False
                return redirect(url_for('welcome'))
        else:
            return render_template('login.html', error=True)
    
    return render_template('login.html', error=False)

@app.route('/welcome')
def welcome():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session.get('username')
    user_name = session.get('user_name', username)
    logged_in_at = session.get('logged_in_at')
    is_permanent = session.permanent
    
    session_age = None
    if logged_in_at:
        login_time = datetime.fromisoformat(logged_in_at)
        session_age = str(datetime.now() - login_time).split('.')[0]
    
    return render_template(
        'welcome.html',
        username=username,
        user_name=user_name,
        session_age=session_age,
        is_permanent=is_permanent
    )

@app.route('/logout')
def logout():
    session.clear()
    response = make_response(redirect(url_for('login')))
    response.set_cookie('remember_token', '', expires=0)
    return response

@app.route('/recover', methods=['GET', 'POST'])
def recover():
    if request.method == 'POST':
        email = request.form.get('email')
        return render_template('recover.html', success=True)
    return render_template('recover.html', success=False)

@app.route('/session-info')
def session_info():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    info = {
        'username': session.get('username'),
        'user_name': session.get('user_name'),
        'user_email': session.get('user_email'),
        'logged_in_at': session.get('logged_in_at'),
        'is_permanent': session.permanent,
        'session_id': request.cookies.get('login_session', 'Not set'),
        'remember_token': 'Set' if request.cookies.get('remember_token') else 'Not set'
    }
    
    return render_template('session_info.html', info=info)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
    #app.run(debug=True, host='127.0.0.1', port=5000)
