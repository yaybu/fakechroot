from setuptools import setup, find_packages
import os

version = '0.0.6'

setup(name='fakechroot',
      version=version,
      url="http://github.com/isotoma/fakechroot",
      description="A fixture for using a fakechroot environment in your tests",
      long_description=open("README.rst").read(),
      author="John Carr",
      author_email="john.carr@isotoma.com",
      license="Apache Software License",
      classifiers = [
          "Intended Audience :: System Administrators",
          "Operating System :: POSIX",
          "License :: OSI Approved :: Apache Software License",
      ],
      packages=find_packages(exclude=['ez_setup']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
      ],
      extras_require = {
          'test': ['unittest2', 'discover', 'mock'],
          },
      )
