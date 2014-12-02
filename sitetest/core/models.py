# -*- coding: utf-8 -*-

import traceback     
import datetime
import httplib
import urllib2
import urllib
import urlparse
import cgi
import re
import os
import sys
from slugify import slugify
from bs4 import BeautifulSoup


TYPE_OTHER = 'other'
TYPE_MAILTO = 'mailto'
TYPE_INTERNAL = 'internal'
TYPE_EXTERNAL = 'external'

MEDIA_SUFFIXES = [
    '.png', '.jpg', '.jpeg', '.gif','.ico',
    '.doc', '.pdf', '.ppt', '.zip', '.gzip', '.mp3', '.rar', '.exe', 
    '.avi', '.mpg', '.tif', '.wav', '.mov', '.psd', '.ai', '.wma',
    '.eps','.mp4','.bmp','.indd','.swf','.jar','.dmg','.iso','.flv',
    '.gz','.fla','.ogg','.sql'
]

HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
   'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
   'Accept-Encoding': 'none',
   'Accept-Language': 'en-US,en;q=0.8',
   'Connection': 'keep-alive'}

class MessageSet(object):
    # __slots__ = ['success', 'error', 'warning', 'info',]

    success = None
    error = None
    warning = None
    info = None

    def __init__(self):
        self.success = []
        self.error = []
        self.warning = []
        self.info = []

    def get_score(self):
        error_score = sum([message.count for message in self.error])
        warning_score = sum([message.count for message in self.warning])
        info_score = sum([message.count for message in self.info])

        return "%s-%s-%s"%(error_score, warning_score, info_score)

class Message(object):
    __slots__ = ['message','count']

    message = None
    count = 1

    def __init__(self, message, count=1 ):
        self.message = message
        self.count = count

class SuccessMessage(Message):
    pass

class ErrorMessage(Message):
    pass

class WarningMessage(Message):
    pass

class InfoMessage(Message):
    pass

class BaseMessageable(object):
    messages = None

    def __init__(self):
        pass

    def get_score(self):
        if self.messages:
            return self.messages.get_score()
        return None
    

    def add_error_message(self, message, count=1):
        self.messages.error.append(ErrorMessage(message, count))

    def add_warning_message(self, message, count=1):
        self.messages.warning.append(WarningMessage(message, count))

    def add_info_message(self, message, count=1):
        self.messages.info.append(InfoMessage(message, count))

    def add_success_message(self, message, count=1):
        self.messages.success.append(SuccessMessage(message, count))

class LinkSet(BaseMessageable):
    include_media = False
    canonical_domain = None
    domain_aliases = None
    ignore_query_string_keys = []
    alias_query_strings = []

    current_links = {}
    loaded_links = {}
    parsed_links = {}
    parsable_links = {}

    def __init__(self, include_media, canonical_domain, domain_aliases, ignore_query_string_keys=None, alias_query_strings=None, skip_test_urls=None, skip_urls=None):

        self.messages = MessageSet()

        if ignore_query_string_keys is None:
            ignore_query_string_keys = []

        if alias_query_strings is None:
            alias_query_strings = []
        
        if skip_test_urls is None:
            skip_test_urls = []

        if skip_test_urls is None:
            skip_test_urls = []

        self.include_media = include_media
        self.canonical_domain = canonical_domain
        self.domain_aliases = domain_aliases
        self.ignore_query_string_keys = ignore_query_string_keys
        self.alias_query_strings = alias_query_strings
        self.skip_test_urls = skip_test_urls
        self.skip_urls = skip_urls

        super(LinkSet, self).__init__()    

        
    def load_link(self, page_link, recursive, expected_code=200, verbose=False):

        # max_count = 170
        # if len(self.parsed_links) > max_count:
        #     print "PARSED %s PAGES, turn recursive off"%(max_count)
        #     return

        if page_link.is_loadable_type(self.include_media) and page_link.url not in self.loaded_links:

            if verbose:
                trace_memory_usage()
                print ">>> Load Link %s (%s/%s, %s)"%(page_link.__unicode__(), len(self.parsed_links), len(self.parsable_links), len(self.current_links))

            load_successful, response = page_link.load(expected_code)
            
            if not load_successful:
                message = "Loading error on page <a href='#%s' class='pagelink alert-link'>%s</a> Expected %s Received %s"%(page_link.internal_page_url, page_link.url, 200, page_link.response_code)
                self.add_error_message(message)
            

            #record that we have parsed it
            if page_link.url not in self.loaded_links:
                self.loaded_links[page_link.url] = page_link
            

            #parse child links of internal pages only
            if page_link.has_response and page_link.is_internal():

                page_link.parse_response(response)

                #record that we have parsed it
                if page_link.url not in self.parsed_links:
                    self.parsed_links[page_link.url] = page_link
                
                #Let's do it again!
                if recursive:
                    for child_link_url in page_link.links:
                        if child_link_url not in self.parsed_links:                                                              
                            self.load_link(page_link.links[child_link_url], recursive, 200, verbose)
       



    def get_or_create_link_object(self, url, referer=None):
        incoming_url = url
        referer_url = None if not referer else referer.url

        url = self.get_normalized_href(url, referer_url)
    

        if not url or url == '':
            return None



        if url in self.current_links:
            link = self.current_links[url]
        else:
            link = LinkItem(url, self)
            self.current_links[url] = link
            
            if link.is_internal():
                self.parsable_links[link.url] = link

            #print ">>> Create Link %s (<<< %s)"%(link.__unicode__(), referer_url)

        if referer and referer.url != url:
            link.add_referer(referer)

        if self.alias_query_strings:
            alias_url = clean_query_string(url, self.alias_query_strings)
            if url != alias_url:
                link.alias_to = alias_url

        if self.skip_test_urls:
            for skip_url_pattern in self.skip_test_urls:
                regexp = re.compile(skip_url_pattern)
                if regexp.search(url):
                    link.skip_test = True

        if self.skip_urls:
            for skip_url_pattern in self.skip_urls:
                regexp = re.compile(skip_url_pattern)
                if regexp.search(url):
                    link.skip = True



        return link



    def get_link_type(self, url):
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
                if self.canonical_domain.lower() in url.lower():
                    return TYPE_INTERNAL

                for domain in self.domain_aliases:
                    if domain.lower() in url.lower():
                        return TYPE_INTERNAL
                return TYPE_EXTERNAL




    def get_normalized_href(self, url, normalized_parent_url=None):
        
        normalized = url
        if normalized.startswith('//'):
            if self.canonical_domain.startswith('https'):
                normalized = u"https:%s"%(normalized)
            else:
                normalized = u"http:%s"%(normalized)

        #Remove invalid bits
        normalized = url_fix(normalized)

        #If this is the homepage
        if normalized.strip('/') == self.canonical_domain.strip('/'):
            normalized = self.canonical_domain

        dequeried_parent_url = clear_query_string(normalized_parent_url)

        #remove anything after the hashtag:
        normalized = normalized.split('#')[0]

        #for internal urls, make main domain present
        link_type = self.get_link_type(url)
        if link_type == TYPE_INTERNAL:            

            if self.canonical_domain not in normalized:
                #First see if it has an alias domain
                for alias in self.domain_aliases:
                    if alias.lower() in normalized.lower():
                        normalized = normalized.lower().replace(alias.lower(), self.canonical_domain)
                        #print "Replace alias domain in %s with canonical: %s"%(url, normalized)
                        

                #Next, does it use an absolute path?
                if normalized.startswith('/'):
                    if self.canonical_domain.endswith('/'):
                        normalized = "%s%s"%(self.canonical_domain, normalized[1:])
                    else:
                        normalized = "%s%s"%(self.canonical_domain, normalized)
                    #print "relative from root, replacd %s with %s"%(url, normalized)
                    

                #if not, it must be relative to the parent
                elif normalized_parent_url:
                    if dequeried_parent_url.endswith('/'):
                        normalized = "%s%s"%(dequeried_parent_url, normalized)
                    else:
                        normalized = "%s/%s"%(dequeried_parent_url, normalized)

                    #print "relative from parent, replaced %s with %s"%(url, normalized)
                    
            #Next remove unwanted query strings:
            normalized = clean_query_string(normalized, self.ignore_query_string_keys)

        return normalized


           


    

class LinkItem(BaseMessageable):
    

    # __slots__ = ['_set', 'referers', 'image_links', 'hyper_links', 'css_links',
    # 'script_links', 'url', 'ending_url', 'starting_type', 'ending_type', 'path',
    # 'response_code', 'has_response','response_content_type','redirect_path',
    # 'html','content','response_load_time','description','is_media','alias_to','skip_test','has_sitemap_entry']


    has_response = False
    response_content_type = None    
    
    alias_to = None
    skip_test = False
    skip = False
    has_sitemap_entry = False


    def __init__(self, url, set):

        self.messages = MessageSet()

        self.referers = {}
        self.image_links = {}
        self.hyper_links = {}
        self.css_links = {}
        self.script_links = {}
        self._set = set
        self.url = self.ending_url = url
        parsed = urlparse.urlparse(url)
        name, extension = os.path.splitext(parsed.path)
        self.starting_type = self.ending_type = self._set.get_link_type(url)
        self.path = parsed.path
        self.is_media = (extension.lower() in MEDIA_SUFFIXES)

        super(LinkItem, self).__init__()


    def __unicode__(self):
        url = (u"%s-%s")%(self.url, self.ending_url) if self.url != self.ending_url else self.url
        type = (u"%s-%s")%(self.starting_type, self.ending_type) if self.starting_type != self.ending_type else self.starting_type

        return (u"%s [%s]")%(url, type)



    @property
    def internal_page_url(self):
        return slugify("load-test-result-%s"%(self.url))

    @property
    def encoded_url(self):
        return urllib.quote_plus(self.url)


    @property
    def links(self):
       return dict(self.image_links.items() + self.hyper_links.items() + self.css_links.items() + self.script_links.items())

    def is_loadable_type(self, include_media):
        is_internal_or_external = self.starting_type == TYPE_INTERNAL or self.starting_type == TYPE_EXTERNAL
        allow_media = (self.is_media and include_media) or (self.is_media==False)
        not_skip = self.skip == False
        return is_internal_or_external and allow_media and not_skip

    def is_internal(self):
        return self.ending_type == TYPE_INTERNAL and self.starting_type == TYPE_INTERNAL

    def is_internal_html(self):
        content_type = self.response_content_type
        return self.is_internal() and content_type and 'html' in content_type.lower()


    def is_javascript(self):
        content_type = self.response_content_type
        return content_type and 'javascript' in content_type.lower()

    def load(self, expected_code=200):


        request = urllib2.Request(self.url, headers=HEADERS)
        response = None
                
        try:

            start_time = datetime.datetime.now()
            response = urllib2.urlopen(request)
            end_time = datetime.datetime.now()
            self.response_code = response.code
            #self.response = response#u"%s"%(response)
            self.has_response = True
            self.response_content_type = response.info().getheader('Content-Type')
            self.ending_url = response.geturl()
            self.ending_type = self._set.get_link_type(self.ending_url)

            if self.url != self.ending_url:
                redirect_path = trace_path(self.url, [])
                self.redirect_path = redirect_path

                
            load_time = end_time - start_time
            milliseconds = timedelta_milliseconds(load_time)
            self.response_load_time = milliseconds        

        except urllib2.HTTPError, e:
            #checksLogger.error('HTTPError = ' + str(e.code))

            try:
                self.response_code = e.code

            except:
                self.response_code = "Unknown HTTPError"

                

        except urllib2.URLError, e:
            #checksLogger.error('URLError = ' + str(e.reason))

            self.response_code = "Unknown URLError: %s"%(e.reason)


        except httplib.BadStatusLine as e:
            self.response_code = "Bad Status Error. (Presumably, the server closed the connection before sending a valid response)"

        except Exception:
                
            self.response_code = "Unknown Exception: %s"%(traceback.format_exc())


        if expected_code != self.response_code:
            message = "Loading error on page <a href='#%s' class='alert-link'>%s</a> Expected %s Received %s"%(self.internal_page_url, self.url, expected_code, self.response_code)
            self.add_error_message(message)
            return (False, response)
        else:
            return (True, response)

    def parse_response(self, response):
        try:
            soup = BeautifulSoup(response)
        except:
            soup = None
            self.add_error_message("Error parsing HTML on page %s"%(self.url))

    
        if soup:

            page_html = soup.prettify()
            self.html = page_html
            
            enumerated_html_list = page_html.split("\n")
            counter = 0
            enumerated_html = ''
            for line in enumerated_html_list:
                new_line = "%s: %s"%(counter, line)
                enumerated_html += "%s\n"%(new_line)
                counter += 1
            self.enumerated_html = enumerated_html

            self.add_links(get_images_on_page(soup), self.image_links)
            self.add_links(get_css_on_page(soup), self.css_links)
            self.add_links(get_scripts_on_page(soup), self.script_links)
            self.add_links(get_hyperlinks_on_page(soup)+get_sitemap_links_on_page(soup), self.hyper_links)
            
        

    def add_links(self, input_links, list):
        for input_link in input_links:
            link_item = self._set.get_or_create_link_object(input_link, self)
            if link_item:
                self.add_link(link_item, list)

    def add_link(self, link_item, list):
        is_same_url = self.url == link_item.url
        list_has_link = (link_item.url in list)

        if is_same_url==False and list_has_link==False:
            list[link_item.url] = link_item
        

    def add_referer(self, link_item):
        #print 'add referer to %s from %s'%(self.url, link_item.url)
        self.add_link(link_item, self.referers)
   



    
        




###########################
## HELPER FUNCTIONS #######
###########################

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
    if not url:
        return None

    #Remove all query params from url
    url_parts = list(urlparse.urlparse(url))
    url_parts[4] = urllib.urlencode({})
    new_url = urlparse.urlunparse(url_parts)

    return new_url 

def get_hyperlinks_on_page(soup):
    output = []  

    #Traditional hyperlinks
    for a in soup.findAll('a'):

        try:
            href = a['href']  
            output.append(href)      
        except:
            href = None

    return output

def get_sitemap_links_on_page(soup):
    output = []  

    #Sitemap links
    for url in soup.findAll('url'):
        url_loc = None
        for loc in url.findAll('loc'):
            if loc.text:
                output.append(loc.text)

    return output

def get_css_on_page(soup):
    output = []  

    #CSS Links
    for a in soup.findAll('link'):
        try:
            href = a['href']  
            rel = a['rel'][0].strip()
            if rel == 'stylesheet':
                output.append(href)      
        except:
            href = None 

    return output 

def get_scripts_on_page(soup):
    output = []  

    #JS Links
    for a in soup.findAll('script'):
        try:
            src = a['src']  
            output.append(src)      
        except:
            href = None 

    return output


def get_images_on_page(soup):
    output = []

    #Traditional hyperlinks
    for img in soup.findAll('img'):

        try:
            src = img['src']  
            output.append(src)      
        except:
            src = None

    return output

def timedelta_milliseconds(td):
    return td.days*86400000 + td.seconds*1000 + td.microseconds/1000    

# Recursively follow redirects until there isn't a location header
def trace_path(url, traced, depth=0):

    if depth > 12:

        return traced

    request = urllib2.Request(url, headers=HEADERS)
    response = None
    response_data = {'url':url,'response_code':None,'response_content_type':None,'redirect':None,'response_load_time':None}
    has_redirect = False

    try:

        start_time = datetime.datetime.now()
        response = urllib2.urlopen(request)
        end_time = datetime.datetime.now()
        response_data['response_code'] = response.code
        response_data['response_content_type'] = response.info().getheader('Content-Type')

        load_time = end_time - start_time
        milliseconds = timedelta_milliseconds(load_time)
        response_data['response_load_time'] = milliseconds     

        ending_url = response.geturl()
        has_redirect = url != ending_url

        if has_redirect:
            response_data['redirect'] = ending_url
               

    except urllib2.HTTPError, e:
        #checksLogger.error('HTTPError = ' + str(e.code))

        try:
            response_data['response_code'] = e.code    
        except:
            response_data['response_code'] = "Unknown HTTPError"

    except urllib2.URLError, e:
        #checksLogger.error('URLError = ' + str(e.reason))
        response_data['response_code'] = "Unknown URLError: %s"%(e.reason)
       
    # except httplib.HTTPException, e:
    #     #checksLogger.error('HTTPException')

    #     if expect_success:
    #         message = "Loading error on page <a href='#%s' class='alert-link'>%s</a> ERROR: %s"%(link['internal_page_url'], link_url, e)
    #         messages['error'].append(message)
    #         link['messages']['error'].append(message)

    except Exception:
        response_data['response_code'] = "Unknown Exception: %s"%(traceback.format_exc())
        
    
    traced.append(response_data)

    if has_redirect:
        traced = trace_path(ending_url, traced)
        

    return traced

def url_fix(s, charset='utf-8'):
    """Sometimes you get an URL by a user that just isn't a real
    URL because it contains unsafe characters like ' ' and so on.  This
    function can fix some of the problems in a similar way browsers
    handle data entered by the user:

    >>> url_fix(u'http://de.wikipedia.org/wiki/Elf (Begriffsklärung)')
    'http://de.wikipedia.org/wiki/Elf%20%28Begriffskl%C3%A4rung%29'

    :param charset: The target charset for the URL if the url was
                    given as unicode string.

    TODO:
    https://fonts.googleapis.com/css?family=Alegreya+Sans:400,700,400italic,700italic should become:
    https://fonts.googleapis.com/css?family=Alegreya+Sans%3A400%2C700%2C400italic%2C700italic

    """
    if isinstance(s, unicode):
        s = s.encode(charset, 'ignore')
    scheme, netloc, path, qs, anchor = urlparse.urlsplit(s)
    path = urllib.quote(path, '/%')
    qs = urllib.quote_plus(qs, ':&=')
    return urlparse.urlunsplit((scheme, netloc, path, qs, anchor))    

def trace_memory_usage():
    print 'Memory usage: %s' % memory_usage_resource()
    # import gc
    # import objgraph
    # gc.collect()  # don't care about stuff that would be garbage collected properly
    # objgraph.show_most_common_types()

def memory_usage_resource():
    import resource

    rusage_denom = 1024.
    if sys.platform == 'darwin':
        # ... it seems that in OSX the output is different units ...
        rusage_denom = rusage_denom * rusage_denom
    mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / rusage_denom
    return mem    