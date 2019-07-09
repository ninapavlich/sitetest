import logging
import traceback

import requests
import robotparser
from urlparse import urlparse
import subprocess

from ..core.models import HEADERS, TLSAV1dapter

logger = logging.getLogger('sitetest')


def test_basic_site_quality(site, verbose=False):
    """
    This tests for robots.txt, sitemap.xml, top-level favicon.ico, test 400 page
    """

    if verbose:
        logger.debug('Running site quality tests...')

    # robots_error = site.get_or_create_message_category('robots-error', "Page is not accessible based on robots.txt", 'warning')

    canonical_domain = site.canonical_domain
    homepage_link = site.get_or_create_link_object(canonical_domain, None)

    if canonical_domain.endswith("/"):
        favicon_url = "%sfavicon.ico" % (canonical_domain)
        error_url = "%sthisShouldNotExist" % (canonical_domain)
        image_error_url = "%sthisShouldNotExist.jpg" % (canonical_domain)
    else:
        favicon_url = "%s/favicon.ico" % (canonical_domain)
        error_url = "%s/thisShouldNotExist" % (canonical_domain)
        image_error_url = "%s/thisShouldNotExist.jpg" % (canonical_domain)

    # 1 - Test robots.txt
    robots_link = site.get_or_create_link_object(site.robots_url)
    robots_link.robots_url = False
    site.load_link(robots_link, False, 200)

    # 2 - Test sitemap.xml
    sitemap_links = site.sitemap_links

    # 3 - Test favicon.ico
    favicon_link = site.get_or_create_link_object(favicon_url)
    site.load_link(favicon_link, False, 200)

    # 4 - Test thisShouldNotExist
    error_link = site.get_or_create_link_object(error_url)
    site.load_link(error_link, False, 404)

    image_error_link = site.get_or_create_link_object(image_error_url)
    site.load_link(image_error_link, False, 404)

    # #5 - Verify that sitemap matches up with the actual pages
    if len(sitemap_links) > 0:
        for sitemap_link in sitemap_links:
            for link_url in sitemap_link.hyper_links:
                link_item = sitemap_link.hyper_links[link_url]
                link_item.has_sitemap_entry = True

    # #6 - Verify that no public pages are blocked by robots.txt
    rp = robotparser.RobotFileParser()
    rp.set_url(site.robots_url)
    rp.read()
    if robots_link.response_code == 200:
        for link_url in site.parsed_links:
            link = site.parsed_links[link_url]
            if link.is_internal_html:
                accessible_to_robots = rp.can_fetch("*", link.url)
                link.accessible_to_robots = accessible_to_robots

    if 'https' in canonical_domain:
        ssl_certificate_error = site.get_or_create_message_category('ssl-certificate-error', "SSL Certificate could not be verified", 'danger')
        server_has_poodle_vulnerability_error = site.get_or_create_message_category('server-poodle-vulnerability', "Server Allows SSL3.0; has POODLE vulnerability", 'danger')
        server_has_heartbleed_vulnerability_error = site.get_or_create_message_category('server-heartbleed-vulnerability', "Server has heartbleed vulnerability", 'danger')

        # 7 -- Verify SSL Cert:
        if verbose:
            logger.debug('Verifying SSL Cert...')
        try:
            error = None
            if site.use_basic_auth:
                auth = requests.auth.HTTPBasicAuth(site.basic_auth_username, site.basic_auth_password)
            else:
                auth = None

            session = requests.Session()
            session.mount('https://', TLSAV1dapter())
            session.get(canonical_domain, headers=HEADERS, auth=auth, verify=True, timeout=10)

        except requests.exceptions.Timeout:
            error = "Timeout when testing SSL Certificate"
        except requests.exceptions.TooManyRedirects:
            error = "TooManyRedirects when testing SSL Certificate"
        except requests.exceptions.RequestException as e:
            error = "Request Exception when testing SSL Certificate: %s" % (e)
        except Exception:
            error = "Unknown Exception when testing SSL Certificate: %s" % (traceback.format_exc())

        if error:
            homepage_link.add_error_message(error, ssl_certificate_error)

        # 8 -- Verify SSL Security:
        try:
            if verbose:
                logger.debug('Verifying SSL Security...')

            parsed_uri = urlparse(canonical_domain)
            p = subprocess.Popen(['sslyze', '--regular', parsed_uri.netloc], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            site.ssl_security_output = out

            server_has_heartbleed_vulnerability = 'Not vulnerable to Heartbleed' not in out
            if server_has_heartbleed_vulnerability:
                homepage_link.add_error_message("Server has heartbleed vulnerability. See &ldquo;Site Info&rdquo; Tab for more info.", server_has_heartbleed_vulnerability_error)

            server_has_poodle_vulnerability = 'SSLV3 Cipher Suites:\n      Server rejected all cipher suites.' not in out
            if server_has_poodle_vulnerability:
                homepage_link.add_error_message("Server has POODLE vulnerability. See &ldquo;Site Info&rdquo; Tab for more info.", server_has_poodle_vulnerability_error)
        except Exception:
            logger.error("Error testing SSL. Ensure sslyze is installed. %s" % (traceback.format_exc()))
