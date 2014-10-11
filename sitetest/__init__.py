import os
import sys
import datetime

from jinja2 import Template, FileSystemLoader, Environment

from .core.retrieve_all_urls import retrieve_all_urls
from .tests.basic_site_quality import test_basic_site_quality
from .tests.basic_page_quality import test_basic_page_quality
from .tests.page_spell_check import test_basic_spell_check
from .tests.w3c_compliance import test_w3c_compliance
from .tests.screenshots import test_screenshots

            
def testSite(credentials, canonical_domain, domain_aliases, test_id, full=False, recursive=True, special_dictionary = None, ignore_query_string_keys=None, ignore_validation_errors=None, verbose=False):
    if verbose:
        if full:
            print "FULL SITE TEST :: %s"%(canonical_domain)
        else:
            print "BASIC SITE TEST :: %s"%(canonical_domain)

    #TODO: boolean for check files and images
    #TODO: Add screenshots from browserstack http://www.browserstack.com/screenshots/api
    #TODO: Add w3c validation
    #TODO: Add linting for css and js files and make sure they are being served as GZIP
    #TODO: testSiteBasic, testURL, testSiteFull (include w3c compliance and browserstack)
    #TODO: Add to python index and readthedocs


    start_time = datetime.datetime.now()

    if not special_dictionary:
        special_dictionary = []

    if not ignore_query_string_keys:
        ignore_query_string_keys = []

    if not ignore_validation_errors:
        ignore_validation_errors = []

    messages = {
        'success':[],
        'error':[],
        'warning':[],
        'info':[],
    }
    current_links, parsed_links, messages = retrieve_all_urls(canonical_domain, canonical_domain, domain_aliases, messages, recursive, full, ignore_query_string_keys, None, None, None, verbose)
    
    if recursive:
        #1. Site quality test
        current_links, messages = test_basic_site_quality(current_links, canonical_domain, domain_aliases, messages, verbose)

    #2. Page quality test
    current_links, messages = test_basic_page_quality(current_links, canonical_domain, domain_aliases, messages, verbose)

    #3. Spell Check test
    current_links, messages = test_basic_spell_check(current_links, canonical_domain, domain_aliases, messages, special_dictionary, verbose)

    if full:
        #4. W3C Compliance test
        current_links, messages = test_w3c_compliance(current_links, canonical_domain, domain_aliases, messages, ignore_validation_errors, verbose)

        #5. Browser Screenshots
        #current_links, messages = test_screenshots(current_links, canonical_domain, domain_aliases, messages, verbose)

        #6. Lint JS and CSS
        #current_links, messages = test_basic_page_quality(current_links, canonical_domain, domain_aliases, messages, verbose)


    sorted_links = sorted(current_links)
    end_time = datetime.datetime.now()

    results = {
        'full':full,
        'messages':messages,
        'links':current_links,
        'sorted_links':sorted_links,
        'site':current_links[canonical_domain],
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
    report_url = save_results_aws(results_file, test_id, credentials, verbose)
    delete_results_local(results_file, verbose)

    return report_url

def delete_results_local(output_path, verbose):
    os.remove(output_path)

def save_results_local(html, output_path, test_id, verbose):
    import codecs
    

    # process Unicode text
    with codecs.open(output_path,'w',encoding='utf8') as file:
        file.write(html)

    #element_ascii = html.encode('ascii', 'ignore')
    # file = open(output_path, "w")
    # file.write(html)
    file.close()

def save_results_aws(file_name, test_id, credentials, verbose):
    import boto.s3

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

        import sys
        def percent_cb(complete, total):
            sys.stdout.write('.')
            sys.stdout.flush()

    from boto.s3.key import Key
    k = Key(bucket)
    k.key = u"%s/%s/%s"%(AWS_RESULTS_PATH, test_id, base_name)
    k.set_contents_from_filename(file_name, cb=percent_cb, num_cb=10)
    k.set_acl('public-read')

    url = "http://s3.amazonaws.com/%s/%s/%s/%s" % (AWS_STORAGE_BUCKET_NAME, AWS_RESULTS_PATH, test_id, base_name)
    return url

def open_results(path):

    import webbrowser
    new = 2 # open in a new tab, if possible

    # open an HTML file on my own (Windows) computer
    if 'http' not in path:
        url = "file://%s"%(path)
    else:
        url = path

    webbrowser.open(url,new=new)

def notify_results(results, credentials):
    from pyslack import SlackClient
    SLACK_TOKEN = credentials['slack']['SLACK_TOKEN']
    SLACK_CHANNEL = credentials['slack']['SLACK_CHANNEL']
    SLACK_USERNAME = credentials['slack']['SLACK_USERNAME']

    client = SlackClient(SLACK_TOKEN)

    message_output = "TEST RESULTS for \"%s\"\n\n"%(results['site']['title'])

    message_output += ('%s links were tested.\n\n'%(len(results['sorted_links'])))

    for message in results['messages']['success']:
        message_output += (message+'\n\n')
    for message in results['messages']['error']:
        message_output += (message+'\n\n')
    for message in results['messages']['warning']:
        message_output += (message+'\n\n')
    for message in results['messages']['info']:
        message_output += (message+'\n\n')

    message_output += ("Full Report: %s"%(results['report_url']))
    
    stripped = stripHtmlTags(message_output)
    client.chat_post_message(SLACK_CHANNEL, stripped, username=SLACK_USERNAME)  

def stripHtmlTags(htmlTxt):
    from bs4 import BeautifulSoup
    if htmlTxt is None:
        return None
    else:
        return ''.join(BeautifulSoup(htmlTxt).findAll(text=True)) 
