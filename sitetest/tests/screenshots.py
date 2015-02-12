import sys
import urllib2
import urllib
import json
import base64
from ..core.models import HEADERS

def test_screenshots(set, credentials, max_test_count=20, verbose=False):
    
    if 'browserstack' in credentials and 'USERNAME' in credentials['browserstack']:
        
        username = credentials['browserstack']['USERNAME']
        password = credentials['browserstack']['PASSWORD']
        user_data = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')


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
        print "Warning: Browserstack API credentials not supplied."