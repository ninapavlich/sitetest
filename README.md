sitetest
========

Sitetest is a python utility for testing websites. The test results are uploaded
to an AWS bucket as static HTML and notifications are sent to a Slack channel.

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
```

**canonical_domain** is the domain that we're testing. If you're running a 
non-recursive test on a single url, then canonical_domain should be the single
url that you're testing, e.g. 'https://www.example.com/subfolder/testme/'
```python
canonical_domain = 'https://www.example.com'
```

**domain_aliases** are domains that should be considered equivalent to the canonical
 domain. If a domain alias is found, it will be replaced with the canonical 
 domain for testing
```python
domain_aliases = [
	'http://www.example.com',
	'https://example.com',
	'http://example.com'
]
```
**test_id** is a unique identifier for this test. Tests will be uploaded to AWS at 
this url: 
	
	"http://s3.amazonaws.com/AWS_STORAGE_BUCKET_NAME
	/AWS_RESULTS_PATH/test_id/time-and-date-of-test.html"

```python
test_id = "example-site-test-full"
```

**if full == False,** the test will check each page for 200 response, test each page
 for Lorem Ipsum and spelling errors and test each page for unique title and 
 description

**if full == True,** the test will ALSO verify that media files (images, docs, zips,
 etc) are valid, validate W3C Compliance for each URL, Generate browser 
 screenshots (someday), and lint JS and CSS (someday)
```python
full = True 

```


**If recursive == False,** the test will test only the canonical_domain
**if recursive == True,** the test will recursively test all links found within the 
canonical_domain. It will also test /robots.txt, /sitemap.xml, /favicon.ico and 
/thisShouldNotExist returns a 404
```python
recursive = True

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
ignore_validation_errors = ['Bad value X-UA-Compatible for attribute http-equiv on element meta.', ]

```


skip_test_urls is a list of url fragments that, if matched using regex, will be ignored in site tests.
```python
skip_test_urls = ['comments/reply','comments/flag' ]

```


**If verbose == True,** you will see log output of the urls as they're parsed and 
the overall test status
```python
verbose = True
```

EXAMPLE USAGE:
```python


canonical_domain = 'https://www.example.com'
test_id = "example-site-test-full"
full = False
recursive = True
verbose = True


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
    'special_dictionary':['yolo',],
    'ignore_query_string_keys':['next'],
    'alias_query_strings':['page'],
    'ignore_validation_errors':[],
    'skip_test_urls':['comments/reply','comments/flag' ]
}

testSite(credentials, canonical_domain, domain_aliases, test_id, full, 
	recursive, options, verbose)
```