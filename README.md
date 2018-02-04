<h1 align="center">sample-sheet</h2>

<p align="center">A Python 3.6 library for handling Illumina sample sheets</p>

<p align="center">
  <a href="#installation"><strong>Installation</strong></a>
  ·
  <a href="#tutorial"><strong>Tutorial</strong></a>
  ·
  <a href="#command-line-utility"><strong>Command Line Utility</strong></a>
  ·
  <a href="#contributing"><strong>Contributing</strong></a>
</p>

<p align="center">
  <a href="https://travis-ci.org/clintval/sample-sheet">
    <img src="https://travis-ci.org/clintval/sample-sheet.svg?branch=master"></img>
  </a>

  <a href="https://codecov.io/gh/clintval/sample-sheet">
    <img src="https://codecov.io/gh/clintval/sample-sheet/branch/master/graph/badge.svg"></img>
  </a>

  <a href="https://badge.fury.io/py/sample_sheet">
    <img src="https://badge.fury.io/py/sample_sheet.svg" alt="PyPI version"></img>
  </a>

  <a href="https://github.com/clintval/sample-sheet/issues">
    <img src="https://img.shields.io/github/issues/clintval/sample-sheet.svg"></img>
  </a>

  <a href="https://github.com/clintval/sample-sheet/blob/master/LICENSE">
    <img src="https://img.shields.io/github/license/clintval/sample-sheet.svg"></img>
  </a>
</p>

<br>

<h3 align="center">Installation</h3>

```
❯ pip install sample_sheet
```

<br>

<h3 align="center">Tutorial</h3>

A sample sheet can be read from S3, HDFS, WebHDFS, HTTP as well as local (compressed or not).

```python
>>> from sample_sheet import SampleSheet 
>>> SampleSheet('s3://bucket/prefix/SampleSheet.csv')
SampleSheet("s3://bucket/prefix/SampleSheet.csv")
```

An example sample sheet can be found at [`tests/resources/paired-end-single-index.csv`](tests/resources/paired-end-single-index.csv).

```python
>>> from sample_sheet import SampleSheet
>>>
>>> url = 'https://raw.githubusercontent.com/clintval/sample-sheet/master/tests/resources/paired-end-single-index.csv'
>>> sample_sheet = SampleSheet(url)
```

The metadata of the sample sheet can be accessed with the `Header`, `Reads` and, `Settings` attributes:

```python
>>> sample_sheet.header.Assay
'SureSelectXT'

>>> sample_sheet.Reads
[151, 151]

>>> sample_sheet.is_paired_end
True

>>> sample_sheet.Settings.BarcodeMismatches
'2'
```

The samples can be accessed directly or _via_ iteration:

```python
>>> sample_sheet.samples
[Sample({"Sample_ID": "1823A", "Sample_Name": "1823A-tissue", "index": "GAATCTGA"}),
 Sample({"Sample_ID": "1823B", "Sample_Name": "1823B-tissue", "index": "AGCAGGAA"}),
 Sample({"Sample_ID": "1824A", "Sample_Name": "1824A-tissue", "index": "GAGCTGAA"}),
 Sample({"Sample_ID": "1825A", "Sample_Name": "1825A-tissue", "index": "AAACATCG"}),
 Sample({"Sample_ID": "1826A", "Sample_Name": "1826A-tissue", "index": "GAGTTAGC"}),
 Sample({"Sample_ID": "1826B", "Sample_Name": "1823A-tissue", "index": "CGAACTTA"}),
 Sample({"Sample_ID": "1829A", "Sample_Name": "1823B-tissue", "index": "GATAGACA"})]

>>> for sample in sample_sheet:
>>>     print(sample)
>>>     break
"1823A"
```

If a column labeled `Read_Structure` is provided _per_ sample, then additional functionality is enabled.

```python
>>> first_sample, *_ = sample_sheet.samples
>>> first_sample.Read_Structure
ReadStructure(structure="151T8B151T")

>>> first_sample.Read_Structure.total_cycles
310

>>> first_sample.Read_Structure.tokens
['151T', '8B', '151T']
```

#### Sample Sheet Creation

Sample sheets can be created _de novo_ and written to a file-like object:

```python
>>> sample_sheet = SampleSheet()
>>>
>>> sample_sheet.Header.IEM4FileVersion = 4
>>> sample_sheet.Header.add_attr(
>>>     attr='Investigator_Name',
>>>     value='jdoe',
>>>     name='Investigator Name')
>>>
>>> sample_sheet.Settings.CreateFastqForIndexReads = 1
>>> sample_sheet.Settings.BarcodeMismatches = 2
>>>
>>> sample_sheet.Reads = [151, 151]
>>>
>>> sample = Sample(dict(
>>>     Sample_ID='1823A',
>>>     Sample_Name='1823A-tissue',
>>>     index='ACGT'))
>>>
>>> sample_sheet.add_sample(sample)
>>>
>>> import sys
>>> sample_sheet.write(sys.stdout)
"""
[Header],,
IEM4FileVersion,4,
Investigator Name,jdoe,
,,
[Reads],,
151,,
151,,
,,
[Settings],,
BarcodeMismatches,2,
,,
[Data],,
Sample_ID,Sample_Name,index
1823A,1823A-tissue,ACGT
"""
```

#### IPython Integration

A quick summary of the samples can be displayed in Markdown ASCII or HTML rendered Markdown if run in an IPython environment:

```python
>>> sample_sheet.experimental_design
"""
| Sample_ID   | Sample_Name   | Library_ID   | Description      |
|:------------|:--------------|:-------------|:-----------------|
| 1823A       | 1823A-tissue  | 2017-01-20   | 0.5x treatment   |
| 1823B       | 1823B-tissue  | 2017-01-20   | 0.5x treatment   |
| 1824A       | 1824A-tissue  | 2017-01-20   | 1.0x treatment   |
| 1825A       | 1825A-tissue  | 2017-01-20   | 10.0x treatment  |
| 1826A       | 1826A-tissue  | 2017-01-20   | 100.0x treatment |
| 1826B       | 1823A-tissue  | 2017-01-17   | 0.5x treatment   |
| 1829A       | 1823B-tissue  | 2017-01-17   | 0.5x treatment   |
"""
```

<br>

<h3 align="center">Command Line Utility</h3>

Prints a tabular summary of the sample sheet.

```bash
❯ sample-sheet summary paired-end-single-index.csv
┌Header─────────────┬─────────────────────────────────┐
│ IEM1FileVersion   │ 4                               │
│ Investigator_Name │ jdoe                            │
│ Experiment_Name   │ exp001                          │
│ Date              │ 11/16/2017                      │
│ Workflow          │ SureSelectXT                    │
│ Application       │ NextSeq FASTQ Only              │
│ Assay             │ SureSelectXT                    │
│ Description       │ A description of this flow cell │
│ Chemistry         │ Default                         │
└───────────────────┴─────────────────────────────────┘
┌Settings──────────────────┬──────────┐
│ CreateFastqForIndexReads │ 1        │
│ BarcodeMismatches        │ 2        │
│ Reads                    │ 151, 151 │
└──────────────────────────┴──────────┘
┌Identifiers┬──────────────┬────────────┬──────────┬────────┐
│ Sample_ID │ Sample_Name  │ Library_ID │ index    │ index2 │
├───────────┼──────────────┼────────────┼──────────┼────────┤
│ 1823A     │ 1823A-tissue │ 2017-01-20 │ GAATCTGA │        │
│ 1823B     │ 1823B-tissue │ 2017-01-20 │ AGCAGGAA │        │
│ 1824A     │ 1824A-tissue │ 2017-01-20 │ GAGCTGAA │        │
│ 1825A     │ 1825A-tissue │ 2017-01-20 │ AAACATCG │        │
│ 1826A     │ 1826A-tissue │ 2017-01-20 │ GAGTTAGC │        │
│ 1826B     │ 1823A-tissue │ 2017-01-17 │ CGAACTTA │        │
│ 1829A     │ 1823B-tissue │ 2017-01-17 │ GATAGACA │        │
└───────────┴──────────────┴────────────┴──────────┴────────┘
┌Descriptions──────────────────┐
│ Sample_ID │ Description      │
├───────────┼──────────────────┤
│ 1823A     │ 0.5x treatment   │
│ 1823B     │ 0.5x treatment   │
│ 1824A     │ 1.0x treatment   │
│ 1825A     │ 10.0x treatment  │
│ 1826A     │ 100.0x treatment │
│ 1826B     │ 0.5x treatment   │
│ 1829A     │ 0.5x treatment   │
└───────────┴──────────────────┘
```

<br>

<h3 align="center">Contributing</h3>

Pull requests and issues welcome!

To make a development install:

```bash
❯ git clone git@github.com:clintval/sample-sheet.git
❯ pip install -e 'sample-sheet[fancytest]'
```

To run the tests:

```
❯ ./sample-sheet/run-tests
Name                            Stmts   Miss  Cover
---------------------------------------------------
sample_sheet/__init__.py            1      0   100%
sample_sheet/_sample_sheet.py     280      0   100%
---------------------------------------------------
TOTAL                             281      0   100%

OK!  58 tests, 0 failures, 0 errors in 0.0s
```

