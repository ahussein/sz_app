# -*- coding: utf-8 -*-
"""
Flask app entry point
"""

from flask import Flask, jsonify, url_for, redirect, request
from flask_pymongo import PyMongo
from flask_restful import Api, Resource
from bson import json_util
import json


app = Flask(__name__)
app.config['MONGO_DBNAME'] = "sz"
mongo = PyMongo(app, config_prefix="MONGO")
APP_URL = "http://127.0.0.1:80"


def mongo_jsonfy(data):
	"""
	Jsonfy version that works with mongo bson data
	"""
	return json.loads(json_util.dumps(data))

class Article(Resource):
	def get(self):
		data = []
		cursor = mongo.db.articles.find().limit(10)
		for article in cursor:
			data.append(article)

		return mongo_jsonify({'response': data})


	def post(self):
		data = request.get_json()
		if not data:
			data = {'response': "ERROR"}
			return jsonify(data)



class Index(Resource):
	def get(self):
		return redirect(url_for("articles"))



api = Api(app)
api.add_resource(Index, "/", endpoint="index")
api.add_resource(Article, "/api", endpoint="articles")


if __name__ == "__main__":
	app.run(debug=True, port=80)
