from flask import Blueprint, current_app, abort, request, session, jsonify
from CTFd.utils.security.auth import login_user
from CTFd.models import db, Users
from itsdangerous import URLSafeTimedSerializer

def load(app):
    token_login_blueprint = Blueprint('token_login', __name__)

    @token_login_blueprint.route('/api/token-login', methods=['POST'])
    def token_login():
        secret = current_app.secret_key
        if not secret:
           abort(500)

        data = requst.form or request.get_json()
        token = data.get('token', None)
        if not token:
            return jsonify(success=False, data={
                'message': 'Token not found',
                'keys': token.keys(),
            }), 403

        serializer = URLSafeTimedSerializer(secret)

        try:
            tokenized_username = serializer.loads(token, max_age=30)
        except SignatureExpired:
            current_app.logger.debug('Token has expired')
            return jsonify(success=False, data={
                'message': 'Token expired',
            }), 403
        except BadSignature:
            current_app.logger.debug('Bad Token Signature')
            return jsonify(success=False, data={
                'message': 'Token not found',
                'message': 'Bad signature',
            }), 403

        user = Users.query.filter_by(name=tokenized_username)
        if not user:
            return jsonify(success=False, data={
                'message': 'Bad username',
            }), 403

        session.regenerate()

        login_user(user)
        db.session.close()
        return jsonify(success=True)

    app.register_blueprint(token_login_blueprint)
