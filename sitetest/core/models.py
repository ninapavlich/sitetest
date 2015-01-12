# -*- coding: utf-8 -*-

import traceback     
import datetime
import gzip
import httplib
import html5lib
import urllib2
import urllib
import urlparse
import cgi
import re
import os
import sys
import zlib
from slugify import slugify
from bs4 import BeautifulSoup


TYPE_OTHER = 'other'
TYPE_MAILTO = 'mailto'
TYPE_INTERNAL = 'internal'
TYPE_EXTERNAL = 'external'


IMAGE_SUFFIXES = [
    '.png', '.jpg', '.jpeg', '.gif','.ico','.svg'
]
FONT_SUFFIXES = [
    '.otf','.ttf','.eot', '.cff','.afm','.lwfn','.ffil','.fon','.pfm','.woff','.std','.pro','.xsf'
]
MEDIA_SUFFIXES = IMAGE_SUFFIXES + FONT_SUFFIXES + [
    '.doc', '.pdf', '.ppt', '.zip', '.gzip', '.mp3', '.rar', '.exe', 
    '.avi', '.mpg', '.tif', '.wav', '.mov', '.psd', '.ai', '.wma',
    '.eps','.mp4','.bmp','.indd','.swf','.jar','.dmg','.iso','.flv',
    '.gz','.fla','.ogg','.sql'
]

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
    #'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', #TODO: image/webp
   'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
   'Accept-Encoding': 'gzip, deflate', #TODO: gzip, deflate, sdch
   'Accept-Language': 'en-US,en;q=0.8',
   'Connection': 'keep-alive'}

class MessageSet(object):
    # __slots__ = ['success', 'error', 'warning', 'info',]

    success = None
    error = None
    warning = None
    info = None
    verbose = False

    def __init__(self, verbose=False):
        self.verbose = verbose
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
    verbose = False

    def __init__(self):
        pass

    def get_score(self):
        if self.messages:
            return self.messages.get_score()
        return None
    

    def add_error_message(self, message, count=1):
        if self.verbose:
            print "ERROR: %s"%(message)
        self.messages.error.append(ErrorMessage(message, count))

    def add_warning_message(self, message, count=1):
        #if self.verbose:
        #    print "WARNING: %s"%(message)
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
    loadable_links = {}
    test_results = None
    

    def __init__(self, include_media, include_external_links, canonical_domain, domain_aliases, max_parse_count=None, ignore_query_string_keys=None, alias_query_strings=None, skip_test_urls=None, skip_urls=None, verbose=False):

        self.verbose = verbose
        self.messages = MessageSet(verbose)

        if ignore_query_string_keys is None:
            ignore_query_string_keys = []

        if alias_query_strings is None:
            alias_query_strings = []
        
        if skip_test_urls is None:
            skip_test_urls = []

        if skip_test_urls is None:
            skip_test_urls = []

        self.include_media = include_media
        self.include_external_links = include_external_links
        self.canonical_domain = canonical_domain
        self.domain_aliases = domain_aliases
        self.ignore_query_string_keys = ignore_query_string_keys
        self.alias_query_strings = alias_query_strings
        self.skip_test_urls = skip_test_urls
        self.skip_urls = skip_urls
        self.max_parse_count = None if not max_parse_count else int(max_parse_count)
        super(LinkSet, self).__init__()    

    @property
    def robots_url(self):
        return "%srobots.txt"%(self.canonical_domain) if self.canonical_domain.endswith("/") else "%s/robots.txt"%(self.canonical_domain)

    @property
    def robots_link(self):
        return self.current_links[self.robots_url]

    @property
    def default_sitemap_url(self):
        return "%ssitemap.xml"%(self.canonical_domain) if self.canonical_domain.endswith("/") else "%s/sitemap.xml"%(self.canonical_domain)

    @property
    def sitemap_links(self):
        return [self.current_links[url] for url in self.current_links if self.current_links[url].is_sitemap==True]
        
    def load_link(self, page_link, recursive, expected_code=200, force=False):

        if self.max_parse_count and len(self.parsed_links) >= self.max_parse_count and force == False:
            #print "PARSED %s PAGES, turn recursive off"%(self.max_parse_count)
            return

        is_loadable = page_link.is_loadable_type(self.include_media, self.include_external_links)
        not_already_loaded = (page_link.url not in self.loaded_links)

        if is_loadable==True and not_already_loaded==True:

            if self.verbose:
                # trace_memory_usage()
                print ">>> Load Link %s (parsed: %s/%s, loaded: %s/%s, total: %s)"%(page_link.__unicode__(), len(self.parsed_links), len(self.parsable_links), len(self.loaded_links), len(self.loadable_links),  len(self.current_links))

            load_successful, response = page_link.load(self, expected_code)
            
            if not load_successful:
                message = "Loading unsuccessful on page <a href='#%s' class='pagelink alert-link'>%s</a> Expected %s Received %s"%(page_link.internal_page_url, page_link.url, 200, page_link.response_code)
                self.add_error_message(message)
            

            #record that we have parsed it
            if page_link.url not in self.loaded_links:
                self.loaded_links[page_link.url] = page_link


            #parse child links of internal pages and css only
            if page_link.likely_parseable_type == True:

                # if self.verbose:
                #     # trace_memory_usage()
                #     print ">>> Parse Link %s (%s/%s, %s)"%(page_link.__unicode__(), len(self.parsed_links), len(self.parsable_links), len(self.current_links))

                page_link.parse_response(response, self)

                #record that we have parsed it
                if page_link.url not in self.parsed_links:
                    self.parsed_links[page_link.url] = page_link
            

        #Let's do it again!
        if recursive==True:
            for child_link_url in page_link.links:
                if child_link_url not in self.parsed_links:                                                              
                    self.load_link(page_link.links[child_link_url], recursive, 200)
       



    def get_or_create_link_object(self, url, referer=None):
        incoming_url = url
        referer_url = None if not referer else referer.url

        url = self.get_normalized_href(url, referer_url)
        slashed_url = u"%s/"%url
        deslashed_url = url.rstrip(u"/")

        if not url or url == '':
            return None


        if url in self.current_links:
            link = self.current_links[url]
        elif slashed_url in self.current_links:
            link = self.current_links[slashed_url]
        elif deslashed_url in self.current_links:
            link = self.current_links[deslashed_url]
        else:
            link = LinkItem(url, self, self.verbose)
            self.current_links[url] = link
            
            if link.likely_parseable_type == True:
                self.parsable_links[link.url] = link

            if link.is_loadable_type(self.include_media, self.include_external_links):
                self.loadable_links[link.url] = link

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
    response_code = None
    response_content_type = None    
    alias_to = None
    skip_test = False
    skip = False
    has_sitemap_entry = False
    accessible_to_robots = False
    is_sitemap = False
    is_robots = False
    


    def __init__(self, url, set, verbose=False):

        self.messages = MessageSet(verbose)
        self.verbose = verbose
        self.referers = {}
        self.image_links = {}
        self.audio_links = {}
        self.video_links = {}
        self.hyper_links = {}
        # self.object_links = {}
        self.css_links = {}
        self.css_image_links = {}
        self.font_links = {}
        self.script_links = {}
        self.iframe_links = {}
        # self.xhr_links = {}
        self.url = self.ending_url = url
        parsed = urlparse.urlparse(url)
        name, extension = os.path.splitext(parsed.path)
        self.starting_type = self.ending_type = set.get_link_type(url)
        self.path = parsed.path
        self.domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed)
        self.is_media = (extension.lower() in MEDIA_SUFFIXES)
        self.is_font = (extension.lower() in FONT_SUFFIXES)
        self.is_image = (extension.lower() in IMAGE_SUFFIXES)
        self.source = None
        self.html = None


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
    def active_mixed_content_links(self):
        #https://community.qualys.com/blogs/securitylabs/2014/03/19/https-mixed-content-still-the-easiest-way-to-break-ssl
        #css + scripts + xhr + web sockets + iframes
        return dict(\
            self.script_links.items() + \
            self.css_links.items() + \
            self.iframe_links.items() + \
            self.css_image_links.items() + \
            self.font_links.items()\
        )

    @property
    def links(self):
       return dict(self.image_links.items() + self.hyper_links.items() + self.css_links.items() + self.script_links.items())

    @property
    def content(self):
        if self.is_html == True or self.is_xml == True:
            return self.html
        #elif self.is_javascript == True or self.is_css == True or self.is_xml == True:
        return self.source

    @property
    def is_alias(self):
        return self.alias_to != None


    def is_loadable_type(self, include_media, include_external_links):
        if self.skip == True:
            return False

        is_internal = (self.starting_type == TYPE_INTERNAL and not self.is_media)
        is_allowed_external = (self.starting_type == TYPE_EXTERNAL and include_external_links)
        is_allowed_media = (self.is_media and include_media)
        
        is_loadable = is_internal or is_allowed_external or is_allowed_media

        return is_loadable

    @property
    def is_parseable_type(self):
        return self.has_response and (self.is_internal == True or self.is_css == True or self.is_javascript == True)

    @property
    def likely_parseable_type(self):
        return (self.starting_type == TYPE_INTERNAL and not self.is_media == True) \
            or ('.css' in self.url.lower()) or ('.js' in self.url.lower()) \
            or ('.gz' in self.url.lower())

    @property
    def is_internal(self):
        return self.ending_type == TYPE_INTERNAL and self.starting_type == TYPE_INTERNAL

    @property
    def is_internal_html(self):
        return self.is_internal == True and self.is_html == True

    @property
    def is_html(self):
        content_type = self.response_content_type
        return content_type and 'html' in content_type.lower()

    @property
    def is_javascript(self):
        content_type = self.response_content_type
        return content_type and 'javascript' in content_type.lower()

    @property
    def is_xml(self):
        content_type = self.response_content_type
        return content_type and 'xml' in content_type.lower()

    @property
    def is_css(self):
        content_type = self.response_content_type
        return content_type and 'css' in content_type.lower()

    def load(self, set, expected_code=200):


        request = urllib2.Request(self.url, headers=HEADERS)
        response = None
        start_time = datetime.datetime.now()

        try:

            
            response = urllib2.urlopen(request)
            end_time = datetime.datetime.now()
            self.response_code = response.code
            #self.response = response#u"%s"%(response)
            self.has_response = True
            response_header = response.info()
            self.response_content_type = response_header.getheader('Content-Type')
            self.response_encoding = response_header.getheader('Content-Encoding')
            self.ending_url = response.geturl()
            self.ending_type = set.get_link_type(self.ending_url)

            load_time = end_time - start_time
            milliseconds = timedelta_milliseconds(load_time)
            self.response_load_time = milliseconds        

            if self.url != self.ending_url:
                redirect_path = trace_path(self.url, [])
                self.redirect_path = redirect_path

        except urllib2.HTTPError, e:
            #checksLogger.error('HTTPError = ' + str(e.code))

            try:
                self.response_code = e.code

                end_time = datetime.datetime.now()
                load_time = end_time - start_time
                milliseconds = timedelta_milliseconds(load_time)
                self.response_load_time = milliseconds   
                
                if self.response_code == 303:
                    try:

                        redirect_path = trace_path(self.url, [])       
                        self.redirect_path = redirect_path     
                        if len(redirect_path) > 0:
                            response_data = redirect_path[-1]
                            self.response_content_type = response_data['response_content_type']
                            self.response_code = response_data['response_code']
                            self.ending_url = response_data['url']
                            self.ending_type = set.get_link_type(self.ending_url)      
                            if self.response_code == 200:
                                request = urllib2.Request(self.ending_url, headers=HEADERS)
                                response = urllib2.urlopen(request)    
                                self.has_response = True

                    except Exception:
                        print 'error getting response headers: %s'%(traceback.format_exc())
                    

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

    def parse_response(self, response, set):
        raw_response = None if response==None else response.read()
        self.source = raw_response

        #DETECT COMPRESSION
        if response:
            if self.response_encoding:

                if self.response_encoding == 'gzip':

                    try:
                        #Attempt to read as gzipped file
                        decompressed = zlib.decompress(raw_response, 16+zlib.MAX_WBITS)
                        self.source = decompressed
                    except Exception:
                        print raw_response
                        self.source = raw_response

                elif self.response_encoding == 'deflate':

                    try:
                        decompressed = zlib.decompressobj(-zlib.MAX_WBITS).decompress(raw_response)
                        self.source = decompressed
                    except Exception:
                        self.source = raw_response
            else:
                self.source = raw_response


        #PARSE HTML/XML
        if self.is_html == True or self.is_xml == True:

            try:
                soup = BeautifulSoup(self.source, 'html5lib')
            except Exception:
                soup = None
                self.add_error_message("Error parsing HTML on page %s: %s"%(self.url, traceback.format_exc()))

        
            if soup:

                page_html = soup.prettify()
                self.html = page_html

                self.add_links(get_css_on_page(soup), self.css_links, set)
                self.add_links(get_images_on_page(soup), self.image_links, set)
                self.add_links(get_images_from_css(set, self), self.css_image_links, set)
                self.add_links(get_fonts_on_page(set, self), self.font_links, set)

                self.add_links(get_scripts_on_page(soup), self.script_links, set)
                self.add_links(get_hyperlinks_on_page(soup)+get_sitemap_links_on_page(soup), self.hyper_links, set)

                self.add_links(get_audio_on_page(soup), self.audio_links, set)
                self.add_links(get_video_on_page(soup), self.video_links, set)
                #TODO: self.add_links(get_video_on_page(soup), self.object_links, set)
                self.add_links(get_iframes_on_page(soup), self.iframe_links, set)
                #self.add_links(get_xhr_links_on_page(soup), self.xhr_links, set)
        
        

        #Create enumerated source
        if self.content:
            try:
                enumerated_source_list = self.content.split(u"\n")
                counter = 0
                enumerated_source = u''
                for line in enumerated_source_list:
                    new_line = (u"%s: %s"%(counter, line))
                    enumerated_source += (u"%s\n"%(new_line))
                    counter += 1
                self.enumerated_source = enumerated_source
            except Exception:
                self.enumerated_source = "Error enumerating source: %s"%(traceback.format_exc())  

        # if 'css' in self.url:
        #     print "CSS %s is_css? %s: %s"%(self.url, self.is_css, self.content)
        


    def add_links(self, input_links, list, set):
        for input_link in input_links:
            link_item = set.get_or_create_link_object(input_link, self)
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

def get_audio_on_page(soup):
    output = []

    for audio in soup.findAll('audio'):

        try:
            src = audio['src']  
            output.append(src)      
        except:
            src = None

        for source in audio.findAll('source'):
            try:
                src = source['src']  
                output.append(src)      
            except:
                src = None



    return output

def get_video_on_page(soup):
    output = []

    for video in soup.findAll('video'):

        try:
            src = video['src']  
            output.append(src)      
        except:
            src = None

        for source in video.findAll('source'):
            try:
                src = source['src']  
                output.append(src)      
            except:
                src = None

    return output

def get_iframes_on_page(soup):
    output = []

    for iframe in soup.findAll('iframe'):

        try:
            src = iframe['src']  
            output.append(src)      
        except:
            src = None

    return output

def get_images_from_css(set, link):
    #TODO -- also include inline css
    output = []
    for css_url in link.css_links:
        css_link = link.css_links[css_url]
        set.load_link(css_link, False, 200)

        if css_link.response_code == 200:
            if css_link.content:
                all_urls = re.findall('url\(([^)]+)\)',css_link.content)
                for url in all_urls:
                    full_url = urlparse.urljoin(css_link.url, url.strip("'").strip('"'))
                    parsed = urlparse.urlparse(full_url)
                    name, extension = os.path.splitext(parsed.path)
                    is_font = (extension.lower() in FONT_SUFFIXES)
                    if is_font:
                        output.append(full_url)
    return output

def get_fonts_on_page(set, link):
    #TODO -- also include inline css
    output = []
    for css_url in link.css_links:
        css_link = link.css_links[css_url]
        set.load_link(css_link, False, 200)

        if css_link.response_code == 200:
            if css_link.content:
                all_urls = re.findall('url\(([^)]+)\)',css_link.content)
                for url in all_urls:
                    full_url = urlparse.urljoin(css_link.url, url.strip("'").strip('"'))
                    parsed = urlparse.urlparse(full_url)
                    name, extension = os.path.splitext(parsed.path)
                    is_font = (extension.lower() in FONT_SUFFIXES)
                    if is_font:
                        output.append(full_url)

    
    return output

def timedelta_milliseconds(td):
    return td.days*86400000 + td.seconds*1000 + td.microseconds/1000    

# Recursively follow redirects until there isn't a location header
class NoRedirection(urllib2.HTTPErrorProcessor):

    def http_response(self, request, response):
        return response

    https_response = http_response

def trace_path(url, traced, depth=0):

    MAX_REDIRECTS = 12
    if depth > MAX_REDIRECTS:
        return traced

    opener = urllib2.build_opener(NoRedirection)
    request = urllib2.Request(url, headers=HEADERS)
    response = None
    response_data = {'url':url,'response_code':None,'response_content_type':None,'redirect':None,'response_load_time':None}
    has_redirect = False

    try:

        start_time = datetime.datetime.now()
        response = opener.open(request)
        end_time = datetime.datetime.now()
        response_data['response_code'] = response.code
        response_header = response.info()
        response_data['response_content_type'] = response_header.getheader('Content-Type')
        response_data['response_encoding'] = response_header.getheader('Content-Encoding')
        

        load_time = end_time - start_time
        milliseconds = timedelta_milliseconds(load_time)
        response_data['response_load_time'] = milliseconds     

        ending_url = response_header.getheader('Location') or url
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

def store_file_locally(url):

    temp_folder = 'tmp'
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    # Open the url
    try:
        f = urllib2.urlopen(url)
        local_path = os.path.join(temp_folder, os.path.basename(url))

        # Open our local file for writing
        with open(local_path, "wb") as local_file:
            local_file.write(f.read())

    #handle errors
    except urllib2.HTTPError, e:
        print "HTTP Error:", e.code, url
    except urllib2.URLError, e:
        print "URL Error:", e.reason, url

    return local_path   

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