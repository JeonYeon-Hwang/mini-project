from flask import Blueprint, jsonify, request
from db import db

user_bp = Blueprint('user', __name__)

@user_bp.route('/food/profile', methods=['GET'])
def get_user_slack():
    nickname = request.args.get('nickname')
    user = db.users.find_one({'nickname': nickname})
    if user:
        return jsonify({'result': 'success', 'slack_url': user['slack_url']})
    return jsonify({'result': 'fail', 'message': '사용자를 찾을 수 없습니다'})