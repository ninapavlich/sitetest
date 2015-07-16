import sys
import urllib2
import json
import urlparse
from ..core.models import HEADERS

def test_pagespeed(set, credentials, options, max_test_count=1000, verbose=False):
    
    if 'google' in credentials and 'API_KEY' in credentials['google']:

        if verbose:
            print '\n\nRunning site speed and optimization tests...\n'
        
        API_KEY = credentials['google']['API_KEY']

        use_basic_auth = False if 'use_basic_auth' not in options else truthy(options['use_basic_auth'])
        basic_auth_username = '' if use_basic_auth==False else options['basic_auth_username']
        basic_auth_password = '' if use_basic_auth==False else options['basic_auth_password']

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

                    if use_basic_auth:
                        parsed = urlparse.urlparse(link.url)
                        updated_location = "%s:%s@%s"%(basic_auth_username, basic_auth_password, parsed.netloc)
                        parsed = parsed._replace(netloc=updated_location)
                        updated = urlparse.urlunparse(parsed)
                        url = updated
                    else:
                        url = link.url

                    testing_url = 'https://www.googleapis.com/pagespeedonline/v1/runPagespeed?url=%s&key=%s'%(url, API_KEY)

                    request = urllib2.Request(testing_url)
                    response = urllib2.urlopen(request)
                    
                    try:
                        result = json.load(response)
                    except:
                        result = None
                        if verbose:
                            print "Error parsing json %s - %s"%(link.url, response.read())


                    if result:
                        link.loading_score = result

                        score = int(result['score'])
                        if score < 25:
                            link.loading_score_group = "low"
                        elif score < 50:
                            link.loading_score_group = "medium-low"
                        elif score < 75:
                            link.loading_score_group = "medium"
                        elif score < 90:
                            link.loading_score_group = "medium-high"
                        if score > 90:
                            link.loading_score_group = "high"



    else:
        print "Warning: Google API credentials not supplied."

def truthy(value):
    if value == 'True':
        return True
    elif value == 'False':
        return False
    return value                