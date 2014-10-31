import datetime
import urllib2
import urllib
import urlparse
import cgi
import re
import os
from bs4 import BeautifulSoup

TYPE_OTHER = 'other'
TYPE_MAILTO = 'mailto'
TYPE_INTERNAL = 'internal'
TYPE_EXTERNAL = 'external'

MEDIA_SUFFIXES = [
    '.png', '.jpg', '.gif',
    '.doc', '.pdf', '.ppt', '.zip', '.gzip', '.mp3', '.rar', '.exe', 
    '.avi', '.mpg', '.tif', '.wav', '.mov', '.psd', '.ai', '.wma',
    '.eps','.mp4','.bmp','.indd','.swf','.jar','.dmg','.iso','.flv',
    '.gz','.fla','.html','.ogg','.sql'
]

def retrieve_all_urls(page_url, canonical_domain, domain_aliases, messages, recursive, include_media, ignore_query_string_keys=None, referer=None, current_links=None, parsed_links=None, verbose=False):
    if current_links is None:
        current_links = {}

    if parsed_links is None:
        parsed_links = []

    if ignore_query_string_keys is None:
        ignore_query_string_keys = []


    normalized_page_url = get_normalized_href(page_url, canonical_domain, domain_aliases, page_url, ignore_query_string_keys)
    page_link = get_or_create_link_object(page_url, current_links, canonical_domain, domain_aliases, referer)
    page_link_type = get_link_type(normalized_page_url, canonical_domain, domain_aliases)

    if page_link['is_media'] and include_media == False:
        return (current_links, parsed_links, messages)

    if verbose:
        print ">>> Parse %s (<<< %s)"%(normalized_page_url, referer)


    #If page is a real link (e.g. not mailto or ftp), actually test the url
    if page_link_type == TYPE_INTERNAL or page_link_type == TYPE_EXTERNAL:
        
        response, messages = load_link_object(page_link, canonical_domain, domain_aliases, messages)

    else:
        response = None



    #record that we have parsed it
    if normalized_page_url not in parsed_links:
        parsed_links.append(normalized_page_url)
    else:
        #if it's already in there, dont parse children
        return (current_links, parsed_links, messages)
    
    #parse child links of internal pages only
    if response and page_link_type == TYPE_INTERNAL:

        try:
            soup = BeautifulSoup(response)
        except:
            soup = None
            messages['error'].append("Error parsing HTML on page %s"%(page_url))

    
        if soup:

            page_link['html'] = soup.prettify()

            page_urls = get_urls_on_page(soup)

            for href in page_urls:

                normalized_href = get_normalized_href(href, canonical_domain, domain_aliases, page_url, ignore_query_string_keys)                
                link = get_or_create_link_object(normalized_href, current_links, canonical_domain, domain_aliases, page_url)

                if not normalized_href in page_link['links'] and normalized_href != normalized_page_url:
                    page_link['links'].append(normalized_href)
        
        #Let's do it again!
        if recursive:
            for child_link in page_link['links']:
                if child_link not in parsed_links:
                    #print 'parse child page %s'%(child_link)
                    current_links, parsed_links, messages = retrieve_all_urls(child_link, canonical_domain, domain_aliases, messages, recursive, include_media, ignore_query_string_keys, normalized_page_url, current_links, parsed_links, verbose)
    if verbose:           
        print "Parsed %s links"%(len(parsed_links))

    return (current_links, parsed_links, messages)

def get_urls_on_page(soup):
    output = []

    #Traditional hyperlinks
    for a in soup.findAll('a'):

        try:
            href = a['href']  
            output.append(href)      
        except:
            href = None
    

    #Sitemap links
    for url in soup.findAll('url'):
        url_loc = None
        for loc in url.findAll('loc'):
            if loc.text:
                output.append(loc.text)

    #CSS Links
    for a in soup.findAll('link'):
        try:
            href = a['href']  
            rel = a['rel'][0].strip()
            if rel == 'stylesheet':
                output.append(href)      
        except:
            href = None 

    #JS Links
    for a in soup.findAll('script'):
        try:
            src = a['src']  
            output.append(src)      
        except:
            href = None 

    return output

def get_normalized_href(url, canonical_domain, domain_aliases, normalized_parent_url=None, ignore_query_string_keys=None):
    if ignore_query_string_keys is None:
        ignore_query_string_keys = []

    if url.startswith('//'):
        if canonical_domain.startswith('https'):
            url = u"https:%s"%(url)
        else:
            url = u"http:%s"%(url)

    #Normalize url by converting to lowercase: 
    normalized = url.lower()

    dequeried_parent_url = clear_query_string(normalized_parent_url)

    #Remove double slashes: 
    #normalized = url.lower()

    #for internal urls, make main domain present
    link_type = get_link_type(url, canonical_domain, domain_aliases)
    if link_type == TYPE_INTERNAL:

        #remove anything after the hashtag:
        url = url.split('#')[0]

        if canonical_domain not in url:
            #First see if it has an alias domain
            for alias in domain_aliases:
                if alias.lower() in url.lower():
                    normalized = url.lower().replace(alias.lower(), canonical_domain)
                    #print "Replace alias domain in %s with canonical: %s"%(url, normalized)
                    

            #Next, does it use an absolute path?
            if url.startswith('/'):
                if canonical_domain.endswith('/'):
                    normalized = "%s%s"%(canonical_domain, url[1:])
                else:
                    normalized = "%s%s"%(canonical_domain, url)
                #print "relative from root, replacd %s with %s"%(url, normalized)
                

            #if not, it must be relative to the parent
            elif normalized_parent_url:
                if dequeried_parent_url.endswith('/'):
                    normalized = "%s%s"%(dequeried_parent_url, url)
                else:
                    normalized = "%s/%s"%(dequeried_parent_url, url)

                #print "relative from parent, replacd %s with %s"%(url, normalized)
                
        #Next remove unwanted query strings:
        normalized = clean_query_string(normalized, ignore_query_string_keys)


    else:
        normalized = url


    return normalized


def clean_query_string(url, ignore_query_string_keys):
   
    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    for unwanted_key in ignore_query_string_keys:
        if unwanted_key in query:
            del(query[unwanted_key])

    url_parts[4] = urllib.urlencode(query)
    new_url = urlparse.urlunparse(url_parts)

   
    return new_url

def clear_query_string(url):
    #Remove all query params from url
    url_parts = list(urlparse.urlparse(url))
    url_parts[4] = urllib.urlencode({})
    new_url = urlparse.urlunparse(url_parts)

    return new_url    

def load_link_object(link, canonical_domain, domain_aliases, messages, expected_code=200):

    link_url = link['url']

    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

    request = urllib2.Request(link_url, headers=hdr)
    response = None
            
    try:

        start_time = datetime.datetime.now()
        response = urllib2.urlopen(request)
        end_time = datetime.datetime.now()
        link['response_code'] = 200
        link['response'] = response#u"%s"%(response)
        link['response_content_type'] = response.info().getheader('Content-Type')

        load_time = end_time - start_time
        milliseconds = timedelta_milliseconds(load_time)
        link['response_load_time'] = milliseconds        

    except urllib2.HTTPError, e:
        #checksLogger.error('HTTPError = ' + str(e.code))

        try:
            link['response_code'] = e.code
        except:
            link['response_code'] = "Unknown HTTPError"

            

    except urllib2.URLError, e:
        #checksLogger.error('URLError = ' + str(e.reason))

        link['response_code'] = "Unknown URLError: %s"%(e.reason)

    # except httplib.HTTPException, e:
    #     #checksLogger.error('HTTPException')

    #     if expect_success:
    #         message = "Loading error on page <a href='#%s' class='alert-link'>%s</a> ERROR: %s"%(link['internal_page_url'], link_url, e)
    #         messages['error'].append(message)
    #         link['messages']['error'].append(message)

    except Exception:
        import traceback        
        link['response_code'] = "Unknown Exception: %s"%(traceback.format_exc())


    if expected_code != link['response_code']:
        message = "Loading error on page <a href='#%s' class='alert-link'>%s</a> Expected %s Received %s"%(link['internal_page_url'], link_url, expected_code, link['response_code'])
        messages['error'].append(message)
        link['messages']['error'].append(message)

    return response, messages


def get_or_create_link_object(url, current_urls, canonical_domain, domain_aliases, referer_url=None):
    if url in current_urls:
        link = current_urls[url]
        #print '%s exists already'%(link)
    else:
        link = create_link_object(url, canonical_domain, domain_aliases)
        url = link['url']
        current_urls[url] = link
        #print '%s is new'%(link)

    if referer_url and referer_url not in link['referers']:
        link['referers'].append(referer_url)

    return link

def create_link_object(url, canonical_domain, domain_aliases):
    parsed = urlparse.urlparse(url)
    name, extension = os.path.splitext(parsed.path)
    

    MEDIA_SUFFIXES
    return {
        'referers':[],
        'links':[],
        'messages':{
            'success':[],
            'error':[],
            'warning':[],
            'info':[],
        },
        'url':url,
        'internal_page_url':"load-test-result-%s"%(url),
        'encoded_url':urllib.quote_plus(url),
        'type':get_link_type(url, canonical_domain, domain_aliases),
        'path':parsed.path,
        'response_code':None,
        'response':None,
        'response_content_type':None,
        'html':None,
        'title':None,
        'content':None,
        'response_load_time':None,
        'description':None,
        'is_media':(extension.lower() in MEDIA_SUFFIXES),
        'sitemap_entry':None
    }

def get_link_type(url, canonical_domain, domain_aliases):
    #Internal, External, Mailto, Other

    if 'mailto:' in url.lower():
        return TYPE_MAILTO
    elif (':' in url.lower()) and (not 'http' in url.lower()):
        return TYPE_OTHER
    else:
        if '//' not in url.lower():
            return TYPE_INTERNAL
        else:

            #a link is internal if it is relative (doesnt start with http or https)
            # or one of the domain aliases is contained in the url
            if canonical_domain.lower() in url.lower():
                return TYPE_INTERNAL

            for domain in domain_aliases:
                if domain.lower() in url.lower():
                    return TYPE_INTERNAL
            return TYPE_EXTERNAL

def timedelta_milliseconds(td):
    return td.days*86400000 + td.seconds*1000 + td.microseconds/1000
