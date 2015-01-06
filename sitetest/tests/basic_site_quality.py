from bs4 import BeautifulSoup
import robotparser

def test_basic_site_quality(site, verbose=False):
    """
    This tests for robots.txt, sitemap.xml, top-level favicon.ico, test 400 page
    """

    if verbose:
        print 'Running site quality tests...'

    canonical_domain = site.canonical_domain

    if canonical_domain.endswith("/"):
        favicon_url = "%sfavicon.ico"%(canonical_domain)
        error_url = "%sthisShouldNotExist"%(canonical_domain)
        image_error_url = "%sthisShouldNotExist.jpg"%(canonical_domain)
    else:
        favicon_url = "%s/favicon.ico"%(canonical_domain)
        error_url = "%s/thisShouldNotExist"%(canonical_domain)
        image_error_url = "%s/thisShouldNotExist.jpg"%(canonical_domain)
        
    #1 - Test robots.txt
    robots_link = site.get_or_create_link_object(site.robots_url)
    robots_link.robots_url = False
    site.load_link(robots_link, False, 200)
    
    
    #2 - Test sitemap.xml
    sitemap_links = site.sitemap_links
    
    #3 - Test favicon.ico
    favicon_link = site.get_or_create_link_object(favicon_url)
    site.load_link(favicon_link, False, 200)

    #4 - Test thisShouldNotExist
    error_link = site.get_or_create_link_object(error_url)
    site.load_link(error_link, False, 404)

    image_error_link = site.get_or_create_link_object(image_error_url)
    site.load_link(image_error_link, False, 404)
    

    #5 - Verify that sitemap matches up with the actual pages
    #TODO -- work with compound sitemaps
    #if sitemap_link.response_code == 200:
    if len(sitemap_links) > 0:

        for sitemap_link in sitemap_links:
            for link_url in sitemap_link.hyper_links:
                link_item = sitemap_link.hyper_links[link_url]
                link_item.has_sitemap_entry = True


        if verbose:
            print 'Verifying pages are included in sitemap...'
        total = len(site.loaded_links)
        count = 0
        
        #For any internal page that doesn't have a sitemap entry, add a notice
        page_missing_sitemap = 0
        for link_url in site.loaded_links:
            link = site.loaded_links[link_url]

            if verbose:
                print "%s/%s"%(count, total)
            count += 1
            

            if link.is_internal_html == True:
                
                if link.has_sitemap_entry == False and not link.alias_to and not link.skip_test:
                    link.add_info_message("Page is not included in sitemap")
                    page_missing_sitemap += 1

        if verbose:
            print 'Verifying sitemap pages are not orphans...'
        total = len(site.parsed_links)
        count = 0

        orphan_page = 0
        for link_url in site.parsed_links:
            link = site.parsed_links[link_url]

            if verbose:
                print "%s/%s"%(count, total)
            count += 1
            
            if len(link.referers) == 1 and link.has_sitemap_entry:
                link.add_info_message("Page is in the sitemap, but not accessible from elsewhere in the site.")
                orphan_page += 1

        if page_missing_sitemap > 0:
            site.add_warning_message("%s pages were not included in sitemap"%(page_missing_sitemap))

        if orphan_page > 0:
            site.add_info_message("%s pages were found in the sitemap, but not accessible from elsewhere in the site."%(page_missing_sitemap))

        
    #6 - Verify that no public pages are blocked by robots.txt
    rp = robotparser.RobotFileParser()
    rp.set_url(site.robots_url)
    rp.read()
    if robots_link.response_code == 200:
        for link_url in site.parsed_links:
            link = site.parsed_links[link_url]
            accessible_to_robots = rp.can_fetch("*", link.url)
            link.accessible_to_robots = accessible_to_robots
            if not accessible_to_robots:
                link.add_info_message("Page is accessible, but not to robots.")
            