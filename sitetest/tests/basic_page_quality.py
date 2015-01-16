from bs4 import BeautifulSoup, SoupStrainer
import traceback  



def test_basic_page_quality(set, recursive, verbose=False):
    """
    For each page, make sure there is a unique title and description
    """

    if verbose:
        print 'Running page quality tests...'
    
    unique_titles = {}
    unique_descriptions = {}

    unique_title_error_count = 0
    unique_description_error_count = 0
    social_tag_error_count = 0
    analytics_missing_error_count = 0
    ssl_error_count = 0
    h1_error_count = 0

    compression_error_count = 0
    robots_error_count = 0
    sitemap_error_count = 0
    

    total = len(set.parsed_links)
    count = 0
    for link_url in set.parsed_links:
        if verbose:
            print "%s/%s"%(count, total)
        count += 1

        link = set.parsed_links[link_url]
        
        if link.is_internal_html == True:

            link_html = link.html
            if link_html:
                try:
                    soup = BeautifulSoup(link_html)
                    
                    #1 - Test Title
                    try:
                        page_title = soup.title.string
                    except:
                        page_title = ''
                    link.title = page_title.strip()

                    is_redirected_page = link.url != link.ending_url
                    is_alias_page = link.alias_to != None
                    is_skip_test = link.skip_test == True
                    is_https = 'https' in link.url

                    if not is_skip_test:

                        if page_title == '':
                            message = "Page title is missing from <a href='#%s' class='alert-link'>%s</a>."%(link.internal_page_url, link_url)
                            link.add_warning_message(message)

                        elif page_title not in unique_titles:
                            unique_titles[page_title] = link.path
                        else:
                            if link.path.strip('/') != unique_titles[page_title].strip('/') and not is_redirected_page and not is_alias_page:
                                message = "Page title &ldquo;%s&rdquo; in <a href='#%s' class='alert-link'>%s</a> is not unique."%(page_title, link.internal_page_url, link_url)
                                link.add_warning_message(message)
                                unique_title_error_count += 1
                            

                        #2 - Test Description
                        page_description = None
                        descriptions = soup.findAll(attrs={"name":"description"})
                        for description in descriptions:
                            try:
                                page_description = description['content'].strip()
                                link.description = page_description
                            except:
                                pass                        

                        if page_description:

                            if page_description not in unique_descriptions:
                                unique_descriptions[page_description] = link.path
                            else:               
                                if link.path.strip('/') != unique_descriptions[page_description].strip('/') and not is_redirected_page and not is_alias_page:
                                    message = "Page description in <a href='#%s' class='alert-link'>%s</a> is not unique."%(link.internal_page_url, link_url)
                                    link.add_warning_message(message)
                                    unique_description_error_count += 1

                        else:                       
                            message = "Page description is missing from <a href='#%s' class='alert-link'>%s</a>."%(link.internal_page_url, link_url)
                            link.add_warning_message(message)

                        meta_tags = [
                            ['property','og:site_name'],
                            ['property','og:title'],
                            ['property','og:description'],
                            ['property','og:type'],
                            ['property','og:url'],
                            ['property','og:image'],
                            ['name','twitter:site'],
                            ['name','twitter:creator'],
                            ['name','twitter:card'],
                            ['name','twitter:title'],
                            ['name','twitter:description'],
                            ['name','twitter:url'],
                            ['name','twitter:image:src'],
                            ['itemprop','name'],
                            ['itemprop','description'],
                            ['itemprop','image']
                        ]

                        #3 - Test Meta tags
                        missing_met_tags = []
                        for tag in meta_tags:
                            prop_type = tag[0]
                            property_name = tag[1]
                            property_content_name = 'content'
                            value = None

                            properties = soup.findAll(attrs={prop_type:property_name})
                            for property_item in properties:
                                try:
                                    value = property_item[property_content_name].strip()
                                except:
                                    value = None
                            if not value:
                                missing_met_tags.append("%s:%s"%(prop_type, property_name))

                        if len(missing_met_tags) > 0:                        
                            social_tag_error_count += 1
                            tags = ', '.join(missing_met_tags)
                            message = "Meta tag(s) missing from page: %s"%(tags)
                            link.add_info_message(message)

                        

                        #4 - Test Analytics
                        #TODO: Sometimes this gives a false positive
                        link_source = link.source
                        universal_analytics_indicator = 'GoogleAnalyticsObject'
                        asynchronous_analytics_indicator = '_gaq'
                        has_ua = universal_analytics_indicator.lower() in link_source.lower()
                        has_asynca = asynchronous_analytics_indicator.lower() in link_source.lower()
                        if not has_ua and not has_asynca:
                            analytics_missing_error_count += 1
                            message = "Page missing google analytics."
                            link.add_warning_message(message)


                        if is_https:
                            #5 - Verity that javascript, css and images are all loaded with https also
                            for link_url in link.active_mixed_content_links:
                                
                                if 'http:' in link_url:
                                    ssl_error_count += 1
                                    message = "HTTP active mixed resource was found on HTTPS page: %s"%(link_url)
                                    link.add_warning_message(message)

                        #6 - Verify that page has exactly one h1
                        h1_count = len(soup.findAll('h1'))
                        if h1_count != 1:
                            h1_error_count += 1
                            message = "Page doesn't have exactly one H1, it has %s"%(h1_count)
                            link.add_warning_message(message)

                        #7 - Compression
                        if link.response_encoding == None:
                            compression_error_count += 1
                            message = "Content is not compressed"
                            link.add_warning_message(message)

                        #8 - Robots
                        if link.accessible_to_robots == False:
                            robots_error_count += 1
                            message = "This page is not accessible to robots.txt"
                            link.add_warning_message(message)

                        #9 - Sitemap
                        if recursive:
                            if link.is_alias == False:
                                if link.has_sitemap_entry == False:
                                    sitemap_error_count += 1
                                    message = "This page is not in the sitemap."
                                    link.add_warning_message(message)


                        #10 - Are CSS Files comfbined
                        css_link_domains = {}
                        for css_link_url in link.css_links:
                            css_link = link.css_links[css_link_url]
                            if css_link.domain not in css_link_domains:
                                css_link_domains[css_link.domain] = 0
                            css_link_domains[css_link.domain] += 1

                        for css_domain in css_link_domains:
                            domain_count = css_link_domains[css_domain]
                            if domain_count > 1:
                                message = "%s css files from the same domain %s. These CSS files should be combined if possible."%(domain_count, css_domain)
                                link.add_warning_message(message)

                        #10 - Are JS Files comfbined
                        js_link_domains = {}
                        for js_link_url in link.script_links:
                            js_link = link.script_links[js_link_url]
                            if js_link.domain not in js_link_domains:
                                js_link_domains[js_link.domain] = 0
                            js_link_domains[js_link.domain] += 1

                        for js_domain in js_link_domains:
                            domain_count = js_link_domains[js_domain]
                            if domain_count > 1:
                                message = "%s script files from the same domain %s. These script files should be combined if possible."%(domain_count, js_domain)
                                link.add_warning_message(message)


        
                except Exception:        
                    print "Parsing page quality: %s"%(traceback.format_exc())

    if analytics_missing_error_count > 0:
        set.add_warning_message("%s page(s) were found to be missing google analytics"%(analytics_missing_error_count), analytics_missing_error_count)

    if unique_title_error_count > 0:
        set.add_warning_message("%s page(s) were found to have non-unique page titles"%(unique_title_error_count), unique_title_error_count)

    if unique_description_error_count > 0:
        set.add_warning_message("%s page(s) were found to have non-unique page descriptions"%(unique_description_error_count), unique_description_error_count) 

    if social_tag_error_count > 0:
        set.add_info_message("%s page(s) were found to have missing social meta tags"%(social_tag_error_count), social_tag_error_count)    

    if ssl_error_count > 0:
        set.add_warning_message("%s HTTP active mixed resource were found on HTTPS pages"%(ssl_error_count), ssl_error_count)             

    if h1_error_count > 0:
        set.add_warning_message("%s page(s) didn't have exactly one H1 tag"%(h1_error_count), h1_error_count)             

    if compression_error_count > 0:
        set.add_warning_message("%s page(s) are not compressed"%(compression_error_count), compression_error_count)             

    if robots_error_count > 0:
        set.add_warning_message("%s page(s) are not accessible to robots.txt"%(robots_error_count), robots_error_count)             

    if sitemap_error_count > 0:
        set.add_warning_message("%s page(s) are not in the sitemap"%(sitemap_error_count), sitemap_error_count)             

