from flask import Blueprint, render_template, jsonify
from bson.objectid import ObjectId
from db import db
import time

food_bp = Blueprint('food', __name__)


# 카드 상세 화면 api
@food_bp.route('/food/<string:card_id>', methods=['GET'])
def article(card_id):
   card = db.cards.find_one({'_id': ObjectId(card_id)})
   # print( "찾은 카드 " + card)
   card['_id'] = str(card['_id'])
   card['card_duedate'] = time.strftime('%Y-%m-%d %H:%M', time.localtime(card['card_duedate']))
   return jsonify({'result': 'success' , 'data' : card })
#    return render_template('article.html', card=card)