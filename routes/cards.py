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
   user = get_current_user()
   
   card = db.cards.find_one({'_id': ObjectId(card_id)})
   card['_id'] = str(card['_id'])
   card['card_duedate'] = time.strftime('%Y-%m-%d %H:%M', time.localtime(card['card_duedate']))
   card['card_type'] = FOOD_IMAGE_MAP.get(card['card_type'])
   
   return render_template('article.html', 
                           card = card, 
                           user=user)

def get_current_user():
   token = request.cookies.get("access_token")
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
