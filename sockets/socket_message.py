from flask_socketio import SocketIO, emit
from flask import request

host = "0.0.0.0"
port = 12345


socketio = SocketIO()
messages = []

@socketio.on('message')
def handle_message(data):
    msg = {'text': data['text'], 'userId': data['userId'], 'nickname': data.get('nickname', '')}
    messages.append(msg)
    emit('message', msg, broadcast=True)