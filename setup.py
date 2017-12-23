from setuptools import setup

setup(
    name='sample_sheet',
    packages=['sample_sheet'],
    version='0.0.1',
    description='An Illumina Sample Sheet parsing utility.',
    long_description=open('README.md').read().strip(),
    author='clintval',
    author_email='valentine.clint@gmail.com',
    url='https://github.com/clintval/sample-sheet',
    download_url='https://github.com/clintval/sample-sheet/archive/0.0.1.tar.gz',  # noqa
    py_modules=['sample_sheet'],
    install_requires=[
        'click',
        'smart_open',
        'tabulate',
        'terminaltables',
    ],
    extras_requires={
        'test': ['nose', 'nose-progressive'],
    },
    scripts=[
        'scripts/csv-whitespace-strip',
        'scripts/sample-sheet-summary',
    ],
    license='MIT',
    zip_safe=True,
    keywords='illumina samplesheet sample sheet parser bioinformatics',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ]
)
