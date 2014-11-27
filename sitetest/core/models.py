# -*- coding: utf-8 -*-

import datetime
import httplib
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
    '.png', '.jpg', '.jpeg', '.gif',
    '.doc', '.pdf', '.ppt', '.zip', '.gzip', '.mp3', '.rar', '.exe', 
    '.avi', '.mpg', '.tif', '.wav', '.mov', '.psd', '.ai', '.wma',
    '.eps','.mp4','.bmp','.indd','.swf','.jar','.dmg','.iso','.flv',
    '.gz','.fla','.html','.ogg','.sql'
]

class MessageSet():
    success = []
    error = []
    warning = []
    info = []


class Message():
    message = None

    def __init__(self, message):
        self.message = message

class SuccessMessage(Message):
    pass

class ErrorMessage(Message):
    pass

class WarningMessage(Message):
    pass

class InfoMessage(Message):
    pass

class BaseMessageable():
    messages = MessageSet()

    def add_error_message(self, message):
        self.messages.error.append(ErrorMessage(message))

    def add_warning_message(self, message):
        self.messages.warning.append(WarningMessage(message))

    def add_info_message(self, message):
        self.messages.info.append(InfoMessage(message))

    def add_success_message(self, message):
        self.messages.success.append(SuccessMessage(message))

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

    def __init__(self, include_media, canonical_domain, domain_aliases, ignore_query_string_keys=None, alias_query_strings=None, skip_test_urls=None):

        if ignore_query_string_keys is None:
            ignore_query_string_keys = []

        if alias_query_strings is None:
            alias_query_strings = []
        
        if skip_test_urls is None:
            skip_test_urls = []

        self.include_media = include_media
        self.canonical_domain = canonical_domain
        self.domain_aliases = domain_aliases
        self.ignore_query_string_keys = ignore_query_string_keys
        self.alias_query_strings = alias_query_strings
        self.skip_test_urls = skip_test_urls

        
    def load_link(self, page_link, recursive):

        if page_link.is_loadable_type(self.include_media) and page_link.url not in self.loaded_links:

            print ">>> Load Link %s (%s/%s, %s)"%(page_link.__unicode__(), len(self.parsed_links), len(self.parsable_links), len(self.current_links))

            load_successful = page_link.load()
            
            if not load_successful:
                message = "Loading error on page <a href='#%s' class='alert-link'>%s</a> Expected %s Received %s"%(page_link.internal_page_url, page_link.url, 200, page_link.response_code)
                self.add_error_message(message)
            

            #record that we have parsed it
            if page_link.url not in self.loaded_links:
                self.loaded_links[page_link.url] = page_link
            

            #parse child links of internal pages only
            if page_link.response and page_link.is_internal():

                page_link.parse_response()

                #record that we have parsed it
                if page_link.url not in self.parsed_links:
                    self.parsed_links[page_link.url] = page_link
                
                #Let's do it again!
                if recursive:
                    for child_link_url in page_link.links:
                        if child_link_url not in self.parsed_links:                                                              
                            self.load_link(page_link.links[child_link_url], recursive)
       



    def get_or_create_link_object(self, url, referer=None):
        incoming_url = url

        url = self.get_normalized_href(url)

        
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
        

        if url.startswith('//'):
            if self.canonical_domain.startswith('https'):
                url = u"https:%s"%(url)
            else:
                url = u"http:%s"%(url)

        #Normalize url by converting to lowercase: 
        normalized = url_fix(url.lower())

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

                    #print "relative from parent, replacd %s with %s"%(url, normalized)
                    
            #Next remove unwanted query strings:
            normalized = clean_query_string(normalized, self.ignore_query_string_keys)


        else:
            normalized = url


        return normalized


           


    

class LinkItem(BaseMessageable):
    

    _set = None

    referers = None
    image_links = None
    hyper_links = None
    css_links = None
    script_links = None



    url = None
    ending_url = None
    starting_type = None
    ending_type = None
    path = None
    response_code = None
    response = None
    response_content_type = None    
    redirect_path = None
    html = None
    content = None
    response_load_time = None
    description = None
    is_media = None
    sitemap_entry = None
    alias_to = None
    skip_test = False


    def __init__(self, url, set):

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

    def __unicode__(self):
        url = (u"%s-%s")%(self.url, self.ending_url) if self.url != self.ending_url else self.url
        type = (u"%s-%s")%(self.starting_type, self.ending_type) if self.starting_type != self.ending_type else self.starting_type

        return (u"%s [%s]")%(url, type)



    @property
    def internal_page_url(self):
        return "load-test-result-%s"%(self.url)

    @property
    def encoded_url(self):
        return urllib.quote_plus(self.url)


    @property
    def links(self):
       return dict(self.image_links.items() + self.hyper_links.items() + self.css_links.items() + self.script_links.items())

    def is_loadable_type(self, include_media):
        is_internal_or_external = self.starting_type == TYPE_INTERNAL or self.starting_type == TYPE_EXTERNAL
        allow_media = (self.is_media and include_media) or (self.is_media==False)
        return is_internal_or_external and allow_media

    def is_internal(self):
        return self.ending_type == TYPE_INTERNAL and self.starting_type == TYPE_INTERNAL


    def load(self, expected_code=200):

        hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
           'Accept-Encoding': 'none',
           'Accept-Language': 'en-US,en;q=0.8',
           'Connection': 'keep-alive'}

        request = urllib2.Request(self.url, headers=hdr)
        response = None
                
        try:

            start_time = datetime.datetime.now()
            response = urllib2.urlopen(request)
            end_time = datetime.datetime.now()
            self.response_code = response.code
            self.response = response#u"%s"%(response)
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
            import traceback        
            self.response_code = "Unknown Exception: %s"%(traceback.format_exc())


        if expected_code != self.response_code:
            message = "Loading error on page <a href='#%s' class='alert-link'>%s</a> Expected %s Received %s"%(self.internal_page_url, self.url, expected_code, self.response_code)
            self.add_error_message(message)
            return False
        else:
            return True

    def parse_response(self):
        try:
            soup = BeautifulSoup(self.response)
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

    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

    request = urllib2.Request(url, headers=hdr)
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
        import traceback     
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