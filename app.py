from flask import Flask, render_template, jsonify, request
app = Flask(__name__)

import time

import requests
from bs4 import BeautifulSoup

from bson.objectid import ObjectId

from pymongo import MongoClient
client = MongoClient('mongodb://test:test@52.79.109.78', 27017)
db = client.dbjungle



#기본 화면 api
@app.route('/')
def home():
   return render_template('index.html')



#로그인 api




#회원가입 api




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
   return render_template('index.html', cards = all_cards)



#특정 카드의 댓글을 보여주는 api
@app.route('/food/<string:card_id>/comments', methods=['GET'])
def show_card_comments(card_id):
   query =  {'_id': ObjectId(card_id)}
   dedicated_comments = list(db.comments.find(query).sort('comment_sent_time', 1))
   return render_template('index.html', comments = dedicated_comments)



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
   return jsonify({'result' : 'success', 'msg': '댓글이 등록되었습니다!'})



#특정 카드에 가입하는 api
@app.route('/food/join', methods=['POST'])
def join_clud():
   # user_id = db.users.get_user_id()
   card_id_receive = request.form['card_id_give']
   
   db.cards.update_one(
      {'_id' : card_id_receive },
      {'$push': { 'card_members' : "user_id-임시"}}
   )
   return jsonify({'result' : 'success', 'msg': '가입이 완료되었습니다!'})



if __name__ == '__main__':
   app.run('0.0.0.0', port=5001, debug=True)

