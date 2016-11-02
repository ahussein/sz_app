# -*- coding: utf-8 -*-
"""
Flask app entry point
"""

from flask import Flask, jsonify, url_for, redirect, request
from flask_pymongo import PyMongo
from flask_restful import Api, Resource
from bson import json_util
import json
from bson.son import SON
from flask_cors import CORS

app = Flask(__name__)
app.config['MONGO_DBNAME'] = "sz"
CORS(app)
mongo = PyMongo(app, config_prefix="MONGO")



def mongo_jsonfy(data):
	"""
	Jsonfy version that works with mongo bson data
	"""
	return json.loads(json_util.dumps(data))

def _calculate_distance(loc1, loc2):
	"""
	Calculates the distance in meters between two points
	"""
	from geopy.distance import great_circle
	distance = great_circle(loc1, loc2)
	return distance.m

class Article(Resource):
	def get(self):
		data = []
		cursor = mongo.db.articles.find().limit(10)
		for article in cursor:
			data.append(article)

		return mongo_jsonfy({'response': data})


	def post(self):
		data = request.get_json()
		print(data)
		if not data:
			result = {'response': "ERROR"}
			return mongo_jsonfy(result)

		filters = data.get('filters', {})
		location_filter = filters.get('location', {})
		# for location filter we expect a source point [lat, lng] and a distance in meters
		if 'source' not in location_filter or 'distance' not in location_filter:
			result = {'response': "ERROR"}
			return mongo_jsonfy(result)
		query ={"address.geometry": { "$nearSphere": { "$geometry": { "type": "Point", "coordinates": location_filter['source'] }, "$maxDistance": location_filter['distance'] } } }
		# query = {"address.coordinates": SON([("$near", location_filter['source']), ("$maxDistance", location_filter['distance']/ 6378.1)])}
		found_articles = []
		for article in mongo.db.articles.find(query):
			# clean the article reault
			# article.pop('text')
			article['address'].pop('bbox')
			# if 'geometry' in article['address']:
			# 	article['address'].pop('geometry')

			found_articles.append(article)
			# get distance
			article['distance'] = _calculate_distance(article['address']['coordinates'], location_filter['source'])
			
			# geojson require a properties attribute, we need to do this better!
			article['geometry'] = {}
			if 'geometry' in article['address']:
				article['geometry'] = article['address']['geometry']
			for key, value in article.copy().iteritems():
				article['properties'][key] = value

		result = {'response': found_articles if found_articles else 'No articles found', 'count': len(found_articles)}
		return mongo_jsonfy(result)


class Index(Resource):
	def get(self):
		return redirect(url_for("articles"))


api = Api(app)
api.add_resource(Index, "/", endpoint="index")
api.add_resource(Article, "/api", endpoint="articles")


if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0' ,port=8080)
