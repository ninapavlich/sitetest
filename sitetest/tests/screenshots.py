import datetime
import os
import sys
import urllib2
import urllib
import urlparse
import json
import base64
import time
from boto.s3.key import Key
import boto.s3

from ..core.models import HEADERS
from selenium import webdriver

def test_screenshots(set, credentials, options, test_id, max_test_count=20, verbose=False):
	

	use_browserstack = False #True if('browserstack' in credentials and 'USERNAME' in credentials['browserstack']) else False

	if max_test_count== None:
		max_test_count = 20

	test_dir = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

	use_basic_auth = False if 'use_basic_auth' not in options else truthy(options['use_basic_auth'])
	basic_auth_username = '' if use_basic_auth==False else options['basic_auth_username']
	basic_auth_password = '' if use_basic_auth==False else options['basic_auth_password']
	
	if use_browserstack:
		username = credentials['browserstack']['USERNAME']
		password = credentials['browserstack']['PASSWORD']
		user_data = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
	else:		

		if use_basic_auth:
			profile = webdriver.FirefoxProfile()
			profile.set_preference('network.http.phishy-userpass-length', 255)
			browser = webdriver.Firefox(firefox_profile=profile)
		else:
			browser = webdriver.Firefox()



	total = len(set.parsed_links)
	count = 0
	tested_count = 0
	for link_url in set.parsed_links:
		if verbose:
			print "%s/%s"%(count, total)
		count += 1

		link = set.parsed_links[link_url]

		
		if link.is_internal_html==True and not link.skip_test == True:

			if tested_count < max_test_count:
				tested_count += 1

				if use_browserstack==True:

					browser_data = {
						"browsers": [
							{"os": "Windows", "os_version": "7", "browser_version": "8.0", "browser": "ie"},
							{"os": "Windows", "os_version": "7", "browser_version": "9.0", "browser": "ie"}
						], 
						"url": link.url
					}
			
					api_url = 'http://www.browserstack.com/screenshots'
					request = urllib2.Request(api_url, json.dumps(browser_data))
					request.add_header("Authorization", "Basic %s" % user_data)   
					request.add_header('Content-Type', 'application/json')
					request.add_header('Accept', 'application/json')

					response = urllib2.urlopen(request)
					result = json.load(response)
					#TODO -- handle results...

				else:


					#!/usr/bin/env python
					
					if use_basic_auth:
						parsed = urlparse.urlparse(link.url)
						updated_location = "%s:%s@%s"%(basic_auth_username, basic_auth_password, parsed.netloc)
						parsed = parsed._replace(netloc=updated_location)
						updated = urlparse.urlunparse(parsed)
						url = updated
					else:
						url = link.url

					browser.get(url)

					if 'screenshots' in options:

						for key, screenshot in options['screenshots'].iteritems():
							

							width = screenshot[0]
							height = screenshot[1]
							browser.set_window_size(width, height)

							#delay, allow to render
							time.sleep(1)

							

							results_dir = os.path.join(os.path.dirname(__file__), '..', 'test_results', test_id, test_dir, link.internal_page_url)
							if not os.path.exists(results_dir):
								os.makedirs(results_dir)
								
							filename = '%s/%s-%s.png'%(results_dir, width, height)
							browser.save_screenshot(filename)

							folder = '%s/%s/%s'%(test_id, test_dir, link.internal_page_url)
							image_url = copy_to_amazon(filename, folder, test_id, credentials, verbose)

							link.screenshots[key] = image_url
						

	browser.quit()


def copy_to_amazon(file_name, folder, test_id, credentials, verbose):
	

	if 'aws' in credentials and 'AWS_ACCESS_KEY_ID' in credentials['aws']:
		AWS_ACCESS_KEY_ID = credentials['aws']['AWS_ACCESS_KEY_ID']
		AWS_SECRET_ACCESS_KEY = credentials['aws']['AWS_SECRET_ACCESS_KEY']
		AWS_STORAGE_BUCKET_NAME = credentials['aws']['AWS_STORAGE_BUCKET_NAME']
		AWS_RESULTS_PATH = credentials['aws']['AWS_RESULTS_PATH']

		test_dir = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

		base_name = os.path.basename(file_name)
		bucket_name = AWS_STORAGE_BUCKET_NAME    

		conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
		bucket = conn.get_bucket(bucket_name)

		current_dir = os.path.dirname(__file__)

		if verbose:
			print 'Uploading %s to Amazon S3 from %s' % (base_name, file_name)

			def percent_cb(complete, total):
				sys.stdout.write('.')
				sys.stdout.flush()

		
		k = Key(bucket)
		k.key = u"%s/%s/%s"%(AWS_RESULTS_PATH, folder, base_name)
		k.set_contents_from_filename(file_name, cb=percent_cb, num_cb=10)
		k.set_acl('public-read')

		url = "http://s3.amazonaws.com/%s/%s/%s/%s" % (AWS_STORAGE_BUCKET_NAME, AWS_RESULTS_PATH, folder, base_name)

		# if verbose:
		# 	print 'Uploaded to %s' % (url)

		return url

	else:
		print "Warning: AWS API credentials not supplied." 
		return None

def truthy(value):
	if value == 'True':
		return True
	elif value == 'False':
		return False
	return value		