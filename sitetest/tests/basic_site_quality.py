from ..core.retrieve_all_urls import get_or_create_link_object, load_link_object


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

	#3 - Test thisShouldNotExist
	error_link = get_or_create_link_object(error_url, current_urls, canonical_domain, domain_aliases)
	response, messages = load_link_object(error_link, canonical_domain, domain_aliases, messages, 404)
	
	return current_urls, messages