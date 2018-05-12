from setuptools import find_packages, setup


try:
    import pypandoc
    long_description = pypandoc.convert_file('README.md', 'rst')
    long_description = long_description.replace('\r', '')
except (ImportError, OSError):
    import io
    with io.open('README.md', encoding='utf-8') as f:
        long_description = f.read()


PACKAGE = 'sample_sheet'
PACKAGE_NAME = 'sample-sheet'
VERSION = '0.5.0'

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
    extras_require={
        'ci': ['nose', 'codecov'],
        'fancytest': ['nose', 'coverage'],
    },
    scripts=[
        'scripts/sample-sheet',
    ],
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
    ]
)
