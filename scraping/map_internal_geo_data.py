import time
import os
import sys
import json
import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from urllib.parse import urlparse, parse_qs

# ~~~~~~ INPUTS ~~~~~~
# json file keyed by internal location id with values in (city, county, state, country, postalcode)
input_mapping = str(sys.argv[1])
# filename to output mapping json
output_mapping = str(sys.argv[2])
# directory to output geojson files
output_directory = str(sys.argv[3])

with open(input_mapping) as f:
	input_json = json.load(f)

driver = webdriver.Chrome()
driver.set_window_size(800, 800)

# delete old output mapping file if exists and open fresh file
if os.path.exists(output_mapping):
	os.remove(output_mapping)
ouput_mapping_file = open(output_mapping, "a")
ouput_mapping_file.write('{\n')

#check if output directory exists
if not os.path.exists(output_directory):
	os.mkdir(output_directory)

# open json file keyed by internal location id
for x in input_json:

	for y in input_json[x].keys():
		if y not in ('city', 'county', 'state', 'country', 'postalcode'):
			print('key value ' + y + ' not recognized')

	url = 'https://nominatim.openstreetmap.org/search.php?'

	url = url + 'city='
	try:
		url = url + input_json[x]['city'].replace(' ', '+')
	except KeyError:
		pass

	url = url + '&county='
	try:
		url = url + input_json[x]['county'].replace(' ', '+')
	except KeyError:
		pass

	url = url + '&state='
	try:
		url = url + input_json[x]['state'].replace(' ', '+')
	except KeyError:
		pass

	url = url + '&country='
	try:
		url = url + input_json[x]['country'].replace(' ', '+')
	except KeyError:
		pass

	url = url + '&postalcode='
	try:
		url = url + input_json[x]['postalcode'].replace(' ', '+')
	except KeyError:
		pass

	driver.get(url)

	try:
		element = driver.find_element_by_css_selector("#content > #searchresults > .highlight > a")

		osmid = None
		
		if parse_qs(urlparse(element.get_attribute("href")).query)['class'][0] == 'boundary':
			osmid = parse_qs(urlparse(element.get_attribute("href")).query)['osmid'][0]
			ouput_mapping_file.write('\"' + x + '\": ' + osmid + ',\n')
		else:
			element.click()
			retry_count = 0
			while retry_count < 100:
				try:
					addresses = driver.find_elements_by_css_selector("#address > tbody > tr")
					retry_count = 100
				except:
					retry_count = retry_count + 1
					time.sleep(0.1)
					pass

			# addresses = driver.find_elements_by_css_selector("#address > tbody > tr")
			for i in range(len(addresses)):
				address_type = addresses[i].find_element_by_css_selector("td:nth-of-type(2)").get_attribute("innerText")
				osmid = addresses[i].find_element_by_css_selector("td:nth-of-type(3) > a").get_attribute("href").split('/')[-1]
				if address_type.split(':')[0] == 'boundary':
					ouput_mapping_file.write('\"' + x + '\": ' + osmid + ',\n')
					break

		if osmid:
			r = requests.get('http://polygons.openstreetmap.fr/get_geojson.py?id=' + osmid + '&params=0')

			output_mapping_filename = output_directory + '/' + osmid + '.txt'
			if os.path.exists(output_mapping_filename):
				os.remove(output_mapping_filename)
			ouput_geojson_file = open(output_mapping_filename, 'a')
			try:
				ouput_geojson_file.write(json.dumps(r.json()))
			except json.decoder.JSONDecodeError:
				ouput_geojson_file.write('None')
				print('no geojson data found for osmid ' + osmid + ': ' + url)
			ouput_geojson_file.close()
		else:
			print('no osmid found for locationId=' + x + ': ' + url)
			ouput_mapping_file.write('\"' + x + '\": 0,\n')

		time.sleep(1)
	except NoSuchElementException:
		print('error parsing html element for locationId=' + x + ': ' + url)
		ouput_mapping_file.write('\"' + x + '\": 0,\n')

ouput_mapping_file.write('}')
ouput_mapping_file.close()
driver.close()

