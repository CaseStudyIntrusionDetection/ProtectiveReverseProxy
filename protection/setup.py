from setuptools import find_packages, setup
import os

setup(
    name='src',
    packages=find_packages(),
    version=os.environ.get('PRP_VERSION'),
    description='The part of the systeme detecting the malicious requests.',
    author='CaseStudy IntrusionDetection',
    license='GPLv3',
)
