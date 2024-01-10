from setuptools import setup, find_packages

setup(
    name='chu',
    version='0.6',
    packages=find_packages(),
    install_requires=[
        'pika',  # Add other dependencies here
    ],
    author='David Sigley',
    author_email='djsigley@gmail.com',
    description='Library for publishing and receiving events via Pika / RabbitMQ',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/sigularusrex/chu',
)
