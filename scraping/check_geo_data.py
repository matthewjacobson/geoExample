import os
import sys
import json
import requests

mapping = str(sys.argv[1])
directory = str(sys.argv[2])

with open(mapping) as f:
	mapping_json = json.load(f)

for x in mapping_json:
	osmid = str(mapping_json[x])
	geo_json_path = directory + '/' + osmid + '.txt'
	if not os.path.exists(geo_json_path):
		r = requests.get('http://polygons.openstreetmap.fr/get_geojson.py?id=' + osmid + '&params=0')
		ouput_geojson_file = open(geo_json_path, 'a')
		try:
			ouput_geojson_file.write(json.dumps(r.json()))
		except json.decoder.JSONDecodeError:
			ouput_geojson_file.write('None')
			print('no geojson data found for osmid ' + osmid + ': ' + 'http://polygons.openstreetmap.fr/get_geojson.py?id=' + osmid + '&params=0')
		ouput_geojson_file.close()