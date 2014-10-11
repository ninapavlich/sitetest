from setuptools import setup, find_packages
#this is a test
setup(name = 'sitetest',
      description = 'Python library for testing websites',
      version = '0.1',
      url = 'https://github.com/ninapavlich/sitetest',
      author = 'Nina Pavlich',
      author_email='nina@ninalp.com',
      license = 'Apache 2.0',
      packages=find_packages(exclude=['ez_setup']),
      zip_safe = False,
      include_package_data=True,
      install_requires = ['setuptools','httplib2','beautifulsoup4', 'jinja2', 'w3c-validator', 'pyenchant', 'pyslack', 'boto'],
      classifiers=[
                   'Development Status :: 1 - Development',
                   'Environment :: Web Environment',
                   'Framework :: Fabric',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python'
                  ]
)