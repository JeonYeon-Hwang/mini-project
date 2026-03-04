from flask import Flask, render_template, jsonify, request
app = Flask(__name__)

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
   
   return jsonify({'result' : 'success'})



#모든 카드를 보여주는 api
@app.route('/food/card/show', methods=['GET'])
def show_cards():
   all_cards = "임시"
   
   return jsonify({'result' : 'success', 'cards' : all_cards})



#특정 카드의 댓글을 보여주는 api
@app.route('/food/<int:card_id>/comments', methods=['GET'])
def show_card_comments(card_id):
   dedicated_comments = "임시"
   
   return jsonify({'result' : 'success', 'comments' : dedicated_comments })



#댓글을 등록하는 api
@app.route('/food/<int:card_id>/comments', methods=['GET'])
def create_comments(card_id):
   
   return jsonify({'result' : 'success'})



#특정 카드에 가입하는 api
@app.route('/food/join', methods=['GET'])
def join_clud():
   
   return jsonify({'result' : 'success'})




if __name__ == '__main__':
   app.run('0.0.0.0', port=5001, debug=True)

