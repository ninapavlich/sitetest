# -*- coding: utf-8 -*-
import sys
import traceback  
import urllib2
import httplib
import threading
import time


def test_ua_blocks(site, ua_test_list, verbose=False):
    """
    Test user agents to make sure they're blocked

    ua_test_list = {
        'User Agent Example':{
            'expected_code':403,
            'test_urls':[]
        }
    }
    """

    if verbose:
        print '\n\nRunning User Agent tests...\n'

    default_url = site.canonical_domain
    error_count = 0
       
    for user_agent_key, user_agent in ua_test_list.iteritems():
        if 'expected_code' in user_agent:
            expected_code = user_agent['expected_code']
        else:
            expected_code = 403
        

        if 'test_urls' in user_agent:
            for url in user_agent['test_urls']:
               

                success = test_load(site, url, user_agent_key, expected_code)
                if success == False:
                    error_count += 1
                    

        else:
            success = test_load(site, default_url, user_agent_key, expected_code)
            if success == False:
                error_count += 1

        
    if error_count > 0:
        message = "%s pages incorrectly handled user agents."%(error_count)
        site.add_error_message(message)

def test_load(site, url, user_agent, expected_code):    
    
    try:
        link = site.current_links[url]
    except:
        link = None

    code = load_ua(url, user_agent)
    if code != expected_code:
        
        message = "Page %s incorrectly handled user agent %s. Expected %s received %s"%\
        (link.url, user_agent, expected_code, code)

        if link:
            link.add_error_message(message)
        else:
            site.add_error_message(message)

        return False
    return True


def load_ua(url, user_agent):    

    TEST_HEADERS = {'User-Agent': user_agent,
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', #TODO: image/webp
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'
    }

    code = None
    try:
        request = urllib2.Request(url, headers=TEST_HEADERS)        
        response = urllib2.urlopen(request)
        code = response.code
    except urllib2.HTTPError, e:
        code = e.code
    except urllib2.URLError, e:
        code = e.reason
    except httplib.BadStatusLine as e:
        code = "Bad Status Error"
    except Exception:
        code = "Unkown Exception"

    return code

        