sitetest
========

Python library for testing websites

##Requirements:
```
#enchant is required for spelling
brew install enchant
```

##Usage:

```python
from sitetest import testSite

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
    }
}

"""
Canonical domain is the domain that we're testing. If you're running a 
non-recursive test on a single url, then canonical_domain should be the single
url that you're testing, e.g. 'https://www.example.com/subfolder/testme/'
"""
canonical_domain = 'https://www.example.com'

"""
Domain aliases are domains that should be considered equivalent to the canonical
 domain. If a domain alias is found, it will be replaced with the canonical 
 domain for testing
"""
domain_aliases = [
	'http://www.example.com',
	'https://example.com',
	'http://example.com'
]
"""
Test id is a unique identifier for this test. Tests will be uploaded to AWS at 
this url: "http://s3.amazonaws.com/AWS_STORAGE_BUCKET_NAME/AWS_RESULTS_PATH/test_id/time-and-date-of-test.html"
"""
test_id = "example-site-test-full"

"""
if full == False, the test will check each page for 200 response, test each page
 for Lorem Ipsum and spelling errors and test each page for unique title and 
 description

if full == True, the test will ALSO verify that media files (images, docs, zips,
 etc) are valid, validate W3C Compliance for each URL, Generate browser 
 screenshots (someday), and lint JS and CSS (someday)
"""
full = True 

"""
If recursive == False, the test will test only the canonical_domain
if recursive == True, the test will recursively test all links found within the 
canonical_domain. It will also test /robots.txt, /sitemap.xml, /favicon.ico and 
/thisShouldNotExist returns a 404
"""
recursive = True

"""
special_dictionary is a list of words to ignore in the spelling test
"""
special_dictionary = ['yolo',]

"""
ignore_query_string_keys is a list of query strings to ignore as unique urls
"""
ignore_query_string_keys = ['next',]

"""
ignore_validation_errors is a list of validation messages from w3c to ignore
"""
ignore_validation_errors = ['Bad value X-UA-Compatible for attribute http-equiv on element meta.', ]


testSite(credentials, canonical_domain, domain_aliases, test_id, full, recursive=True, special_dictionary = None, ignore_query_string_keys=None, ignore_validation_errors=None)
```