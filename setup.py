from setuptools import setup


try:
    import pypandoc
    long_description = pypandoc.convert_file('README.md', 'rst')
    long_description = long_description.replace('\r', '')
except (ImportError, OSError):
    import io
    with io.open('README.md', encoding='utf-8') as f:
        long_description = f.read()


setup(
    name='sample_sheet',
    packages=['sample_sheet'],
    version='0.2.0',
    description='An Illumina Sample Sheet parsing utility.',
    long_description=long_description,
    author='clintval',
    author_email='valentine.clint@gmail.com',
    url='https://github.com/clintval/sample-sheet',
    download_url='https://github.com/clintval/sample-sheet/archive/v0.2.0.tar.gz',  # noqa
    py_modules=['sample_sheet'],
    install_requires=[
        'click',
        'smart_open>=1.5.4',
        'tabulate',
        'terminaltables',
    ],
    extras_require={
        'ci': ['nose', 'codecov'],
        'fancytest': ['nose', 'nose-progressive', 'coverage'],
    },
    scripts=[
#        'scripts/csv-whitespace-strip',
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
