import setuptools
import sys

from os import path

if sys.version_info < (3, 6):
    sys.exit(f'Python < 3.6 will not be supported.')

this_directory = path.abspath(path.dirname(__file__))

with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

PACKAGE: str = 'sample_sheet'

setuptools.setup(
    name='sample-sheet',
    version='0.9.2',
    author='clintval',
    author_email='valentine.clint@gmail.com',
    description='An Illumina Sample Sheet parsing library',
    url='https://github.com/clintval/sample-sheet',
    download_url=f'https://github.com/clintval/sample-sheet/archive/0.9.2.tar.gz',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    zip_safe=True,
    packages=setuptools.find_packages(where='./'),
    install_requires=['click', 'requests', 'tabulate', 'terminaltables'],
    extras_require={'smart_open': ['smart_open>=1.5.4']},
    scripts=['scripts/sample-sheet'],
    keywords='illumina samplesheet sample sheet parser bioinformatics',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    project_urls={
        'Documentation': 'https://sample-sheet.readthedocs.io',
        'Issue-Tracker': 'https://github.com/clintval/sample-sheet/issues',
    },
)
