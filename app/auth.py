from flask import session, redirect, url_for, g
from functools import wraps
from app.models import User

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('main.login'))
        g.current_user = get_current_user()
        return f(*args, **kwargs)
    return decorated_function