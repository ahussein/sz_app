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
"""

import csv
import os
import sys

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
	types = {'google': GoogleGeocoder}

	def get(self, geocoder_type='google'):
		"""
		Get an instance of a geocoder

		@param geocoder_type: The type of the geocoder instance
		@type geocoder_type: str
		"""
		return types.get(geocoder_type, 'google')


def main(input_file_path):
	"""
	Main entry point for the script, expect a csv file path and rewrite a new file with locoation attribute added

	@param input_file_path: path to the input csv file
	@type input_file_path: str
	"""
	# validate that the input file path exist
	if not os.path.exists(input_file_path):
		raise Error('Input file [%s] does not exist' % input_file_path)

	with open(input_file_path, 'rb') as fd:
		reader = csv.DictReader(fd, delimiter=';')
		for row in reader:
			print(row['Handlungsorte'])


if __name__ == '__main__':
	input_file_path = sys.argv[1]
	main(input_file_path)