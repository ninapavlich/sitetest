import urllib2
import json

def test_site_loading_optimized(set, credentials):
    
    if 'google' in credentials and 'API_KEY' in credentials['google']:

        print 'Running site speed and optimization tests...'
        
        API_KEY = credentials['google']['API_KEY']

        for link_url in set.parsed_links:
            link = set.parsed_links[link_url]
            
            if link.is_internal():
                

                testing_url = 'https://www.googleapis.com/pagespeedonline/v1/runPagespeed?url=%s&key=%s'%(link.url, API_KEY)
                
                hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                   'Accept-Encoding': 'none',
                   'Accept-Language': 'en-US,en;q=0.8',
                   'Connection': 'keep-alive'}

                request = urllib2.Request(testing_url, headers=hdr)
                response = urllib2.urlopen(request)
                
                result = json.load(response)
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