import re
from os.path import join, dirname
from setuptools import setup, find_packages

# reading package version (without reloading it)
with open(join(dirname(__file__), 'staemerald', '__init__.py')) as v_file:
    package_version = re.compile(r".*__version__ = '(.*?)'", re.S).match(v_file.read()).group(1)

dependencies = [
    'restfulpy == 0.40.1',
    'nanohttp == 0.26.1',
    'pymlconf == 0.8.6',
    'sqlalchemy',
    'itsdangerous',
    'redis',
    'sqlalchemy-media == 0.15.0',
    'wand >= 0.4.3',
    'ujson',
    'requests',
    'oath',
    'pycrypto',
    'qrcode',
    'Pillow',

    # deployment
    'alembic',
    'gunicorn',
]

setup(
    name="staemerald",
    version=package_version,
    author="Prefect",
    author_email="mahdi_1373@yahoo.com",
    install_requires=dependencies,
    packages=find_packages(),
    test_suite="staemerald.tests",
    entry_points={
        'console_scripts': [
            'staemerald = staemerald:staemerald.cli_main',
        ]
    },
    message_extractors={'staemerald': [
        ('**.py', 'python', None),
    ]},
)
