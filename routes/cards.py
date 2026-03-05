from flask import Blueprint, render_template, jsonify, request
from bson.objectid import ObjectId
from db import db


import time
import jwt
import datetime
import hashlib
SECRET_KEY = "welcometothejungle"


from contents import FOOD_IMAGE_MAP

food_bp = Blueprint('food', __name__)


# 카드 상세 화면 api
@food_bp.route('/food/<string:card_id>', methods=['GET'])
def article(card_id):
   try:
      token_receive = request.cookies.get('mytoken')
      payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
      user_id_receive = payload['id']
      nickname = db.users.find_one({'id': user_id_receive}).get('nickname')
   except:
      nickname = None  
   pass
   


   card = db.cards.find_one({'_id': ObjectId(card_id)})
   # print( "찾은 카드 " + card)
   card['_id'] = str(card['_id'])
   card['card_duedate'] = time.strftime('%Y-%m-%d %H:%M', time.localtime(card['card_duedate']))
   card['card_type'] = FOOD_IMAGE_MAP.get(card['card_type'])
   # return jsonify({'result': 'success' , 'data' : card })
   return render_template('article.html', card=card, nickname = nickname )