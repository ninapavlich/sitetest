import traceback  
import sys
from bs4 import BeautifulSoup, SoupStrainer



def test_basic_page_quality(set, recursive, verbose=False):
    """
    For each page, make sure there is a unique title and description
    """

    if verbose:
        print '\n\nRunning page quality tests...\n'
    
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
    orphan_page_error_count = 0


    page_title_missing_error = set.get_or_create_message_category('page-title-missing-error', "Page title missing", 'warning')
    page_title_unique_error = set.get_or_create_message_category('page-title-unique-error', "Page title not unique", 'warning')
    page_description_missing_error = set.get_or_create_message_category('page-description-missing-error', "Page description missing", 'warning')
    page_description_unique_error = set.get_or_create_message_category('page-description-unique-error', "Page description not unique", 'warning')
    missing_analytics = set.get_or_create_message_category('missing-analytics-error', "Page missing Google Analytics", 'warning')
    mixed_resources = set.get_or_create_message_category('mixed-resources-error', "HTTP active mixed resource on HTTPS page", 'warning')
    h1_error = set.get_or_create_message_category('h1-error', "Page doesn't have exactly one H1", 'warning')
    compressed_error = set.get_or_create_message_category('compressed-error', "Page is not compressed", 'warning')
    robots_error = set.get_or_create_message_category('robots-error', "Page is not accessible based on robots.txt", 'warning')
    sitemap_error = set.get_or_create_message_category('sitemap-error', "Page not in sitemap", 'warning')
    multiple_stylesheets = set.get_or_create_message_category('multiple-stylesheets-error', "Multiple stylesheets from the same domain. These should be combined if possible", 'warning')
    multiple_scripts = set.get_or_create_message_category('multiple-scripts-error', "Multiple scripts from the same domain. These should be combined if possible", 'warning')
    sitemap_orphan_error = set.get_or_create_message_category('sitemap-orphan-error', "Orphan pages in the sitemap, but not accessible from elsewhere in the site", 'warning')

    missing_meta_tags = set.get_or_create_message_category('missing-meta-tags', "Missing social media meta tags", 'info')

    
    


    total = len(set.parsed_links)
    count = 0
    for link_url in set.parsed_links:
        if verbose:
            print '%d/%d' % (count, total)
            
        count += 1

        link = set.parsed_links[link_url]
        
        if link.is_internal_html==True and not link.skip_test == True:

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

                    is_redirected_page = link.is_redirect_page
                    is_alias_page = link.alias_to != None
                    is_skip_test = link.skip_test == True
                    is_https = 'https' in link.url

                    if not is_skip_test:

                        
                        if page_title == '':
                            message = "Page title is missing from <mark>%s</mark>"%(link_url)
                            link.add_warning_message(message, self.page_title_missing_error)
                            link.title = link_url


                        elif (page_title not in unique_titles) and (is_redirected_page == False) and (is_alias_page == False):
                            unique_titles[page_title] = link.path
                        else:

                            if page_title not in unique_titles:
                                unique_titles[page_title] = link.path

                            if link.path.strip('/') != unique_titles[page_title].strip('/') and (is_redirected_page == False) and (is_alias_page == False):
                                message = "Page title <mark>&ldquo;%s&rdquo;</mark> is not unique."%(page_title)
                                link.add_warning_message(message, page_title_unique_error)
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
                                    message = "Page description in <mark>&ldquo;%s&rdquo;</mark> &ldquo;%s&rdquo; </mark> is not unique."%(link.title, page_description)
                                    link.add_warning_message(message, page_description_unique_error)
                                    unique_description_error_count += 1

                        else:                       
                            message = "Page description is missing from <mark>&ldquo;%s&rdquo;</mark>"%(link.title)
                            link.add_warning_message(message, page_description_missing_error)

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

                        # if len(missing_met_tags) > 0:                        
                        #     social_tag_error_count += 1
                        #     tags = ', '.join(missing_met_tags)
                        #     message = "Page &ldquo;%s&rdquo; missing meta tag(s): %s"%(link.title, tags)
                        #     link.add_info_message(message, missing_meta_tags)

                        

                        #4 - Test Analytics
                        #TODO: Sometimes this gives a false positive
                        link_source = link.source
                        universal_analytics_indicator = 'GoogleAnalyticsObject'
                        asynchronous_analytics_indicator = '_gaq'
                        js_indicator = 'google-analytics'
                        has_ua = universal_analytics_indicator.lower() in link_source.lower()
                        has_asynca = asynchronous_analytics_indicator.lower() in link_source.lower()
                        has_js = js_indicator.lower() in link_source.lower()
                        if not has_ua and not has_asynca and not has_js:
                            analytics_missing_error_count += 1
                            message = "Page <mark>&ldquo;%s&rdquo;</mark> missing google analytics."%(link.title)
                            link.add_warning_message(message, missing_analytics)


                        if is_https:
                            #5 - Verity that javascript, css and images are all loaded with https also
                            for link_url in link.active_mixed_content_links:
                                
                                if 'http:' in link_url:
                                    ssl_error_count += 1
                                    message = "HTTP active mixed resource was found on HTTPS page <mark>&ldquo;%s&rdquo;</mark>"%(link.title)
                                    link.add_warning_message(message, mixed_resources)

                        #6 - Verify that page has exactly one h1
                        h1_count = len(soup.findAll('h1'))
                        if h1_count != 1:
                            h1_error_count += 1
                            message = "Page <mark>&ldquo;%s&rdquo;</mark> doesn't have exactly one H1, it has <mark>%s</mark>"%(link.title, h1_count)
                            link.add_warning_message(message, h1_error)

                        #7 - Compression
                        if link.response_encoding == None:
                            compression_error_count += 1
                            message = "Content is not compressed"
                            link.add_warning_message(message, compressed_error)

                        #8 - Robots
                        if link.accessible_to_robots == False:
                            robots_error_count += 1
                            message = "Page <mark>&ldquo;%s&rdquo;</mark> is not accessible to robots.txt"%(link.title)
                            link.add_warning_message(message, robots_error)

                        #9 - Sitemap
                        if recursive:
                            if link.is_alias == False:
                                if link.has_sitemap_entry == False:
                                    sitemap_error_count += 1
                                    message = "Page <mark>&ldquo;%s&rdquo;</mark> is not in the sitemap"%(link.title)
                                    link.add_warning_message(message, sitemap_error)

                                if len(link.referers) == 1 and link.has_sitemap_entry == True and link.url != set.canonical_domain:
                                    link.add_info_message("Page <mark>&ldquo;%s&rdquo;</mark> is in the sitemap, but not accessible from elsewhere in the site."%(link.title), sitemap_orphan_error)
                                    orphan_page_error_count += 1


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
                                message = "<mark>%s</mark> css files from the same domain <mark>%s</mark>."%(domain_count, css_domain)
                                link.add_warning_message(message, multiple_stylesheets)

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
                                message = "<mark>%s</mark> script files from the same domain <mark>%s</mark>."%(domain_count, js_domain)
                                link.add_warning_message(message, multiple_scripts)


        
                except Exception:        
                    print "Parsing page quality: %s"%(traceback.format_exc())

    # if analytics_missing_error_count > 0:
    #     set.add_warning_message("%s page(s) were found to be missing google analytics"%(analytics_missing_error_count), missing_analytics, analytics_missing_error_count)

    # if unique_title_error_count > 0:
    #     set.add_warning_message("%s page(s) were found to have non-unique page titles"%(unique_title_error_count), page_title_unique_error, unique_title_error_count)

    # if unique_description_error_count > 0:
    #     set.add_warning_message("%s page(s) were found to have non-unique page descriptions"%(unique_description_error_count), page_description_unique_error, unique_description_error_count) 

    # if social_tag_error_count > 0:
    #     set.add_info_message("%s page(s) were found to have missing social meta tags"%(social_tag_error_count), missing_meta_tags, social_tag_error_count)    

    # if ssl_error_count > 0:
    #     set.add_warning_message("%s HTTP active mixed resource were found on HTTPS pages"%(ssl_error_count), mixed_resources, ssl_error_count)             

    # if h1_error_count > 0:
    #     set.add_warning_message("%s page(s) didn't have exactly one H1 tag"%(h1_error_count), h1_error, h1_error_count)             

    # if compression_error_count > 0:
    #     set.add_warning_message("%s page(s) are not compressed"%(compression_error_count), compressed_error, compression_error_count)             

    # if robots_error_count > 0:
    #     set.add_warning_message("%s page(s) are not accessible to robots.txt"%(robots_error_count), robots_error, robots_error_count)             

    # if sitemap_error_count > 0:
    #     set.add_warning_message("%s page(s) are not in the sitemap"%(sitemap_error_count), sitemap_error, sitemap_error_count)            

    # if orphan_page_error_count > 0: 
    #     set.add_warning_message("%s page(s) in the sitemap, but not accessible from elsewhere in the site."%(orphan_page_error_count), sitemap_orphan_error, orphan_page_error_count)            

