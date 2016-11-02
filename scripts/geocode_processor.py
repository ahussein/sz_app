# _*_ coding: utf-8  _*_
"""
A script that process a datasource file exported from the archive system
The exported data from the archive system are exported as csv file with the following fileds

DialogId = original ID of article delivered by editorial system
ArtikelId = unique ID of article given by Lesewert-database
Überschrifttext = heading of article
Datum = date
Ressort = section/desk
Unterressort = subsection
Seite = page
Dachzeilentext = headline of article
Vorspanntext/Untertiteltext = header of article
Artikeltext = basetext of article
Unterschrifttext = “onlinebox”/additional information at the end of an article
Bildunterschrifttext = caption
Handlungsort = location manually tagged by archive (“geotag”)
Originaltext = original code of the XML delivered by editorial system

The script will extract the Handlungsort field values and process them to clean any un-needed words and then send a query to a geocoder service to retrieve
a pair of latitude and longitude. An example Handlungsort field value is: Lausitzring, Klettwitz, Deutschland

articles = [
{
	'dialog_id': '',
	'article_id': '',
	'heading': '',
	'pub_date':'',
	'categories': '',
	'text': '',
	'address': {
		'text': '',
		'coord': ['', ''],
		'bbox': {},
	},
	'online_url': '',
	'image': '',
},
]
"""

import csv, codecs, cStringIO
import os
import sys
import geocoder
import json
# import click
import time

# handle unicode issues
class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


class Error(Exception):
	"""
	Error class
	"""
	pass


class GoogleGeocoder(object):
	"""
	Google geocoder
	"""
	def __init__(self):
		"""
		Initialize geocoder
		"""
		self._api_string = '' 

	def geocode(self, input):
		"""
		Geocode a string input and return a location properties

		@param input: Input string that represent a location string e.g: Lausitzring, Klettwitz, Deutschland
		@type input: str
		"""
		pass


class GeocoderFactory(object):
	"""
	Geocoder factory to create new geocoder instance
	"""
	types = ['google', 'komoot'] 

	def get(self, geocoder_type=None):
		"""
		Get an instance of a geocoder

		@param geocoder_type: The type of the geocoder instance
		@type geocoder_type: str
		"""
		if geocoder_type is None:
			geocoder_type = DEFAULT_GEOCODER_TYPE
		if geocoder_type not in self.types:
			raise Error('Invalid GeoCoder type [%s]' % geocoder_type)
		return getattr(geocoder, geocoder_type)


report_template = \
"""
Geocoder report
================
Input file: %(input_file_path)s
Total number of records: %(nr_of_records)s

Number of records with no location address: %(nr_location_records)s
Number of records with failed geocoding: %(nr_failed_geocoding)s

Errors: 
%(errors)s
"""

error_msg = 'Cannot get location for address [%s] associated with article [%s]. Error: [%s]'
DEFAULT_GEOCODER_TYPE = 'google'
ADDRESS_CACHE = {}
DEFAULT_CACHE_FILE_PATH = 'geocoder_address_cache.json'

def load_address_cache(cache_file_path=None):
	"""
	Loads address cache from the disk

	@param cache_file_path: Path to the cache file on the system
	@type cache_file_path: str
	"""
	global ADDRESS_CACHE
	if cache_file_path is None:
		cache_file_path = os.path.join(os.path.dirname(__file__), DEFAULT_CACHE_FILE_PATH)
	if not os.path.exists(cache_file_path):
		print('Cache file [%s] does not exist' % cache_file_path)
	else:
		ADDRESS_CACHE = json.load(open(cache_file_path, 'rb'))


def save_addess_cache(cache_file_path=None):
	"""
	Saves the address cache to the disk

	@param cache_file_path: Path to the cache file on the system
	@type cache_file_path: str
	"""
	if cache_file_path is None:
		cache_file_path = os.path.join(os.path.dirname(__file__), DEFAULT_CACHE_FILE_PATH)
	
	json.dump(ADDRESS_CACHE, open(cache_file_path, 'wb'))


def create_article(row_info, location):
	"""
	Creates an article object from a csv row

	@param row_info: A row from the csv file
	@type row_info: dict

	@param location: Location information for the article entry
	@type location: dict
	"""
	article = {
		'dialog_id': row_info['DialogId'],
		'article_id': row_info['ArtikelId'],
		'heading': row_info['Ueberschrifttext'],
		'pub_date': time.mktime(time.strptime(row_info['Datum'], "%d.%m.%Y")),
		'categories': row_info['Ressort'],
		'subcategories': row_info['Unterressort'],
		'text': row_info['Artikeltext'],
		'address': {
			'text': row_info['Handlungsort'],
			# "geometry": {"type": "Point", "coordinates": [location['lng'], location['lat']] if location else []},
			'coordinates': [location['lng'], location['lat']] if location else [],
			'bbox': location['bbox'] if location else {},
		},
		'online_url': '',
		'image': '',
		'read_times': 0,

	}
	if location:
		article['address']['geometry'] = {"type": "Point", "coordinates": [location['lng'], location['lat']]}
	return article

def populate_db(articles):
	"""
	Updates the database with the collection of articles

	@param articles: List of articles
	@type articles: list
	"""
	from pymongo import MongoClient
	import pymongo
	from pymongo.errors import BulkWriteError
	client = MongoClient()
	db = client.sz
	articles_collection = db.articles
	# create indexes if not exist
	articles_collection.create_index([('address.geometry', pymongo.GEOSPHERE)])
	articles_collection.create_index([('text', pymongo.TEXT), ('heading', pymongo.TEXT)], default_language="german")


	# delete existing records
	records_to_check = []
	for article in articles:
		records_to_check.append({'dialog_id': article['dialog_id']})
	res = articles_collection.delete_many({"$or": records_to_check})
	print('Found [%s] existing articles in the DB...deleted!' % res.deleted_count)
	try:
		res = articles_collection.insert_many(articles)
		print('Added [%s] articles to DB' % len(res.inserted_ids))
	except BulkWriteError as bwe:
		print(bwe.details)


# @click.command()
# @click.option('--input_file_path', help="Path to the input csv file")
# @click.option('--geocoder_type', default=DEFAULT_GEOCODER_TYPE, help="Geocoder service provide name")
def main(input_file_path, geocoder_type=DEFAULT_GEOCODER_TYPE):
	"""
	Main entry point for the script, expect a csv file path and rewrite a new file with locoation attribute added

	@param input_file_path: Path to the input csv file
	@type input_file_path: str

	@param geocoder_type: Geocoder service provide name
	@type geocoder_type: str
	"""
	# validate that the input file path exist
	if not os.path.exists(input_file_path):
		raise Error('Input file [%s] does not exist' % input_file_path)
	try:
		load_address_cache()
	except Exception, ex:
		print('Failed to load address cache. Error: %s' % ex)

	articles = []
	result = {}
	errors = []
	nr_of_records_with_no_address = 0
	geocoder_obj = GeocoderFactory().get(geocoder_type=geocoder_type)
	default_geocoder_obj = None
	with open(input_file_path, 'rb') as fd:
		reader = UnicodeReader(fd, delimiter=';')
		header = reader.next()
		# workaround for the problem with unicode and the header
		header_items = ['DialogId', 'ArtikelId', 'Ueberschrifttext',
						'Datum', 'Ressort', 'Unterressort',
						'Artikeltext', 'Handlungsort']

		for index, item in enumerate(list(header)):
			for header_item in list(header_items):
				if header_item in item:
					header[index] = header_item
					header_items.remove(header_item)
					break

		for index, row in enumerate(reader):
			row_info = dict(zip(header, row))
			location_address = row[-2]
			article_id = row[0]
			location = {}
			# check if address already in the cache
			if location_address in ADDRESS_CACHE:
				location = ADDRESS_CACHE[location_address]
			else:
				if not location_address:
					nr_of_records_with_no_address += 1
					# print('Artical [%s] does not have location set' % article_id)
				else:
					try:
						geocoder_result = geocoder_obj(location_address)
						if geocoder_result.ok is False:
							if geocoder_type != DEFAULT_GEOCODER_TYPE:
								print("Failed to resolve address [%s] using geocoder [%s]. Trying default geocoder" % (location_address, geocoder_type))
								if default_geocoder_obj is None:
									default_geocoder_obj = GeocoderFactory().get(geocoder_type=DEFAULT_GEOCODER_TYPE)
								geocoder_result = default_geocoder_obj(location_address)
						if geocoder_result.ok is False:	
							msg =  error_msg % (location_address, article_id, geocoder_result)
							errors.append(msg)
						else:
							location = {'lat': geocoder_result.latlng[0], 
										'lng': geocoder_result.latlng[1],
										'bbox': geocoder_result.bbox}
							ADDRESS_CACHE[location_address] = location

					except Exception, ex:
						msg =  error_msg % (location_address, article_id, ex)
						errors.append(msg)
			articles.append(create_article(row_info, location))
			result[article_id] = location
	try:
		save_addess_cache()
	except Exception, ex:
		print('Errors while saving address cache. Error: %s' % ex)

	try:
		populate_db(articles)
	except Exception, ex:
		print('Errors while populating database. Error: %s' % ex)

	report = report_template % {'input_file_path': input_file_path,
								'nr_location_records': nr_of_records_with_no_address,
								'nr_failed_geocoding': len(errors),
								'errors': '\n'.join(errors),
								'nr_of_records': index}
	print(report)


if __name__ == '__main__':
	input_file_path = sys.argv[1]
	geocoder_type = None
	if len(sys.argv) == 3:
		geocoder_type = sys.argv[2]
	main(input_file_path, geocoder_type=geocoder_type)