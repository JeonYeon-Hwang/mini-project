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
   card_duedate_receive = request.form['card_duedate_give']
   card_url_receive = request.form['card_url_give']

   card = {
      'user_id' : user_id_receive,
      'card_title' : card_title_receive,
      'card_text' : card_content_receive,
      'card_duedate' : card_duedate_receive,
      'card_members' : [ ],
      'card_url' : card_url_receive,
      'is_alive' : True
   }

   db.cards.insert_one(card)
   return jsonify({'result' : 'success'})



#모든 카드를 보여주는 api
@app.route('/food/card/show', methods=['GET'])
def show_cards():
   all_cards = list(db.cards.find({}).sort('card_duedate', 1))  
   return jsonify({'result' : 'success', 'cards' : all_cards})



#특정 카드의 댓글을 보여주는 api
@app.route('/food/<int:card_id>/comments', methods=['GET'])
def show_card_comments(card_id):
   query =  {'_id': ObjectId(card_id)}
   dedicated_comments = list(db.comments.find(query).sort('comment_sent_time', 1))
   return jsonify({'result' : 'success', 'comments' : dedicated_comments })



#댓글을 등록하는 api
@app.route('/food/post/comments', methods=['POST'])
def create_comments():
   card_id_receive = request.form['card_id_give']
   user_id_receive = request.form['user_id_give']
   comment_receive = request.form['comment_give']

   now = time
   # user_id = db.users.get_user_id()
   nickname = db.users.find_one({'_id' : "user_id-임시"}).get('nick_name')

   comment = {
      'card_id' : card_id_receive,
      'user_id' : user_id_receive,
      'nickname' : nickname,
      'comment_sent_time': now,
      'comment_text' : comment_receive
   }

   db.comments.insert_one(comment)  
   return jsonify({'result' : 'success'})



#특정 카드에 가입하는 api
@app.route('/food/join', methods=['POST'])
def join_clud():
   # user_id = db.users.get_user_id()
   card_id_receive = request.form['card_id_give']
   
   db.cards.update_one(
      {'_id' : card_id_receive },
      {'$push': { 'card_members' : "user_id-임시"}}
   )
   return jsonify({'result' : 'success'})



if __name__ == '__main__':
   app.run('0.0.0.0', port=5000, debug=True)

