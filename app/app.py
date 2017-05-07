
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

MAX_NR_OF_POPULAR_ARTICLES = 20


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
	return int(distance.m)

class Article(Resource):

	def put(self):
		data = request.get_json()
		print(data)
		if not data:
			result = {'response': "ERROR: No data provided"}
			return mongo_jsonfy(result)
		dialog_id = data.get('dialog_id', '')
		current_user_location = data.get('user_location', '')
		nr_of_read = data.get('nr_of_read', '')
		nr_of_likes = data.get('nr_of_likes', '')
		update_properties = {}
		if dialog_id:
			if type(nr_of_read) ==  int or (type(nr_of_read) == str and nr_of_read.isdigit()):
				nr_of_read = int(nr_of_read)
				update_properties['nr_of_read'] = nr_of_read
			if type(nr_of_likes) ==  int or (type(nr_of_likes) == str and nr_of_likes.isdigit()):
				nr_of_likes = int(nr_of_likes)
				update_properties['nr_of_likes'] = nr_of_likes
		try:
			result = mongo.db.articles.update_many({'dialog_id': dialog_id}, {'$set': update_properties})
		except Exception as ex:
			result = {'response': "ERROR: %s" % ex}
		else:
			result = {'response': 'OK: %s records updated' % result.matched_count}
		return mongo_jsonfy(result)


	def post(self):
		data = request.get_json()
		print(data)
		if not data:
			result = {'response': "ERROR"}
			return mongo_jsonfy(result)

		user_location = data.get('user_location', [])
		requested_fields = data.get('fields', [])
		filters = data.get('filters', {})
		location_filter = filters.get('location', {})
		text_filter = filters.get('text', "")
		categories_filter = filters.get('categories', [])
		time_filter = filters.get("time", [])
		query_kwargs = {}
		query = {}
		popular_news_query = {}
		found_articles = []
		popular_articles = []
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
			if type(time_filter[0]) == str or time_filter[0].isdigit():
				from_date = int(time_filter[0])
				to_date = int(time_filter[1])
			else:  
				from_date = time.mktime(time.strptime(time_filter[0], "%d.%m.%Y"))
				to_date = time.mktime(time.strptime(time_filter[1], "%d.%m.%Y"))
			# query.update({'$and': [ {'pub_date': {'$gt': from_date}}, {'pub_date': {'$lt': to_date}} ]})
			query.update({'pub_date': {'$gte': from_date, '$lte': to_date}})
			
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


		# popular news query
		if location_filter and user_location:
			popular_news_query.update({"address.geometry": { "$nearSphere": { "$geometry": { "type": "Point", "coordinates": user_location }, 
						"$maxDistance": location_filter['distance'] } } })
			for article in mongo.db.articles.find(popular_news_query).sort([('nr_of_likes', -1), ('nr_of_read', -1)]).limit(MAX_NR_OF_POPULAR_ARTICLES):
				article['pub_date'] = datetime.datetime.fromtimestamp(article['pub_date']).strftime('%d.%m.%Y')
				article['distance'] = _calculate_distance(article['address']['geometry']['coordinates'], user_location)
				# filter requested fields
				if requested_fields:
					for key in article.keys():
						if key not in requested_fields:
							article.pop(key)
				popular_articles.append(article)

		for article in found_articles:
			# clean the article reault
			# article.pop('text')
			article['address'].pop('bbox')
			# if 'geometry' in article['address']:
			# 	article['address'].pop('geometry')
			if location_filter:
				# get distance
				article['distance'] = _calculate_distance(article['address']['geometry']['coordinates'], location_filter['source'])
			elif user_location:
				# if no location filter then calculate the distance based on the current location
				article['distance'] = _calculate_distance(article['address']['geometry']['coordinates'], user_location)

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

			if not article['online_url']:
				article['online_url'] = "http://www.sz-online.de/"

			# filter requested fields
			if requested_fields:
				for key in article.keys():
					if key not in requested_fields:
						article.pop(key)


		# make sure to sort by distance if locatio filter is enabled
		if location_filter and requested_fields and 'distance' in requested_fields:
			from operator import itemgetter
			found_articles.sort(key=itemgetter('distance'))
		result = { 
			'filtered_articles' : {'response': found_articles if found_articles else 'No articles found', 'count': len(found_articles)},
			'popular_articles': {'response': popular_articles if popular_articles else 'No articles found', 'count': len(popular_articles)}
			}
		return mongo_jsonfy(result)


class Index(Resource):
	def get(self):
		return redirect(url_for("articles"))


api = Api(app)
api.add_resource(Index, "/", endpoint="index")
api.add_resource(Article, "/api", endpoint="articles")


if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0' ,port=8080)
