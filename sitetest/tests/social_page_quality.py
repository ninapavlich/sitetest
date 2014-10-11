def test_social_page_quality(links, canonical_domain, domain_aliases, success_messages, error_messages):
	"""
	For each page, verify that there are twitter, facebook and google attributes
	"""
	return links, success_messages, error_messages