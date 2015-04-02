import urllib2
def reload_url(url, USER_AGENT_STRING):
	
	request = urllib2.Request(url)
	request.add_header('User-agent',USER_AGENT_STRING)
	response = urllib2.urlopen(request)
	print "RESPONSE:"
	print response.code
	return response
