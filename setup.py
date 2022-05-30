# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


tests_require = [
    'pyssim',
    'urllib3',
    'pytest'
]


setup(
    name='wikimedia_thumbor',
    version='2.9',
    url='https://phabricator.wikimedia.org/diffusion/THMBREXT/',
    license='MIT',
    author='Gilles Dubuc, Wikimedia Foundation',
    description='Wikimedia Thumbor plugins',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'libthumbor>=2.0.2',
        'manhole',
        'python-memcached',
        'python-swiftclient',
        'thumbor>=7.0.10'
    ],
    extras_require={
        'tests': tests_require,
    },
    python_requires="==3.7",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
