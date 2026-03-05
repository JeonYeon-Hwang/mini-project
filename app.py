from flask import Flask, render_template, jsonify, request
app = Flask(__name__)

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
from pymongo import MongoClient
client = MongoClient('mongodb://korobuster001:blueskY114@52.79.125.68', 27017)
db = client.dbjungle



# 기본 화면 api
@app.route('/')
def home():
   return render_template('index.html')



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
      return jsonify({'result': 'success', 'token': token})
   else:
      return jsonify({'result': 'fail', 'message': '아이디 또는 비밀번호가 틀렸습니다'})



#카드를 등록하는 api
@app.route('/food/card/create', methods=['POST'])
def create_card():
   user_id_receive = request.form['user_id_give']
   card_title_receive = request.form['card_title_give']
   card_content_receive = request.form['card_content_give']
   # 1. 프론트에서 보낸 문자열 받기 ("2026-03-31T23:59")
   card_duedate_receive = request.form['card_duedate_give']
   card_url_receive = request.form['card_url_give']

   now = int(time.time())
   clean_date = card_duedate_receive.replace('T', ' ')
   due_timestamp = int(time.mktime(time.strptime(clean_date, '%Y-%m-%d %H:%M')))

   card = {
      'user_id' : user_id_receive,
      'card_title' : card_title_receive,
      'card_text' : card_content_receive,
      'card_duedate' : due_timestamp,
      'card_created_date' : now,
      'card_members' : [ ],
      'card_url' : card_url_receive,
      'is_alive' : True
   }

   db.cards.insert_one(card)
   return jsonify({'result' : 'success'})



#모든 카드를 보여주는 api
@app.route('/food/card/show', methods=['GET'])
def show_cards():
   all_cards = list(db.cards.find({}).sort('card_created_date', 1))  
   
   for card in all_cards:
      if '_id' in card:
         card['_id'] = str(card['_id'])
         card['card_duedate'] = time.strftime('%Y-%m-%d %H:%M', time.localtime(card['card_duedate']))

   # return jsonify({'result' : 'success', 'cards' : all_cards})
   return render_template('index.html', cards = all_cards)



#특정 카드의 댓글을 보여주는 api
@app.route('/food/<string:card_id>/comments', methods=['GET'])
def show_card_comments(card_id):
   query =  {'card_id': card_id}
   dedicated_comments = list(db.comments.find(query).sort('comment_sent_time', 1))
   
   for comments in dedicated_comments:
      if '_id' in comments:
         comments['_id'] = str(comments['_id'])
         comments['comment_sent_time'] = time.strftime('%Y-%m-%d %H:%M', time.localtime(comments['comment_sent_time']))

   # return jsonify({'result' : dedicated_comments})
   return render_template('index.html', comments = dedicated_comments)



#댓글을 등록하는 api
@app.route('/food/post/comments', methods=['POST'])
def create_comments():
   card_id_receive = request.form['card_id_give']
   user_id_receive = request.form['user_id_give']
   comment_receive = request.form['comment_give']

   now = int(time.time())
   user_data = db.users.find_one({'id': user_id_receive}, {'_id': False, 'pw': False})
   nickname = user_data.get('nickname')

   comment = {
      'card_id' : card_id_receive,
      'user_id' : user_id_receive,
      'nickname' : nickname,
      'comment_sent_time': now,
      'comment_text' : comment_receive
   }

   db.comments.insert_one(comment)  
   return jsonify({'result' : 'success', 'msg': '댓글이 등록되었습니다!'})



#특정 카드에 가입하는 api, 이미 가입 되었을 시 => 실패 메시지 발송
@app.route('/food/join', methods=['POST'])
def join_clud():
   card_id_receive = request.form['card_id_give']
   user_id_receive = request.form['user_id_give']
   
   card = db.cards.find_one({ '_id' : ObjectId(card_id_receive)})
   user_data = db.users.find_one({'id': user_id_receive}, {'_id': False, 'pw': False})
   nickname = user_data.get('nickname')
   
   if nickname in card.get('card_members', []):
      return jsonify({'result' : 'fail', 'msg' : '이미 가입된 유저입니다.'})

   db.cards.update_one(
      {'_id' : ObjectId(card_id_receive)},
      {'$push': { 'card_members' : nickname }}
   )
   return jsonify({'result' : 'success', 'msg': '가입이 완료되었습니다!'})



#특정 카드에서 탈퇴하는 api
@app.route('/food/exit', methods=['POST'])
def exit_club():
   card_id_receive = request.form['card_id_give']
   user_id_receive = request.form['user_id_give']
   
   user_data = db.users.find_one({'id': user_id_receive}, {'_id': False, 'pw': False})
   nickname = user_data.get('nickname')

   db.cards.update_one(
      {'_id' : ObjectId(card_id_receive)},
      {'$pull': { 'card_members' : nickname }}
   )
   return jsonify({'result' : 'success', 'msg': '탈퇴가 완료되었습니다!'})



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
scheduler.add_job(scheduled_job, 'interval', minutes=10)
scheduler.start()



if __name__ == '__main__':
   app.run('0.0.0.0', port=5001, debug=True)

