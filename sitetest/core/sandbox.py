import logging
import urllib2

logger = logging.getLogger('sitetest')


def reload_url(url, user_agent_string):

    request = urllib2.Request(url)
    request.add_header('User-agent', user_agent_string)
    response = urllib2.urlopen(request)
    logger.info("Response: %s: %s" % (response.code, response))
