from setuptools import setup

setup(
    name='sample_sheet',
    packages=['sample_sheet'],
    version='0.1.0',
    description='An Illumina Sample Sheet parsing utility.',
    long_description=open('README.md').read().strip(),
    author='clintval',
    author_email='valentine.clint@gmail.com',
    url='https://github.com/clintval/sample-sheet',
    download_url='https://github.com/clintval/sample-sheet/archive/v0.1.0.tar.gz',  # noqa
    py_modules=['sample_sheet'],
    install_requires=[
        'click',
        'smart_open',
        'tabulate',
        'terminaltables',
    ],
    extras_require={
        'test': ['nose'],
        'fancytest': ['nose', 'nose-progressive', 'coverage'],
    },
    scripts=[
        'scripts/csv-whitespace-strip',
        'scripts/sample-sheet-summary',
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
