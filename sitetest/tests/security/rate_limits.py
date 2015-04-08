# -*- coding: utf-8 -*-
import sys
import traceback  
import urllib2
import httplib
import threading
import time

from ...core.models import HEADERS

def test_rate_limits(site, total_count=500, verbose=False):
    """
    Hammer the homepage to see if it hits any limits
    """

    if verbose:
        print '\n\nRunning rate limit tests...\n'

    url = site.canonical_domain
    #TODO --- allow urls to test to be configurable

    success_count = 0
  
    counter = {
        'total_count':total_count,
        'current_count':0,
        'success_count': 0,
        'error_count': 0,
    }
    
    start = time.time()
    urls = [url for x in range(total_count)]
    
    def fetch_url(url, counter):
        
        code = None
        try:
            request = urllib2.Request(url, headers=HEADERS)        
            response = urllib2.urlopen(request)
            code = response.code
            html = response.read()                    
            counter['success_count'] += 1
        except urllib2.HTTPError, e:
            code = e.code            
            # print '---> urllib2.HTTPError %s - %s'%(e.code, e.headers)            
            counter['error_count'] += 1
        except urllib2.URLError, e:
            code = e.reason
            counter['error_count'] += 1
        except httplib.BadStatusLine as e:
            code = "Bad Status Error"  
            counter['error_count'] += 1          
        except Exception:
            code = "Unkown Exception"
            counter['error_count'] += 1            

        counter['current_count'] += 1
        # if verbose:
        #     print "Attempt %s/%s: %s"%(counter['current_count'], counter['total_count'], code)
       

    threads = [threading.Thread(target=fetch_url, args=(url,counter)) for url in urls]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    elapsed = (time.time() - start)
    average = elapsed / total_count
    loads_per_second_allowed = counter['success_count'] / elapsed
    success_rate = (float(counter['success_count']) / float(total_count)) * float(100)
    success_rate_formatted = "{0:.0f}%".format(success_rate)
    message = "%s loads were attempted on %s. %s were successful."%(total_count, \
            url, counter['success_count'])
        
    if verbose:
        print message

    site.add_info_message(message)

        