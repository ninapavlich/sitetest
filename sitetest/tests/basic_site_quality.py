from ..core.retrieve_all_urls import get_or_create_link_object, load_link_object, get_urls_on_page
from bs4 import BeautifulSoup
from ..core.retrieve_all_urls import TYPE_INTERNAL

def test_basic_site_quality(current_urls, canonical_domain, domain_aliases, messages, verbose=False):
    """
    This tests for robots.txt, sitemap.xml, top-level favicon.ico, test 400 page
    """

    
    if canonical_domain.endswith("/"):
        robots_url = "%srobots.txt"%(canonical_domain)
        sitemap_url = "%ssitemap.xml"%(canonical_domain)
        favicon_url = "%sfavicon.ico"%(canonical_domain)
        error_url = "%sthisShouldNotExist"%(canonical_domain)
    else:
        robots_url = "%s/robots.txt"%(canonical_domain)
        sitemap_url = "%s/sitemap.xml"%(canonical_domain)
        favicon_url = "%s/favicon.ico"%(canonical_domain)
        error_url = "%s/thisShouldNotExist"%(canonical_domain)
        
    #1 - Test robots.txt
    robots_link = get_or_create_link_object(robots_url, current_urls, canonical_domain, domain_aliases)
    response, messages = load_link_object(robots_link, canonical_domain, domain_aliases, messages)
    
    
    #2 - Test sitemap.xml
    sitemap_link = get_or_create_link_object(sitemap_url, current_urls, canonical_domain, domain_aliases)
    response, messages = load_link_object(sitemap_link, canonical_domain, domain_aliases, messages)
    
    #3 - Test favicon.ico
    favicon_link = get_or_create_link_object(favicon_url, current_urls, canonical_domain, domain_aliases)
    response, messages = load_link_object(favicon_link, canonical_domain, domain_aliases, messages)

    #4 - Test thisShouldNotExist
    error_link = get_or_create_link_object(error_url, current_urls, canonical_domain, domain_aliases)
    response, messages = load_link_object(error_link, canonical_domain, domain_aliases, messages, 404)


    #5 - Verify that sitemap matches up with the actual pages
    if sitemap_link['response_code'] == 200:

        sitemap_soup = BeautifulSoup(sitemap_link['html'])
        sitemap_urls = get_urls_on_page(sitemap_soup)
        
        for url in sitemap_soup.findAll('url'):
            for loc in url.findAll('loc'):
                if loc.text:
                    link_url = loc.text.strip()
                    link_object = current_urls[link_url]
                    link_object['sitemap_entry'] = loc


        #For any internal page that doesn't have a sitemap entry, add a notice
        page_missing_sitemap = 0
        for link_url in current_urls:
            link = current_urls[link_url]
            link_type = link['type']
            content_type = link['response_content_type']

            if link_type == TYPE_INTERNAL and link['response_content_type'] \
                and 'html' in link['response_content_type'].lower():

                if link['sitemap_entry'] == None:
                    link['messages']['info'].append("Notice: Page is not included in sitemap")
                    page_missing_sitemap += 1

        if page_missing_sitemap > 0:
            messages['info'].append("Notice: %s pages were found to be missing from sitemap"%(page_missing_sitemap))

        
    return current_urls, messages