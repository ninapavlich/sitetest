def test_site_redirects(old_links, success_messages, error_messages):
	"""
	For each old link, verify that it gets a permanent redirect header and that the subsequent page is 200
	
	"""
	return success_messages, error_messages