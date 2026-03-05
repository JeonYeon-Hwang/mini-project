from flask import Flask, render_template, jsonify, request, make_response

#라우터 임포트
from sockets.socket_message import socketio
from routes.message import message_bp
from routes.user import user_bp
from routes.cards import food_bp;

#db 임포트
from db import db


app = Flask(__name__)

#외부 등록
socketio.init_app(app)
app.register_blueprint(message_bp)
app.register_blueprint(user_bp)
app.register_blueprint(food_bp)

#추가함
import jwt
import datetime
import hashlib
SECRET_KEY = "welcometothejungle"


import time
import requests

from bs4 import BeautifulSoup
from bson.objectid import ObjectId
from apscheduler.schedulers.background import BackgroundScheduler
from contents import FOOD_IMAGE_MAP



# 서버에서 최초로 가져올 수 있는 카드 수
MINIMUM_CARD_LIMIT = 15

# 기본 화면 api
@app.route('/')
def home():
   category = request.args.get('category')
   query = {'card_type': category} if category else {}
   cards = list(db.cards.find(query)
               .sort([('is_alive', -1), ('card_duedate', 1)]) 
               .limit(MINIMUM_CARD_LIMIT))

   now = int(time.time())
   last_card_id = str(cards[-1].get('_id'))

   for card in cards:
      card['_id'] = str(card['_id'])
      card['card_duedate'] = time.strftime('%Y-%m-%d %H:%M', time.localtime(card['card_duedate']))
      card['card_type'] = FOOD_IMAGE_MAP.get(card['card_type'])
   
   return render_template('index.html', 
                           cards = cards , 
                           snapshot_time = now,
                           cursor = last_card_id 
                           )



#추가함 회원가입 api
@app.route('/food/signin', methods=['POST'])
def signin():
   print("회원가입 실행")
   id_receive = request.form['id_give']
   pw_receive = request.form['pw_give']
   nickname_receive = request.form['nickname_give']
   slack_url_receive = request.form['slack_url_give']

   pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

   existing_user = db.users.find_one({'id': id_receive})
   if existing_user:
      return jsonify({'result': 'fail', 'message': '이미 존재하는 아이디입니다'})

   user = {
      'id': id_receive,
      'pw': pw_hash,
      'nickname': nickname_receive,
      'slack_url': slack_url_receive
   }
   db.users.insert_one(user)
   return jsonify({'result': 'success'})



#추가함 로그인 api
@app.route('/food/login', methods=['POST'])
def login():
   id_receive = request.form['id_give']
   pw_receive = request.form['pw_give']

   pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
   user = db.users.find_one({'id': id_receive, 'pw': pw_hash})

   if user:
      token = jwt.encode(
         {
            'id': id_receive,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
         },
         SECRET_KEY,
         algorithm='HS256'
      )
      response = make_response(jsonify({'result': 'success' , 'token' : token }))
      response.set_cookie('access_token', token, httponly=True, samesite='Lax')
      return response
   else:
      return jsonify({'result': 'fail', 'message': '아이디 또는 비밀번호가 틀렸습니다'})



#토큰 검증 확인
@app.route('/food/identification', methods=['POST'])
def identification():
   token_receive = request.form['token_give']
   
   try:
      # 토큰 해독
      payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
      find_id = payload['id']  # 토큰 안에서 아이디 꺼내기
      return jsonify({'result': 'success', 'id': find_id})
   
   except jwt.ExpiredSignatureError:
      # 토큰 만료됨 (2시간 지남)
      return jsonify({'result': 'fail', 'message': '로그인이 만료됐습니다'})
   
   except jwt.InvalidTokenError:
      # 토큰 위조됨
      return jsonify({'result': 'fail', 'message': '유효하지 않은 토큰입니다'})



#카드를 등록하는 api
@app.route('/food/card/create', methods=['POST'])
def create_card():
   token_receive = request.cookies.get('mytoken')

   # 1. 토큰으로 user_id 찾기
   try:
      payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
      user_id_receive = payload['id']
   except jwt.ExpiredSignatureError:
      return jsonify({'result' : 'fail', 'message' : '로그인이 만료됐습니다'})
   except jwt.InvalidTokenError:
      return jsonify({'result': 'fail', 'massage': '유효하지 않은 토큰 입니다'})

   card_title_receive = request.form['card_title_give']
   card_content_receive = request.form['card_content_give']
   # 1. 프론트에서 보낸 문자열 받기 ("2026-03-31T23:59")
   card_duedate_receive = request.form['card_duedate_give']
   card_url_receive = request.form['card_url_give']
   card_price_receive = request.form['card_price_give']
   card_type_receive = request.form['card_type_give']

   now = int(time.time())
   clean_date = card_duedate_receive.replace('T', ' ')
   due_timestamp = int(time.mktime(time.strptime(clean_date, '%Y-%m-%d %H:%M')))
   first_member = db.users.find_one({'id': user_id_receive}).get('nickname')

   card = {
      'user_id' : user_id_receive,
      'card_title' : card_title_receive,
      'card_text' : card_content_receive,
      'card_duedate' : due_timestamp,
      'card_created_date' : now,
      'card_members' : [ first_member ],
      'card_url' : card_url_receive,
      'card_price' : card_price_receive,
      "card_type" : card_type_receive,
      'is_alive' : True
   }

   db.cards.insert_one(card)
   return jsonify({'result' : 'success'})



#모든 카드를 보여주는 api
@app.route('/food/card/show', methods=['GET'])
def show_cards():
   all_cards = list(db.cards.find({}).sort('card_duedate', 1))  
   all_cards.sort(key=lambda x: x.get('is_alive', False), reverse=True)
   
   now = int(time.time())
   last_card_id = str(all_cards[-1].get('_id'))

   for card in all_cards:
      if '_id' in card:
         card['_id'] = str(card['_id'])
         card['card_duedate'] = time.strftime('%Y-%m-%d %H:%M', time.localtime(card['card_duedate']))
         card['card_type'] = FOOD_IMAGE_MAP.get(card['card_type'])

   return jsonify({'result' : 'success', 
                   'cards' : all_cards, 
                   'snapshot_time' : now,
                   'cursor' : last_card_id})
   # return render_template('index.html', cards = all_cards)




#특정 카드의 댓글을 보여주는 api
@app.route('/food/<string:card_id>/comments', methods=['GET'])
def show_card_comments(card_id):
   query =  {'card_id': card_id}
   dedicated_comments = list(db.comments.find(query).sort('comment_sent_time', 1))
   
   for comments in dedicated_comments:
      if '_id' in comments:
         comments['_id'] = str(comments['_id'])
         comments['comment_sent_time'] = time.strftime('%Y-%m-%d %H:%M', time.localtime(comments['comment_sent_time']))

   return jsonify({'result' : dedicated_comments})
   # return render_template('index.html', comments = dedicated_comments)



#댓글을 등록하는 api
@app.route('/food/post/comments', methods=['POST'])
def create_comments():
   token_receive = request.cookies.get('mytoken')

   # 1. 토큰으로 user_id 찾기
   try:
      payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
      user_id = payload['id']
   except jwt.ExpiredSignatureError:
      return jsonify({'result': 'fail', 'message': '로그인이 만료됐습니다'})
   except jwt.InvalidTokenError:
      return jsonify({'result': 'fail', 'message': '유효하지 않은 토큰입니다'})

   # 2. user_id로 닉네임 찾기
   user_data = db.users.find_one({'id': user_id})
   nickname = user_data.get('nickname')

   card_id_receive = request.form['card_id_give']
   comment_receive = request.form['comment_give']
   now = int(time.time())

   comment = {
      'card_id': card_id_receive,
      'user_id': user_id,
      'nickname': nickname,
      'comment_sent_time': now,
      'comment_text': comment_receive
   }

   db.comments.insert_one(comment)
   return jsonify({'result': 'success', 'message': '댓글이 등록됐습니다!'})



#^^특정 카드에 가입하는 api, 이미 가입 되었을 시 => 실패 메시지 발송
@app.route('/food/join', methods=['POST'])
def join_club():
   card_id_receive = request.form['card_id_give']
   token_receive = request.cookies.get('mytoken')

   try:
      payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
      user_id_receive = payload['id']
   except jwt.ExpiredSignatureError:
      return jsonify({'result': 'fail', 'message': '로그인이 만료됐습니다'})
   except jwt.InvalidTokenError:
      return jsonify({'result': 'fail', 'message': '유효하지 않은 토큰입니다'})

   card = db.cards.find_one({'_id': ObjectId(card_id_receive)})
   user_data = db.users.find_one({'id': user_id_receive}, {'_id': False, 'pw': False})
   nickname = user_data.get('nickname')

   if nickname in card.get('card_members', []):
      return jsonify({'result': 'fail', 'msg': '이미 가입된 유저입니다.'})

   db.cards.update_one(
      {'_id': ObjectId(card_id_receive)},
      {'$push': {'card_members': nickname}}
   )
   return jsonify({'result': 'success', 'msg': '가입이 완료되었습니다!'})



#^^특정 카드에서 탈퇴하는 api
@app.route('/food/exit', methods=['POST'])
def exit_club():
   token_receive = request.form['token_give']
   card_id_receive = request.form['card_id_give']

   # 1. 토큰으로 user_id 찾기
   try:
      payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
      user_id = payload['id']
   except jwt.ExpiredSignatureError:
      return jsonify({'result': 'fail', 'message': '로그인이 만료됐습니다'})
   except jwt.InvalidTokenError:
      return jsonify({'result': 'fail', 'message': '유효하지 않은 토큰입니다'})

   # 2. user_id로 닉네임 찾기
   user_data = db.users.find_one({'id': user_id})
   nickname = user_data.get('nickname')

   db.cards.update_one(
      {'_id': ObjectId(card_id_receive)},
      {'$pull': {'card_members': nickname}}
   )
   return jsonify({'result': 'success', 'message': '탈퇴가 완료됐습니다!'})



@app.route('/food/show_more/<int:page_num>')
def show_more(page_num):
   limit = 9
   skip_value = (page_num - 1) * limit
   
   cards = list(db.cards.find({})
               .sort([('is_alive', -1), ('card_duedate', 1)]) 
               .skip(skip_value)   
               .limit(limit))
   
   for card in cards:
      card['_id'] = str(card['_id'])
      if card.get('card_duedate'):
         card['card_duedate'] = time.strftime('%Y-%m-%d %H:%M', time.localtime(card['card_duedate']))
      if card.get('card_type'):
         card['card_type'] = FOOD_IMAGE_MAP.get(card['card_type'])

   has_more = len(cards) == limit

   return jsonify({
      "result": "success", 
      "cards": cards, 
      "has_more": has_more
   })




#========== 다음은 기능용 메서드 입니다 ===========#



#스캐줄러 메서드 입니다
def scheduled_job():
   print("스캐줄링 작동")

   now = int(time.time())
   db.cards.update_many(
      {'card_duedate' : {'$lte' : now }},
      {'$set' : { 'is_alive' : False}}
   )
         


scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_job, 'interval', seconds=180)
scheduler.start()



if __name__ == '__main__':
   #app.run('0.0.0.0', port=5001, debug=True)

   #소켓 실행
    socketio.run(app, '0.0.0.0', port=5001, debug=True)
