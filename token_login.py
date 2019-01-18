from flask import Blueprint, current_app, abort, request, session
from CTFd.utils.security.auth import login_user
from CTFd.modles import db, Users
from itsdangerous import URLSafeTimedSerializer

def load(app):
    token_login = Blueprint('token_login', __name__)

    @token_login.route('/api/token-login', methods=['POST'])
    def token_login():
        secret = current_app.secret_key
        if not secret:
           abort(500)

        data = requst.form or request.get_json()
        token = request.get('token', None)
        if not token:
            abort(403)

        serializer = URLSafeTimedSerializer(secret)

        try:
            tokenized_username = serializer.loads(token, max_age=30)
        except SignatureExpired:
            current_app.logger.debug('Token has expired')
            abort(403)
        except BadSignature:
            current_app.logger.debug('Bad Token Signature')
            abort(403)

        user = Users.query.filter_by(name=tokenized_username)
        if not user:
            abort(403)

        session.regenerate()

        login_user(user)
        db.session.close()
        return {
            'success': True,
        }
