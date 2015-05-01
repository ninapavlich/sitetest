sitetest
========

Sitetest is a python utility for testing websites. The test results are uploaded
to an AWS bucket as static HTML and notifications are sent to a Slack channel.

##Requirements:
```
#enchant is required for spelling
brew install enchant
```

**Example Report:** http://s3.amazonaws.com/cgp-dev/test_results/fw-django-prod-01/2015-04-10_15-01.html

##Example Usage:
```python

from sitetest import testSite

canonical_domain = 'https://www.example.com'
starting_url = 'https://www.example.com'
test_id = "example-site-test-recursive"
recursive = True


credentials = {
    "slack":{
        "SLACK_TOKEN" : "XXXX-XXXXXXXXX-XXXXXXXXX-XXXXXXXXX-XXXXXX",
        "SLACK_CHANNEL" : "#channel",
        "SLACK_USERNAME" : "slackbot"
    },
    "aws":{
        "AWS_ACCESS_KEY_ID" : "XXXXXXXXX",
        "AWS_SECRET_ACCESS_KEY" : "XXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "AWS_STORAGE_BUCKET_NAME" : "bucket-name",
        "AWS_RESULTS_PATH" : "test_results"
    },
    "google":{
        "PRIVATE_KEY_PASSWORD": "XXXXXXXXX",
        "CLIENT_ID": "XXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "EMAIL_ADDRESS": "XXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "PUBLIC_KEY_FINGERPRINTS":"XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    }
}

domain_aliases = [
    'http://www.example.com',
    'https://example.com',
    'http://example.com'
]

options = {
    'recursive':True,
    'test_media':True,
    'test_external_links':True,
    'run_third_party_tests':True,
    'run_security_tests':True,
    'ua_test_list' = {
        'A1 Website Download/5.1.0 (+http://www.microsystools.com/products/website-download/) miggibot':{
            'expected_code':403,
            'test_urls':[
                'http://www.example.com/alpha/',
                'http://www.example.com/beta/'
            ]
        }
    },
    'verbose':True,
    'special_dictionary':['yolo',],
    'ignore_query_string_keys':['next'],
    'alias_query_strings':['page'],
    'ignore_validation_errors':[],
    'skip_urls':['blog'],
    'skip_test_urls':['comments/reply','comments/flag' ],
    'output_unloaded_links':True,
    'screenshots':{
        'default':[1200, 800],
        'mobile':[375, 667]
    },
    'use_basic_auth':True,
    'basic_auth_username':'admin',
    'basic_auth_password':'p@ssw0rd!'
}

testSite(credentials, canonical_domain, domain_aliases, starting_url, test_id, options)
```


##Options:

**If recursive == False,** the test will test only the canonical_domain
**if recursive == True,** the test will recursively test all links found within 
the canonical_domain. It will also test /robots.txt, /sitemap.xml, /favicon.ico 
and /thisShouldNotExist returns a 404

**if test_media == True,** the test will ALSO verify that media files (images, 
docs, zips, etc) return 404s.

**if test_external_links == True,** the test will ALSO verify that external 
links return 404s.

**if run_third_party_tests == True,** the test will validate W3C Compliance for 
up to 20 urls (the W3C has relatively strict limits for API usage), run Google 
PageSpeed tests for up to 1000 urls.

**if run_security_tests == True,** the test will test rate limits and someday 
other tests too.

**if ua_test_list** is set, this will verify that the specified User Agents 
receive the expected code. This test will be run on the test_urls list if 
specified, or the canonical domain if not specified.

**If verbose == True,** you will see log output of the urls as they're parsed 
and the overall test status

**If output_unloaded_links == True,** a list of all links will be included in
the report, including links that weren't loaded. If you have a lot of external
links, this can be set to False to make the report file slightly smaller.

**If screenshots** are defined, then screenshots will be generated at the
sizes specified. These will be uploaded a subdirectory within the test file.
The screenshots are generated using the Firefox driver for Selenium.

**Use use_basic_auth == True,** and specify basic_auth_username and
basic_auth_password if the URLs being tested are password protected with basic
auth.

**canonical_domain** is the domain that we're testing. If you're running a 
non-recursive test on a single url, then canonical_domain should be the single
url that you're testing, e.g. 'https://www.example.com/subfolder/testme/'
```python
canonical_domain = 'https://www.example.com'
```

**domain_aliases** are domains that should be considered equivalent to the 
canonical domain. If a domain alias is found, it will be replaced with the 
canonical domain for testing
```python
domain_aliases = [
	'http://www.example.com',
	'https://example.com',
	'http://example.com'
]
```
**test_id** is a unique identifier for this test. Tests will be uploaded to AWS 
at this url: 
	
	"http://s3.amazonaws.com/AWS_STORAGE_BUCKET_NAME
	/AWS_RESULTS_PATH/test_id/time-and-date-of-test.html"

```python
test_id = "example-site-test-full"
```



**special_dictionary** is a list of words to ignore in the spelling test
```python
special_dictionary = ['yolo',]

```


**ignore_query_string_keys** is a list of query strings to ignore in the urls.
```python
ignore_query_string_keys = ['next',]

```

**alias_query_strings** is a list of query strings to ignore as unique urls. 
These urls will be loaded and tested, but not subjected to 'unique' tests.
```python
alias_query_strings = ['page',]
```


**ignore_validation_errors** is a list of validation messages from w3c to ignore
```python
ignore_validation_errors = ['Bad value X-UA-Compatible for attribute http-equiv 
on element meta.', ]

```


skip_urls is a list of url fragments that, if matched using regex, will not be 
loaded or tested.
```python
skip_urls = ['blog' ]

```

skip_test_urls is a list of url fragments that, if matched using regex, it will 
be loaded but not undergo any further testing.
```python
skip_test_urls = ['comments/reply','comments/flag' ]

```

**credentials** allow you to integrate with third party tools for tests and 
notification. Result notifications are sent to slack. Test results are uploaded 
to Amazon S3. Google Pagespeed is run on each URL for "Full" tests; only the 
API_KEY is needed for that.
