from setuptools import find_packages
from setuptools import setup

with open('README.md', encoding='utf-8') as handle:
    long_description = handle.read()


PACKAGE = 'sample_sheet'
PACKAGE_NAME = 'sample-sheet'
VERSION = '0.7.0'

URL = f'https://github.com/clintval/{PACKAGE_NAME}'
ARTIFACT = f'https://github.com/clintval/{PACKAGE_NAME}/archive/v{VERSION}.tar.gz'  # noqa

setup(
    name=PACKAGE,
    packages=find_packages(),
    version=VERSION,
    description='An Illumina Sample Sheet parsing utility.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='clintval',
    author_email='valentine.clint@gmail.com',
    url=URL,
    download_url=ARTIFACT,
    install_requires=[
        'click',
        'smart_open>=1.5.4',
        'tabulate',
        'terminaltables',
    ],
    extras_require={'ci': ['nose', 'codecov']},
    scripts=['scripts/sample-sheet'],
    license='MIT',
    zip_safe=True,
    keywords='illumina samplesheet sample sheet parser bioinformatics',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ]
)
