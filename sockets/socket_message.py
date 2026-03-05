from flask_socketio import SocketIO, emit, join_room
from flask import request

host = "0.0.0.0"
port = 12345

socketio = SocketIO()
messages = []

@socketio.on('join')
def on_join(data):
    room = data.get('room')
    if room:
        join_room(room)

@socketio.on('message')
def handle_message(data):
    msg = {'text': data['text'], 'userId': data['userId'], 'nickname': data.get('nickname', '')}
    room = data.get('room')
    messages.append(msg)
    if room:
        emit('message', msg, to=room)
    else:
        emit('message', msg, broadcast=True)