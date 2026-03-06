from flask import Flask, render_template, jsonify, request, make_response, redirect, url_for

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

def get_current_user():
   token = request.cookies.get("mytoken")
   if not token:
      return None

   try:
      payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
      user = db.users.find_one({"id": payload["id"]})
      return user
   except jwt.ExpiredSignatureError:
      return None
   except jwt.InvalidTokenError:
      return None

# 기본 화면 api
@app.route('/')
def home():
   # 사용자 인증 확인
   user = get_current_user()

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

   user = get_current_user()
   
   return render_template('index.html', 
                           cards = cards , 
                           snapshot_time = now,
                           cursor = last_card_id,
                           user=user,
                           )




@app.route('/food/card/mylist')
def my_card_list():
   user = get_current_user()

   if not user:
      return render_template('index.html', cards=[], user=None)

   my_nickname = user.get('nickname')

   cards = list(db.cards.find({'card_members': my_nickname})
               .sort([('is_alive', -1), ('card_duedate', 1)]))

   for card in cards:
      card['_id'] = str(card['_id'])
      card['card_duedate'] = time.strftime('%Y-%m-%d %H:%M', time.localtime(card['card_duedate']))
      card['card_type'] = FOOD_IMAGE_MAP.get(card.get('card_type', ''))

   return render_template('index.html',
                           cards=cards,
                           user=user,
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
      response.set_cookie('mytoken', token, httponly=True, samesite='Lax')
      return response
   else:
      return jsonify({'result': 'fail', 'message': '아이디 또는 비밀번호가 틀렸습니다'})



#닉네임
@app.route('/food/get_nickname', methods=['GET'])
def get_nickname():
   token_receive = request.cookies.get('access_token')
   
   try:
      # 토큰 해독
      payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
      user_id = payload['id']  
      user = db.users.find_one({'id': user_id}, {'_id': False, 'pw': False})
      return jsonify({'result': 'success', 'nickname': user['nickname']})
   
   except jwt.ExpiredSignatureError:
      # 토큰 만료됨 (2시간 지남)
      return jsonify({'result': 'fail', 'message': '로그인이 만료됐습니다'})
   
   except jwt.InvalidTokenError:
      # 토큰 위조됨
      return jsonify({'result': 'fail', 'message': '유효하지 않은 토큰입니다'})


# 로그아웃 API
@app.route('/logout', methods=['POST'])
def logout():
   """로그아웃: mytoken 쿠키 삭제 후 메인 페이지로 리다이렉트"""
   response = make_response(redirect('/'))
   response.set_cookie('mytoken', '', expires=0)
   return response



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

@app.route('/food/card/edit', methods=['POST'])
def edit_card():
   token_receive = request.cookies.get('mytoken')

   # 1. 토큰으로 user_id 찾기
   try:
      payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
      user_id_receive = payload['id']
   except jwt.ExpiredSignatureError:
      return jsonify({'result' : 'fail', 'message' : '로그인이 만료됐습니다'})
   except jwt.InvalidTokenError:
      return jsonify({'result': 'fail', 'message': '유효하지 않은 토큰 입니다'})

   card_id_receive = request.form.get('card_id')
   card_title_receive = request.form['card_title_give']
   card_content_receive = request.form['card_content_give']
   card_duedate_receive = request.form['card_duedate_give']
   card_url_receive = request.form['card_url_give']
   card_price_receive = request.form['card_price_give']
   card_type_receive = request.form['card_type_give']

   clean_date = card_duedate_receive.replace('T', ' ')
   try:
      if clean_date.count(':') == 2:
         due_timestamp = int(time.mktime(time.strptime(clean_date, '%Y-%m-%d %H:%M:%S')))
      else:
         due_timestamp = int(time.mktime(time.strptime(clean_date, '%Y-%m-%d %H:%M')))
   except ValueError:
       return jsonify({'result': 'fail', 'message': '날짜 형식이 올바르지 않습니다.'})

   # 작성자 검증
   card_data = db.cards.find_one({'_id': ObjectId(card_id_receive)})
   if not card_data:
      return jsonify({'result': 'fail', 'message': '존재하지 않는 글입니다.'})
   if card_data.get('user_id') != user_id_receive:
      return jsonify({'result': 'fail', 'message': '수정 권한이 없습니다 (작성자 전용).'})

   update_data = {
      'card_title' : card_title_receive,
      'card_text' : card_content_receive,
      'card_duedate' : due_timestamp,
      'card_url' : card_url_receive,
      'card_price' : card_price_receive,
      "card_type" : card_type_receive,
   }

   db.cards.update_one({'_id': ObjectId(card_id_receive)}, {'$set': update_data})
   return jsonify({'result' : 'success', 'message': '수정되었습니다!'})

@app.route('/food/card/delete', methods=['POST'])
def delete_card():
   token_receive = request.cookies.get('mytoken')

   # 1. 토큰으로 user_id 찾기
   try:
      payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
      user_id_receive = payload['id']
   except jwt.ExpiredSignatureError:
      return jsonify({'result' : 'fail', 'message' : '로그인이 만료됐습니다'})
   except jwt.InvalidTokenError:
      return jsonify({'result': 'fail', 'message': '유효하지 않은 토큰 입니다'})

   card_id_receive = request.form.get('card_id')

   # 작성자 검증
   card_data = db.cards.find_one({'_id': ObjectId(card_id_receive)})
   if not card_data:
      return jsonify({'result': 'fail', 'message': '존재하지 않는 글입니다.'})
   if card_data.get('user_id') != user_id_receive:
      return jsonify({'result': 'fail', 'message': '권한이 없습니다.'})

   db.cards.delete_one({'_id': ObjectId(card_id_receive)})
   return jsonify({'result' : 'success', 'message': '삭제되었습니다.'})
   
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
   
   # 소켓 통신
   socketio.emit('new_message', {
      'text': comment_receive,
      'userId': user_id,
      'nickname': nickname
   }, to=card_id_receive)

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
   return jsonify({'result': 'success', 'msg': '가입되었습니다!'})



#^^특정 카드에서 탈퇴 api
@app.route('/food/exit', methods=['POST'])
def exit_club():
   token_receive = request.cookies.get('mytoken')
   card_id_receive = request.form['card_id_give']
   # 강퇴 대상이 넘어왔는지 확인 (선택적 파라미터)
   target_nickname_receive = request.form.get('target_nickname')

   # 1. 토큰으로 내(요청자) user_id 찾기
   try:
      payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
      user_id = payload['id']
   except jwt.ExpiredSignatureError:
      return jsonify({'result': 'fail', 'message': '로그인이 만료됐습니다'})
   except jwt.InvalidTokenError:
      return jsonify({'result': 'fail', 'message': '유효하지 않은 토큰입니다'})

   # 2. 내 닉네임 조회
   user_data = db.users.find_one({'id': user_id})
   nickname = user_data.get('nickname')

   # 3. 삭제 대상 판별
   if target_nickname_receive and target_nickname_receive != nickname:
      card = db.cards.find_one({'_id': ObjectId(card_id_receive)})
      if not card or card['user_id'] != user_id:
         return jsonify({'result': 'fail', 'message': '권한이 없습니다.'})
      remove_nickname = target_nickname_receive
   else:
      # 스스로 탈퇴하는 경우
      remove_nickname = nickname

   # 4. 멤버 리스트에서 제거
   db.cards.update_one(
      {'_id': ObjectId(card_id_receive)},
      {'$pull': {'card_members': remove_nickname}}
   )
   return jsonify({'result': 'success', 'message': '탈퇴되었습니다.'})
# 내가 가입한 팟 목록 조회
@app.route('/food/my_cards', methods=['GET'])
def get_my_cards():
   user = get_current_user()
   if not user:
      return jsonify({'result': 'fail', 'message': '로그인이 필요합니다'})

   nickname = user['nickname']

   # 내가 가입한 팟 조회 (card_members 배열에 내 닉네임이 포함된 팟)
   my_cards = list(db.cards.find({
      'card_members': nickname
   }).sort([('is_alive', -1), ('card_duedate', 1)]))

   # 데이터 포맷팅 (기존 show_cards()와 동일한 방식)
   for card in my_cards:
      card['_id'] = str(card['_id'])
      if card.get('card_duedate'):
         card['card_duedate'] = time.strftime('%Y-%m-%d %H:%M', time.localtime(card['card_duedate']))
      if card.get('card_type'):
         card['card_type'] = FOOD_IMAGE_MAP.get(card['card_type'])

   return jsonify({'result': 'success', 'cards': my_cards})

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
   now = int(time.time()) + (9 * 3600)
   result = db.cards.update_many(
        {'card_duedate': {'$lte': now}},
        {'$set': {'is_alive': False}}
   )
   print(f"현재 시간: {now}") 
   print(f"매칭된 문서 개수: {result.matched_count}")
   print(f"실제 수정된 문서 개수: {result.modified_count}")
         


scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_job, 'interval', seconds=120)
scheduler.start()



if __name__ == '__main__':
   #app.run('0.0.0.0', port=5001, debug=True)

   #소켓 실행
    socketio.run(app, '0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)
