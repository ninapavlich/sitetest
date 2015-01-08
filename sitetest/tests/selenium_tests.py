import os
import sys
import unittest
import importlib

def test_selenium(site, automated_test_dir, verbose=False):
    
    if verbose:
        print "Testing from dir %s"%(automated_test_dir)
    classes = []

    all_tests = unittest.TestLoader().discover(automated_test_dir, pattern='*.py')
    site.test_results = unittest.TextTestRunner(verbosity=1).run(all_tests)

    if len(site.test_results.errors) > 0:
        site.add_error_message('%s Errors found when running tests'%(len(site.test_results.errors)), len(site.test_results.errors))
    if len(site.test_results.failures) > 0:
        site.add_error_message('%s Failures found when running tests'%(len(site.test_results.failures)), len(site.test_results.failures))
                
    print classes
