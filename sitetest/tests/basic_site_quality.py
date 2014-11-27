from ..core.retrieve_all_urls import get_or_create_link_object, load_link_object, get_urls_on_page
from bs4 import BeautifulSoup
from ..core.retrieve_all_urls import TYPE_INTERNAL

def test_basic_site_quality(site, verbose=False):
    """
    This tests for robots.txt, sitemap.xml, top-level favicon.ico, test 400 page
    """

    canonical_domain = site.canonical_domain

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
    robots_link = site.get_or_create_link_object(robots_url)
    site.load_link(robots_link, False)
    
    
    #2 - Test sitemap.xml
    sitemap_link = site.get_or_create_link_object(sitemap_url)
    site.load_link(sitemap_link, False)
    
    #3 - Test favicon.ico
    favicon_link = site.get_or_create_link_object(favicon_url)
    site.load_link(favicon_link, False)

    #4 - Test thisShouldNotExist
    error_link = site.get_or_create_link_object(error_url)
    site.load_link(error_link, False, 404)
    

    #5 - Verify that sitemap matches up with the actual pages
    #TODO -- work with compound sitemaps
    if sitemap_link.response_code == 200:

        for link_url in sitemap_link.hyper_links:
            link_item = sitemap_link.hyper_links[link_url]
            link_item.has_sitemap_entry = True


        #For any internal page that doesn't have a sitemap entry, add a notice
        page_missing_sitemap = 0
        for link_url in site.current_links:
            link = site.current_links[link_url]
            

            if link.is_internal_html():
                
                if link.has_sitemap_entry == False and not link.alias_to and not link.skip_test:
                    link.add_notice_message("Page is not included in sitemap")
                    page_missing_sitemap += 1

        if page_missing_sitemap > 0:
            site.add_warning_message("%s pages were found to be missing from sitemap"%(page_missing_sitemap))

        