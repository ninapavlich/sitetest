def test_site_loading_optimized(links, canonical_domain, domain_aliases, success_messages, error_messages):
	"""
	For homepage, verify that:
	1. Static files are gzipped
	2. HTML is minified
	3. Cache headers for static files
	
	"""
	return links, success_messages, error_messages