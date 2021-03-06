# FROM: https://github.com/varelaz/varela-python-sitemap-parser/
import lxml.etree
import logging
import traceback

logger = logging.getLogger('sitetest')


class SiteMaps(object):

    def __init__(self, domain, set, recursive):
        self.domain = domain
        self.sitemaps = []
        self.urls = []
        self.fetched_sitemaps = []
        self.set = set
        self.recursive = recursive

    def read_robots(self):
        try:
            robots_link = self.set.get_or_create_link_object(self.set.robots_url, None)
            robots_link.is_robots = True

            self.set.load_link(robots_link, False, 200)

            if robots_link.content:
                for line in robots_link.content.split('\n'):
                    line = line.strip()

                    if line.lower().startswith('sitemap:'):
                        self.sitemaps.append(line[len('Sitemap:'):].strip())

        except Exception as e:
            logger.error("Error Reading Robots: %s" % (traceback.format_exc()))
            logging.exception(e)

    def run(self):
        self.read_robots()
        self.sitemaps = self.sitemaps or [self.set.default_sitemap_url]

        while self.sitemaps and len(self.sitemaps) > 0:
            sitemap_url = self.sitemaps.pop()

            sitemap_link = self.set.get_or_create_link_object(sitemap_url, None)
            sitemap_link.is_sitemap = True
            self.set.load_link(sitemap_link, False, 200, True)
            self.process_sitemap(sitemap_link)

    def process_sitemap(self, sitemap_link):

        namespaces = [
            ('sm', 'http://www.sitemaps.org/schemas/sitemap/0.9'),
        ]

        if not sitemap_link.content:
            return

        xml = sitemap_link.content.encode('utf-8')
        parser = lxml.etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
        tree = lxml.etree.fromstring(xml, parser=parser)

        for sitemap in tree.xpath('//sm:sitemap | //sitemap', namespaces=namespaces):
            for loc in sitemap.xpath('sm:loc | loc', namespaces=namespaces):
                child_sitemap_url = loc.text.strip()
                self.set.get_or_create_link_object(child_sitemap_url, sitemap_link)
                self.sitemaps.append(child_sitemap_url)

        for sitemap in tree.xpath('//sm:url | //url', namespaces=namespaces):
            # TODO: add last update date, rank and update frequency
            for loc in sitemap.xpath('sm:loc | loc', namespaces=namespaces):

                url = loc.text.strip()
                self.urls.append(url)
                logger.debug('Found url (%s)' % (url))
                self.set.get_or_create_link_object(url, sitemap_link)
