import os
import sys
import datetime
import traceback        

from boto.s3.key import Key
import boto.s3
from bs4 import BeautifulSoup
import codecs    
from jinja2 import Template, FileSystemLoader, Environment
from pyslack import SlackClient
import webbrowser

from .core.models import LinkSet
from .tests.basic_site_quality import test_basic_site_quality
from .tests.basic_page_quality import test_basic_page_quality
from .tests.page_spell_check import test_basic_spell_check
from .tests.w3c_compliance import test_w3c_compliance
from .tests.screenshots import test_screenshots
from .tests.lint_js import test_lint_js
from .tests.pagespeed import test_pagespeed

            
def testSite(credentials, canonical_domain, domain_aliases, test_id, full=False, recursive=True, options=None, verbose=False):
    if verbose:
        if full:
            print "FULL SITE TEST :: %s"%(canonical_domain)
        else:
            print "BASIC SITE TEST :: %s"%(canonical_domain)

    #recursive = False
    
    #TODO: Add screenshots from browserstack http://www.browserstack.com/screenshots/api
    #TODO: Add linting for css and js files and make sure they are being served as GZIP
    #TODO: Add social meta tag verification
    #TODO: Pagespeed Insights: https://developers.google.com/speed/docs/insights/v1/getting_started#intro

    #TODO: Add to python index and readthedocs

    start_time = datetime.datetime.now()

    if not options:
        options = {
            'special_dictionary':[],
            'ignore_query_string_keys':[],
            'alias_query_strings':[],
            'ignore_validation_errors':[],
            'skip_test_urls':[],
            'skip_urls':[]
        }


    if 'special_dictionary' not in options:
        special_dictionary = []
    else:
        special_dictionary = options['special_dictionary']

    if 'ignore_query_string_keys' not in options:
        ignore_query_string_keys = []
    else:
        ignore_query_string_keys = options['ignore_query_string_keys']

    if 'alias_query_strings' not in options:
        alias_query_strings = []
    else:
        alias_query_strings = options['alias_query_strings']

    if 'ignore_validation_errors' not in options:
        ignore_validation_errors = []
    else:
        ignore_validation_errors = options['ignore_validation_errors']


    if 'skip_test_urls' not in options:
        skip_test_urls = []
    else:
        skip_test_urls = options['skip_test_urls']

    if 'skip_urls' not in options:
        skip_urls = []
    else:
        skip_urls = options['skip_urls']




    
    #Load pages, starting with homepage    
    set = LinkSet(full, canonical_domain, domain_aliases, ignore_query_string_keys, alias_query_strings, skip_test_urls, skip_urls)
    homepage_link = set.get_or_create_link_object(canonical_domain, None)
    if homepage_link:
        set.load_link(homepage_link, recursive)


    #Load any additional from sitemap
    sitemap_url = "%ssitemap.xml"%(canonical_domain) if canonical_domain.endswith("/") else "%s/sitemap.xml"%(canonical_domain)
    sitemap_link = set.get_or_create_link_object(sitemap_url, None)
    if sitemap_link:
        set.load_link(sitemap_link, recursive)
   


    #if recursive:
    #1. Site quality test
    try:
        test_basic_site_quality(set, verbose)
    except:
        print "Error running site quality check: %s"%(traceback.format_exc())

    #2. Page quality test
    try:
        test_basic_page_quality(set, verbose)
    except Exception:        
        print "Error running page quality check: %s"%(traceback.format_exc())




    #3. Spell Check test
    try:
        print 'running spellcheck...'
        test_basic_spell_check(set, special_dictionary, verbose)
    except Exception:        
        print "Error running spellcheck: %s"%(traceback.format_exc())

    #4. Lint JS
    try:
        test_lint_js(set, verbose)
    except Exception:        
        print "Error linting JS: %s"%(traceback.format_exc())


    




    if full:

        #5. Page Speed
        try:
            test_site_loading_optimized(set, credentials, verbose)
        except Exception:        
           print "Error testing site loading optimization: %s"%(traceback.format_exc())

        #6. W3C Compliance test
        try:
            test_w3c_compliance(set, ignore_validation_errors, verbose)
        except Exception:        
            print "Error validating with w3c: %s"%(traceback.format_exc())

        try:
            #7. Browser Screenshots
            test_screenshots(set, credentials, verbose)
        except Exception:        
            print "Error generating screenshots: %s"%(traceback.format_exc())
    

    end_time = datetime.datetime.now()

    results = {
        'full':full,
        'set':set,
        'site':set.current_links[canonical_domain],
        'start_time':start_time,
        'end_time':end_time,
        'duration':end_time-start_time
    }


    html = render_results(results)
    report_url = save_results(html, test_id, credentials, verbose)
    results['report_url'] = report_url
    open_results(report_url)

    notify_results(results, credentials)

    return results


# def test(module, links):

#   test_results = {
#       'title':'Test Title',
#       'html':'Example html',
#       'error_messages':[
#           'Error Message 1',
#           'Error Message 2',
#       ],
#       'success_messages':[
#           'Success Message 1',
#           'Success Message 2',
#       ]
#   }
#   return test_results

def render_and_save_results(results, template_name, output_path):
    #TODO
    pass


def render_results(results, template_file = 'templates/results.html'):
    
    templateLoader = FileSystemLoader( searchpath="/" )
    templateEnv = Environment( loader=templateLoader )

    TEMPLATE_FILE = os.path.join(os.path.dirname(__file__), template_file)
    template = templateEnv.get_template( TEMPLATE_FILE )

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

    if 'slack' in credentials and 'SLACK_TOKEN' in credentials['slack']:
        SLACK_TOKEN = credentials['slack']['SLACK_TOKEN']
        SLACK_CHANNEL = credentials['slack']['SLACK_CHANNEL']
        SLACK_USERNAME = credentials['slack']['SLACK_USERNAME']

        client = SlackClient(SLACK_TOKEN)

        message_output = "TEST RESULTS for \"%s\"\n\n"%(results['site'].title)

        message_output += ("Full Report: %s\n\n"%(results['report_url']))

        message_output += ('SCORE: %s (Lower is better, Best is 0-0-X)\n\n'%(results['set'].get_score()))

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

def stripHtmlTags(htmlTxt):
    if htmlTxt is None:
        return None
    else:
        return ''.join(BeautifulSoup(htmlTxt).findAll(text=True)) 
