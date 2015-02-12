import sys
import urllib2
import json
from ..core.models import HEADERS

def test_pagespeed(set, credentials, max_test_count=100, verbose=False):
    
    if 'google' in credentials and 'API_KEY' in credentials['google']:

        if verbose:
            print '\n\nRunning site speed and optimization tests...\n'
        
        API_KEY = credentials['google']['API_KEY']

        total = len(set.parsed_links)
        count = 0
        tested_count = 0

        for link_url in set.parsed_links:
            if verbose:
                print "%s/%s"%(count, total)
            count += 1

            link = set.parsed_links[link_url]
            
            if link.is_internal == True and not link.skip_test == True:
                
                if tested_count < max_test_count:
                    tested_count += 1
                    testing_url = 'https://www.googleapis.com/pagespeedonline/v1/runPagespeed?url=%s&key=%s'%(link.url, API_KEY)                   
                    
                    #print testing_url

                    request = urllib2.Request(testing_url, headers=HEADERS)
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