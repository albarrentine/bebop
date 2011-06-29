from distutils.core import setup

setup(
    name='bebop',
    version='0.0.1dev',
    description='Solr abstraction library',
    author='Al Barrentine',
    author_email='al@jumo.com',
    url='http://www.github.com/thatdatabaseguy/bebop',
    install_requires=[
        "pysolr",
        "lxml>=2.2.3",
    ],
    packages=['bebop'],
    
    )
