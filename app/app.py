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

		return mongo_jsonfy({'response': data})


	def post(self):
		data = request.get_json()
		if not data:
			result = {'response': "ERROR"}
			return mongo_jsonfy(result)

		filters = data.get('filters', {})
		location_filter = filters.get('location', {})
		# for location filter we expect a source point [lat, lng] and a distance in meters
		if 'source' not in location_filter or 'distance' not in location_filter:
			result = {'response': "ERROR"}
			return mongo_jsonfy(result)
		query = {"address.coordinates": SON([("$near", location_filter['source']), ("$maxDistance", location_filter['distance'])])}
		found_articles = []
		for article in mongo.db.articles.find(query):
			found_articles.append(article)
		result = {'response': found_articles if found_articles else 'No articles found', 'count': len(found_articles)}
		return mongo_jsonfy(result)


class Index(Resource):
	def get(self):
		return redirect(url_for("articles"))



api = Api(app)
api.add_resource(Index, "/", endpoint="index")
api.add_resource(Article, "/api", endpoint="articles")


if __name__ == "__main__":
	app.run(debug=True, port=80)
