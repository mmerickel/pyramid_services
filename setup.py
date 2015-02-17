import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
except IOError:
    README = CHANGES = ''

requires = [
    'pyramid',
    'zope.interface',
]

tests_require = requires + [
    'coverage',
    'nose',
    'webtest',
]

setup(
    name='pyramid_services',
    version='0.1.1',
    description='A service layer abstraction for the Pyramid Web Framework.',
    long_description=README + '\n\n' + CHANGES,
    # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Pyramid',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    keywords='pyramid services service layer',
    author='Michael Merickel',
    author_email='michael@merickel.org',
    url='https://github.com/mmerickel/pyramid_services',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    extras_require={
        'testing': tests_require,
    },
    tests_require=tests_require,
    test_suite='pyramid_services',
    entry_points={
    },
)
