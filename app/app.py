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
import datetime
import time

app = Flask(__name__)
app.config['MONGO_DBNAME'] = "sz"
CORS(app)
mongo = PyMongo(app, config_prefix="MONGO")

article_categories_map = {
	"LOKDRS_R": "Lokales Dresden",
	"WISSE_R": "Wissen",
	"SEITE3": "Seite3",
    "FEU_R": "Feuilleton",
    "PL_R": "Politik",
    "LEBEN_R": "Leben",
    "TITEL_R": "Titelseite",
    "SP_R": "Sport",
    "WI_R": "Wirtschaft",
    "PAN_R": "Panorama",
    "BE":  "Magazin", 
    "LF_R": "Leserforum"
}

article_categories_reverse_map = {v: k for k, v in article_categories_map.iteritems()}

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
		text_filter = filters.get('text', "")
		categories_filter = filters.get('categories', [])
		time_filter = filters.get("time", [])
		query_kwargs = {}
		query = {}
		found_articles = []
		all_filters_articles_ids = set([])
		if location_filter:
			# for location filter we expect a source point [lat, lng] and a distance in meters
			if 'source' not in location_filter or 'distance' not in location_filter:
				result = {'response': "ERROR"}
				return mongo_jsonfy(result)
			query.update({"address.geometry": { "$nearSphere": { "$geometry": { "type": "Point", "coordinates": location_filter['source'] }, 
						"$maxDistance": location_filter['distance'] } } })
		if categories_filter:
			categories_filter = [article_categories_reverse_map.get(item, item) for item in list(categories_filter)]
			query.update({'categories': {'$in': categories_filter}})

		if time_filter:
			# time filter is in a range formate (from, to)
			from_date = time.mktime(time.strptime(time_filter[0], "%d.%m.%Y"))
			to_date = time.mktime(time.strptime(time_filter[1], "%d.%m.%Y"))
			# query.update({'$and': [ {'pub_date': {'$gt': from_date}}, {'pub_date': {'$lt': to_date}} ]})
			query.update({'pub_date': {'$gt': from_date, '$lt': to_date}})
			
		# we cannot have both text and location search in the same query since they are both indexes, we will have to query first will all filters 
		# and then do another query for the text 
		for article in mongo.db.articles.find(query, **query_kwargs):
			found_articles.append(article)
			all_filters_articles_ids.add(article['dialog_id'])

		# text filter
		if text_filter:
			found_articles = []
			query = {
						"$text": {"$search": text_filter},
						'dialog_id': {'$in': list(all_filters_articles_ids)}
					}
			for article in mongo.db.articles.find(query, **query_kwargs):
				found_articles.append(article)

		for article in found_articles:
			# clean the article reault
			# article.pop('text')
			article['address'].pop('bbox')
			# if 'geometry' in article['address']:
			# 	article['address'].pop('geometry')
			if location_filter:
				# get distance
				article['distance'] = _calculate_distance(article['address']['coordinates'], location_filter['source'])

			article['categories'] = article_categories_map.get(article['categories'], article['categories'])
			article['pub_date'] = datetime.datetime.fromtimestamp(article['pub_date']).strftime('%d.%m.%Y')
			# geojson require a properties attribute, we need to do this better!
			for key, value in article.copy().iteritems():
				if 'properties' not in article:
					article['properties'] = {}
				article['properties'][key] = value
			article['geometry'] = {}
			if 'geometry' in article['address']:
				article['geometry'] = article['address']['geometry']
			article['type'] = 'Feature'

		# make sure to sort by distance if locatio filter is enabled
		if location_filter:
			from operator import itemgetter
			found_articles.sort(key=itemgetter('distance'))
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
