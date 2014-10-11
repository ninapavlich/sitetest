sitetest
========

Python library for testing websites

##Requirements:
```
brew install enchant
```

##Usage:

```python
from sitetest import testAll
canonical_domain = 'https://www.example.com'
domain_aliases = [
	'http://www.example.com',
	'https://example.com',
	'http://example.com'
]
results_file = 'test_output.html'
testAll(canonical_domain, domain_aliases, results_file)
```