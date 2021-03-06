import logging
import unittest

logger = logging.getLogger('sitetest')


def test_selenium(site, automated_test_dir, verbose=False):

    if verbose:
        logger.debug("Testing from dir %s" % (automated_test_dir))

    selenium_errors = site.get_or_create_message_category('selenium-error', "Selenium Errors", 'danger')

    all_tests = unittest.TestLoader().discover(automated_test_dir, pattern='*.py')
    site.test_results = unittest.TextTestRunner(verbosity=1).run(all_tests)

    if len(site.test_results.errors) > 0:
        site.add_warning_message('%s Errors found when running tests' % (len(site.test_results.errors)), selenium_errors, len(site.test_results.errors))
    if len(site.test_results.failures) > 0:
        site.add_error_message('%s Failures found when running tests' % (len(site.test_results.failures)), selenium_errors, len(site.test_results.failures))
