import gzip
import jsbeautifier
import os
import sys
import pyjslint
import urllib2
import traceback 
from itertools import izip

def test_lint_js(set, verbose=False):
    """
    For each page, make sure there is a unique title and description
    """

    if verbose:
        print '\n\nRunning JS Lint test...\n'


    total_js_error_count = 0
    
    total = len(set.parsed_links)
    count = 0

    for link_url in set.parsed_links:
        link = set.parsed_links[link_url]

        if verbose:
            print "%s/%s"%(count, total)
        count += 1
    

        if link.is_javascript:
            
            link_source = link.content.decode('utf-8').encode('ascii', 'ignore')


            if link_source:

                try:
                    beautified_link_source = jsbeautifier.beautify(link_source)
                except Exception:        
                    print "Error beautifying JS: %s"%(traceback.format_exc())
                    beautified_link_source = link_source

                raw_js_errors = pyjslint.check_JSLint(beautified_link_source)
                #js_errors = [str(error) for error in raw_js_errors]

                js_errors = []
                for source, full_message in grouped(raw_js_errors[1:], 2):
                    full_message = full_message.strip()

                    if full_message.startswith("Lint"):
                        message = full_message.split(":")[1].strip()
                        line_ref = full_message.split(":")[0].strip()
                        numbers = [int(s) for s in line_ref.split() if s.isdigit()]

                        error = {
                            'lastLine':numbers[0],
                            'lastColumn':numbers[1],
                            'message':full_message,
                            'src':source
                        }
                        
                        js_errors.append(error)

                
                total_js_error_count += len(js_errors)
                link.validation = {
                    'errors':js_errors
                }
                if len(js_errors) > 0:
                    message = "Found %s lint errors."%(len(js_errors))
                    link.add_info_message(message)
            
#/*jslint white: true */

            

            
    if total_js_error_count > 0:
        set.add_info_message("%s js lint errors found."%(total_js_error_count))             


    #DELETE TMP FOLDER
    try:
        shutil.rmtree('tmp')
    except:
        pass
        





def grouped(iterable, n):
    "s -> (s0,s1,s2,...sn-1), (sn,sn+1,sn+2,...s2n-1), (s2n,s2n+1,s2n+2,...s3n-1), ..."
    return izip(*[iter(iterable)]*n)