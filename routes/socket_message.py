from flask import Blueprint, jsonify
from sockets.socket_message import messages

message_bp = Blueprint('message', __name__)

@message_bp.route('/messages', methods=['GET'])
def get_messages():
    return jsonify({'result': 'success', 'messages': messages})
