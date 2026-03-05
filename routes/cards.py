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
   if card.get('card_duedate') and isinstance(card['card_duedate'], (int, float)):
       card['card_duedate'] = time.strftime('%Y-%m-%d %H:%M', time.localtime(card['card_duedate']))
   card['card_type'] = FOOD_IMAGE_MAP.get(card.get('card_type', ''))
   
   query =  {'card_id': card_id}
   dedicated_comments = list(db.comments.find(query).sort('comment_sent_time', 1))
   for c in dedicated_comments:
      if '_id' in c:
         c['_id'] = str(c['_id'])
      if c.get('comment_sent_time') and isinstance(c['comment_sent_time'], (int, float)):
         c['comment_sent_time'] = time.strftime('%Y-%m-%d %H:%M', time.localtime(c['comment_sent_time']))
   
   return render_template('article.html', 
                           card = card, 
                           user=user,
                           comments=dedicated_comments)

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
