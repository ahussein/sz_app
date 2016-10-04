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

import csv, codecs, cStringIO
import os
import sys
import geocoder

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
			geocoder_type = 'google'
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

def main(input_file_path, geocoder='google'):
	"""
	Main entry point for the script, expect a csv file path and rewrite a new file with locoation attribute added

	@param input_file_path: path to the input csv file
	@type input_file_path: str

	@param geocoder: Geocoder service provide name
	@type geocoder: str
	"""
	# validate that the input file path exist
	if not os.path.exists(input_file_path):
		raise Error('Input file [%s] does not exist' % input_file_path)
	result = {}
	errors = []
	nr_of_records_with_no_address = 0
	geocoder = GeocoderFactory().get(geocoder_type=geocoder)
	with open(input_file_path, 'rb') as fd:
		reader = UnicodeReader(fd, delimiter=';')
		header = reader.next()
		for index, row in enumerate(reader):
			location_address = row[-2]
			article_id = row[0]
			if not location_address:
				nr_of_records_with_no_address += 1
				# print('Artical [%s] does not have location set' % article_id)
			else:
				try:
					geocoder_result = geocoder(location_address)
					if geocoder_result.ok is False:
						msg =  error_msg % (location_address, article_id, geocoder_result)
						errors.append(msg)
					else:
						result[article_id] = {'lalng': geocoder_result.latlng,
												'bbox': geocoder_result.bbox}
				except Exception, ex:
					msg =  error_msg % (location_address, article_id, ex)
					errors.append(msg)
	report = report_template % {'input_file_path': input_file_path,
								'nr_location_records': nr_of_records_with_no_address,
								'nr_failed_geocoding': len(errors),
								'errors': '\n'.join(errors),
								'nr_of_records': index}
	print(report)


if __name__ == '__main__':
	input_file_path = sys.argv[1]
	geocodder = None
	if len(sys.argv) == 3:
		geocoder = sys.argv[2]
	main(input_file_path, geocoder=geocoder)