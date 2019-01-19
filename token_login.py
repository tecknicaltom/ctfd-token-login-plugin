from flask import Blueprint, current_app, abort, request, session, jsonify
from CTFd.models import db, Users
from CTFd.plugins import bypass_csrf_protection
from CTFd.utils.logging import log
from CTFd.utils.security.auth import login_user
from itsdangerous import URLSafeTimedSerializer

def load(app):
    token_login_blueprint = Blueprint('token_login', __name__)

    # make sure logging handlers were installed, see #839
    import logging
    if not logging.getLogger('logins').handlers:
        from CTFd.utils.logging import init_logs
        init_logs(current_app)

    @bypass_csrf_protection
    @token_login_blueprint.route('/api/token-login', methods=['POST'])
    def token_login():
        secret = current_app.secret_key
        if not secret:
           abort(500)

        data = requst.form or request.get_json()
        token = data.get('token', None)
        if not token:
            log('logins', "[{date}] {ip} Token not found ({keys})", keys=",".join(data.keys()))
            abort(403)

        serializer = URLSafeTimedSerializer(secret)

        try:
            tokenized_username = serializer.loads(token, max_age=30)
        except SignatureExpired:
            log('logins', "[{date}] {ip} Token has expired")
            abort(403)
        except BadSignature:
            log('logins', "[{date}] {ip} Bad Token Signature")
            abort(403)

        user = Users.query.filter_by(name=tokenized_username)
        if not user:
            log('logins', "[{date}] {ip} Bad username")
            abort(403)

        session.regenerate()

        login_user(user)
        db.session.close()
        return jsonify(success=True)

    app.register_blueprint(token_login_blueprint)
