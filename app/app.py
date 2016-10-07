# -*- coding: utf-8 -*-
"""
Flask app entry point
"""

from flask import Flask, jsonify, url_for, redirect, request
from flask_pymongo import PyMongo
from flask_restful import Api, Resource


app = Flask(__name__)
app.config['MONGO_DBNAME'] = "test"
mongo = PyMongo(app, config_prefix="MONGO")
APP_URL = "http:127.0.0.1:80"

class Article(Resource):
	def get(self):
		data = []
		return jsonify({'response': data})



class Index(Resource):
	def get(self):
		return redirect(url_for("articles"))



api = Api(app)
api.add_resource(Index, "/", endpoint="index")
api.add_resource(Article, "/api", endpoint="articles")


if __name__ == "__main__":
	app.run(debug=True)