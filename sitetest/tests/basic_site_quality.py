from bs4 import BeautifulSoup

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
        image_error_url = "%sthisShouldNotExist.jpg"%(canonical_domain)
    else:
        robots_url = "%s/robots.txt"%(canonical_domain)
        sitemap_url = "%s/sitemap.xml"%(canonical_domain)
        favicon_url = "%s/favicon.ico"%(canonical_domain)
        error_url = "%s/thisShouldNotExist"%(canonical_domain)
        image_error_url = "%s/sthisShouldNotExist.jpg"%(canonical_domain)
        
    #1 - Test robots.txt
    robots_link = site.get_or_create_link_object(robots_url)
    site.load_link(robots_link, False, 200, verbose)
    
    
    #2 - Test sitemap.xml
    sitemap_link = site.get_or_create_link_object(sitemap_url)
    site.load_link(sitemap_link, False, 200, verbose)
    
    #3 - Test favicon.ico
    favicon_link = site.get_or_create_link_object(favicon_url)
    site.load_link(favicon_link, False, 200, verbose)

    #4 - Test thisShouldNotExist
    error_link = site.get_or_create_link_object(error_url)
    site.load_link(error_link, False, 404, verbose)

    image_error_link = site.get_or_create_link_object(image_error_url)
    site.load_link(image_error_link, False, 404, verbose)
    

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
                    link.add_info_message("Page is not included in sitemap")
                    page_missing_sitemap += 1

        orphan_page = 0
        for link_url in site.parsed_links:
            link = site.parsed_links[link_url]
            
            if len(link.referers) == 0 and link.has_sitemap_entry:
                link.add_info_message("Page is in the sitemap, but not accessible from elsewhere in the site.")
                orphan_page += 1

        if page_missing_sitemap > 0:
            site.add_warning_message("%s pages were found to be missing from sitemap"%(page_missing_sitemap))

        if orphan_page > 0:
            site.add_info_message("%s pages were found in the sitemap but not elsewhere in the site."%(page_missing_sitemap))

        