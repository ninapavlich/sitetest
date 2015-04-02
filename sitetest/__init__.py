import os
import sys
import datetime
import traceback        

from boto.s3.key import Key
import boto.s3
from bs4 import BeautifulSoup
import codecs    
import htmlmin
from jinja2 import Template, FileSystemLoader, Environment
from pyslack import SlackClient
import webbrowser

from .core.sitemap import SiteMaps
from .core.models import LinkSet
from .tests.basic_site_quality import test_basic_site_quality
from .tests.basic_page_quality import test_basic_page_quality
from .tests.page_spell_check import test_basic_spell_check
from .tests.w3c_compliance import test_w3c_compliance
from .tests.screenshots import test_screenshots
from .tests.lint_js import test_lint_js
from .tests.pagespeed import test_pagespeed
from .tests.selenium_tests import test_selenium
from .tests.security.rate_limits import test_rate_limits
from .tests.security.ua_blocks import test_ua_blocks


            
def testSite(credentials, canonical_domain, domain_aliases, starting_url, test_id, options=None):
    
    # recursive = False
    
    #TODO: Add to python index and readthedocs

    start_time = datetime.datetime.now()

    if not options:
        options = {
            'special_dictionary':[],
            'ignore_query_string_keys':[],
            'alias_query_strings':[],
            'ignore_validation_errors':[],
            'skip_test_urls':[],
            'skip_urls':[],
            'recursive':True,
            'test_media':True,
            'test_external_links':True,
            'run_third_party_tests':False,
            'run_security_tests':False,
            'verbose':True,
            'output_unloaded_links':True,
            'max_parse_count':None,
            'automated_tests_dir':None,
            'screenshots':{
                'default':[1200, 800],
                'mobile':[375, 667]
            }
        }


    recursive = True if 'recursive' not in options else truthy(options['recursive'])

    test_media = True if 'test_media' not in options else truthy(options['test_media'])

    test_external_links = True if 'test_external_links' not in options else truthy(options['test_external_links'])

    run_third_party_tests = False if 'run_third_party_tests' not in options else truthy(options['run_third_party_tests'])

    run_security_tests = False if 'run_security_tests' not in options else truthy(options['run_security_tests'])

    verbose = True if 'verbose' not in options else truthy(options['verbose'])

    output_unloaded_links = True if 'output_unloaded_links' not in options else truthy(options['output_unloaded_links'])
    
    special_dictionary = [] if 'special_dictionary' not in options else options['special_dictionary']

    ignore_query_string_keys = [] if 'ignore_query_string_keys' not in options else options['ignore_query_string_keys']

    alias_query_strings = [] if 'alias_query_strings' not in options else options['alias_query_strings']

    ignore_validation_errors = [] if 'ignore_validation_errors' not in options else options['ignore_validation_errors']

    skip_test_urls = [] if 'skip_test_urls' not in options else options['skip_test_urls']

    skip_urls = [] if 'skip_urls' not in options else options['skip_urls']

    max_parse_count = None if 'max_parse_count' not in options else options['max_parse_count']

    automated_tests_dir = None if 'automated_tests_dir' not in options else options['automated_tests_dir']


    if verbose:
        print "SITE TEST :: %s Recursive:%s Media:%s External Links:%s 3rd Party:%s MAX:%s"%(canonical_domain, recursive, test_media, test_external_links, run_third_party_tests, max_parse_count)


    

    #Load pages, starting with homepage    
    set = LinkSet(test_media, test_external_links, canonical_domain, domain_aliases, max_parse_count, ignore_query_string_keys, alias_query_strings, skip_test_urls, skip_urls, verbose)
    homepage_link = set.get_or_create_link_object(canonical_domain, None)

    if recursive == True:
        sitemap = SiteMaps(canonical_domain, set, recursive)
        sitemap.run()
    
    starting_link = set.get_or_create_link_object(starting_url, None)
    if starting_link:
        set.load_link(starting_link, recursive, 200, True)


    
    #if recursive:
    # Site quality test
    try:
        test_basic_site_quality(set, verbose)
    except:
        print "Error running site quality check: %s"%(traceback.format_exc())

    # #Page quality test
    try:
        test_basic_page_quality(set, recursive, verbose)
    except Exception:        
        print "Error running page quality check: %s"%(traceback.format_exc())


    #Spell Check test
    # try:
    #     test_basic_spell_check(set, special_dictionary, verbose)
    # except Exception:        
    #     print "Error running spellcheck: %s"%(traceback.format_exc())

    """
    #Lint JS
    try:
        test_lint_js(set, verbose)
    except Exception:        
        print "Error linting JS: %s"%(traceback.format_exc())
    """
    

    # if automated_tests_dir:
    #     try:
    #         test_selenium(set, automated_tests_dir, verbose)
    #     except Exception:        
    #         print "Error running Selenium tests: %s"%(traceback.format_exc())



    if run_third_party_tests==True:

        #Page Speed
        try:
            test_pagespeed(set, credentials, 1000, verbose)
        except Exception:        
           print "Error testing site loading optimization: %s"%(traceback.format_exc())

        # W3C Compliance test
        try:
            test_w3c_compliance(set, ignore_validation_errors, 20, verbose)
        except Exception:        
            print "Error validating with w3c: %s"%(traceback.format_exc())

    try:
        #Browser Screenshots
        test_screenshots(set, credentials, options, test_id, 20, verbose)
    except Exception:        
        print "Error generating screenshots: %s"%(traceback.format_exc())



    # if run_security_tests==True:
    #     try:
    #         test_rate_limits(set, 500, verbose)
    #     except:
    #         print "Error testing rate limits: %s"%(traceback.format_exc())

    #     try:
    #         ua_test_list = {
    #             'A1 Website Download/5.1.0 (+http://www.microsystools.com/products/website-download/) miggibot':{
    #                 'expected_code':403
    #             }
    #         }
    #         test_ua_blocks(set, ua_test_list, verbose)
    #     except:
    #         print "Error testing ua blocks: %s"%(traceback.format_exc())            
    
        


    end_time = datetime.datetime.now()

    results = {
        'test_media':test_media,
        'test_external_links':test_external_links,
        'run_third_party_tests':run_third_party_tests,
        'run_security_tests':run_security_tests,
        'output_unloaded_links':output_unloaded_links,
        'set':set,
        'site':set.current_links[canonical_domain],
        'start_time':start_time,
        'end_time':end_time,
        'duration':end_time-start_time,
        'max_parse_count':max_parse_count
    }

    html = render_results(results)

    try:
        html_minified = htmlmin.minify(html, True, True)
    except Exception:
        print "Error minifying html: %s"%(traceback.format_exc())
        html_minified = html
        
    report_url = save_results(html_minified, test_id, credentials, verbose)
    results['report_url'] = report_url
    open_results(report_url)

    notify_results(results, credentials)

    return results


def render_and_save_results(results, template_name, output_path):
    #TODO
    pass


def render_results(results, template_file = 'results.html'):
    
    templateLoader = FileSystemLoader( [os.path.join(os.path.dirname(__file__), 'templates/')] )
    templateEnv = Environment( loader=templateLoader )

    template = templateEnv.get_template( template_file )
    rendered = template.render( results )
    return rendered


def save_results(html, test_id, credentials, verbose):

    results_dir = os.path.join(os.path.dirname(__file__), 'test_results')
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    filename = "%s.html"%(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"))
    results_file = os.path.join(results_dir, filename)

    save_results_local(html, results_file, test_id, verbose)
    try:
        report_url = save_results_aws(results_file, test_id, credentials, verbose)
    except Exception:        
        print "Error posting results to AWS: %s"%(traceback.format_exc())
        report_url = None

    if report_url:
        delete_results_local(results_file, verbose)
    else:
        report_url = "file://%s"%results_file       
        

    return report_url

def delete_results_local(output_path, verbose):
    os.remove(output_path)

def save_results_local(html, output_path, test_id, verbose):
    
    

    # process Unicode text
    with codecs.open(output_path,'w',encoding='utf8') as file:
        file.write(html)

    #element_ascii = html.encode('ascii', 'ignore')
    # file = open(output_path, "w")
    # file.write(html)
    file.close()

def save_results_aws(file_name, test_id, credentials, verbose):
    

    if 'aws' in credentials and 'AWS_ACCESS_KEY_ID' in credentials['aws']:
        AWS_ACCESS_KEY_ID = credentials['aws']['AWS_ACCESS_KEY_ID']
        AWS_SECRET_ACCESS_KEY = credentials['aws']['AWS_SECRET_ACCESS_KEY']
        AWS_STORAGE_BUCKET_NAME = credentials['aws']['AWS_STORAGE_BUCKET_NAME']
        AWS_RESULTS_PATH = credentials['aws']['AWS_RESULTS_PATH']

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
        k.key = u"%s/%s/%s"%(AWS_RESULTS_PATH, test_id, base_name)
        k.set_contents_from_filename(file_name, cb=percent_cb, num_cb=10)
        k.set_acl('public-read')

        url = "http://s3.amazonaws.com/%s/%s/%s/%s" % (AWS_STORAGE_BUCKET_NAME, AWS_RESULTS_PATH, test_id, base_name)
        return url

    else:
        print "Warning: AWS API credentials not supplied." 
        return None

def open_results(path):

    
    new = 2 # open in a new tab, if possible

    # open an HTML file on my own (Windows) computer
    if 'http' not in path:
        url = "file://%s"%(path)
    else:
        url = path

    webbrowser.open(url,new=new)

def notify_results(results, credentials):
    try:
        if 'slack' in credentials and 'SLACK_TOKEN' in credentials['slack']:
            SLACK_TOKEN = credentials['slack']['SLACK_TOKEN']
            SLACK_CHANNEL = credentials['slack']['SLACK_CHANNEL']
            SLACK_USERNAME = credentials['slack']['SLACK_USERNAME']

            client = SlackClient(SLACK_TOKEN)

            
            message_output = "Score %s for Test of \"%s\"\n\n"%(results['set'].get_score(), results['site'].title)

            message_output += "Full Report: %s\n\n"%(results['report_url'])        

            # for message in results['messages']['success']:
            #     message_output += (message+'\n\n')
            # for message in results['messages']['error']:
            #     message_output += (message+'\n\n')
            # for message in results['messages']['warning']:
            #     message_output += (message+'\n\n')
            # for message in results['messages']['info']:
            #     message_output += (message+'\n\n')

            
            stripped = stripHtmlTags(message_output)
            client.chat_post_message(SLACK_CHANNEL, stripped, username=SLACK_USERNAME) 
        else:
            print "Warning: Slack API credentials not supplied." 
    except Exception:
        print "Error sending notification to Slack: %s"%(traceback.format_exc())

def stripHtmlTags(htmlTxt):
    if htmlTxt is None:
        return None
    else:
        return ''.join(BeautifulSoup(htmlTxt).findAll(text=True)) 

def truthy(value):
    if value == 'True':
        return True
    elif value == 'False':
        return False
    return value
