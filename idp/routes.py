import codecs
import hashlib
import uuid
import email_validator
from functools import wraps

from flask import Blueprint, request, session, url_for, render_template, redirect, jsonify, abort
from authlib.integrations.flask_oauth2 import current_token
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .models import User, db
from .oauth2 import authorization, require_oauth
from .tasks import send_code, get_user_by_display_name

bp = Blueprint('home', __name__)


def current_user():
    if 'user_id' in session:
        return User.query.filter_by(user_id=session['user_id']).first()
    return None


def split_by_crlf(s):
    return [v for v in s.splitlines() if v]


ratelimit = Limiter(get_remote_address, strategy="moving-window")


@bp.route('/login', methods=('GET', 'POST'))
@ratelimit.limit("1/second", exempt_when=lambda: request.method != "POST")
@ratelimit.limit("5/minute", exempt_when=lambda: request.method != "POST")
def login():
    if request.method == 'POST':
        display_name = request.form.get('username')
        if not display_name:
            return render_template('login.html')
        user = get_user_by_display_name(display_name)

        if not user or user.disabled_login:
            return render_template('login.html', username=display_name,
                                   error="Invalid username (User does not exist, is not part of the group or may be disabled)")

        code = request.form.get('code')
        if not code:
            if user.token is None:  # Only send code if a user has no current code
                send_code.delay(user.user_id)
            return render_template('login.html', username=display_name)

        if not user or not user.is_code_valid(code):
            return render_template('login.html', error="Invalid code")

        session['user_id'] = user.user_id

        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect('/')
    else:
        return render_template('login.html')


def login_required(user_id: str = None):
    def decorator(f):
        @wraps(f)
        def wrap(*args, **kwargs):
            if 'user_id' in session:
                user = User.query.filter_by(user_id=session['user_id']).first()
                if user_id and str(user.user_id) != user_id:
                    return abort(403)
                return f(user, *args, **kwargs)
            return redirect(url_for('home.login', next=request.url))

        return wrap

    return decorator


@bp.route('/logout')
def logout():
    del session['user_id']
    return redirect('/')


# @bp.route('/create_client', methods=('GET', 'POST'))
# def create_client():
#     user = current_user()
#     if not user:
#         return redirect('/')
#     if request.method == 'GET':
#         return render_template('create_client.html')
#
#     client_id = gen_salt(24)
#     client_id_issued_at = int(time.time())
#     client = OAuth2Client(
#         client_id=client_id,
#         client_id_issued_at=client_id_issued_at
#     )
#
#     form = request.form
#     client_metadata = {
#         "client_name": form["client_name"],
#         "client_uri": form["client_uri"],
#         "grant_types": split_by_crlf(form["grant_type"]),
#         "redirect_uris": split_by_crlf(form["redirect_uri"]),
#         "response_types": split_by_crlf(form["response_type"]),
#         "scope": form["scope"],
#         "token_endpoint_auth_method": form["token_endpoint_auth_method"]
#     }
#     client.set_client_metadata(client_metadata)
#
#     if form['token_endpoint_auth_method'] == 'none':
#         client.client_secret = ''
#     else:
#         client.client_secret = gen_salt(48)
#
#     db.session.add(client)
#     db.session.commit()
#     return redirect('/')


@bp.route('/admin', methods=['GET'])
@login_required(user_id="c58b4d88-4a7b-43c5-a775-12211788adf5")
def admin(user):
    return render_template('admin.html', user=user, users=User.query.all())


@bp.route('/admin/toggle_login/<user_id>', methods=['GET'])
@login_required(user_id="c58b4d88-4a7b-43c5-a775-12211788adf5")
def toggle_login(user, user_id: str):
    uid = uuid.UUID(user_id)
    user: User = User.query.get(uid)
    user.disabled_login = not user.disabled_login
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('.admin'))


@bp.route('/admin/reset_token/<user_id>', methods=['GET'])
@login_required(user_id="c58b4d88-4a7b-43c5-a775-12211788adf5")
def reset_token(user, user_id: str):
    uid = uuid.UUID(user_id)
    user: User = User.query.get(uid)
    user.token = None
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('.admin'))


@bp.route('/oauth/authorize', methods=['GET'])
@login_required()
def authorize(user):
    del session['user_id']
    return authorization.create_authorization_response(grant_user=user)


@bp.route('/oauth/token', methods=['POST'])
def issue_token():
    return authorization.create_token_response()


@bp.route('/oauth/revoke', methods=['POST'])
def revoke_token():
    return authorization.create_endpoint_response('revocation')


@bp.route('/api/me')
@require_oauth('profile')
def api_me():
    user: User = User.query.filter_by(user_id=current_token.user_id).first()
    email = f"{codecs.encode(user.display_name, 'idna').decode('utf-8')}@rusk.alliance.rocks"
    try:
        email_validator.validate_email(email)
    except email_validator.EmailNotValidError:
        email = hashlib.md5(user.display_name.encode('utf-8')).hexdigest() + "@rusk.alliance.rocks"
    return jsonify(user_id=str(user.user_id), email=email, given_name=user.display_name)
