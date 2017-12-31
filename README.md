<h1 align="center">sample-sheet</h2>

<p align="center">A Python 3.6 library for handling Illumina sample sheets</p>

<p align="center">
  <a href="#installation"><strong>Installation</strong></a>
  ·
  <a href="#tutorial"><strong>Tutorial</strong></a>
  ·
  <a href="#command-line-tools"><strong>Command Line Tools</strong></a>
  ·
  <a href="#contributing"><strong>Contributing</strong></a>
</p>

<p align="center">
    <img src="https://travis-ci.org/clintval/sample-sheet.svg?branch=master"></img>
    <img src="https://img.shields.io/github/issues/clintval/sample-sheet.svg"></img>
    <img src="https://img.shields.io/github/license/clintval/sample-sheet.svg"></img>
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

>>> url = 'https://raw.githubusercontent.com/clintval/sample-sheet/master/tests/resources/{}'
>>> sample_sheet = SampleSheet(url.format('paired-end-single-index.csv'))
```

The metadata of the sample sheet can be accessed with the `header`, `reads` and, `settings` attributes:

```python
>>> sample_sheet.header.assay
'SureSelectXT'
>>> sample_sheet.reads
[151, 151]
>>> sample_sheet.is_paired
True
>>> sample_sheet.settings.barcode_mismatches
'2'
```

The samples can be accessed directly or _via_ iteration:

```python
>>> sample_sheet.samples
[Sample({"index": "GAATCTGA", "sample_id": "1823A", "sample_name": "1823A-tissue"}),
 Sample({"index": "AGCAGGAA", "sample_id": "1823B", "sample_name": "1823B-tissue"}),
 Sample({"index": "GAGCTGAA", "sample_id": "1824A", "sample_name": "1824A-tissue"}),
 Sample({"index": "AAACATCG", "sample_id": "1825A", "sample_name": "1825A-tissue"}),
 Sample({"index": "GAGTTAGC", "sample_id": "1826A", "sample_name": "1826A-tissue"}),
 Sample({"index": "CGAACTTA", "sample_id": "1826B", "sample_name": "1823A-tissue"}),
 Sample({"index": "GATAGACA", "sample_id": "1829A", "sample_name": "1823B-tissue"})]

>>> for sample in sample_sheet:
>>>     print(repr(sample))
>>>     break
Sample({"index": "GAATCTGA", "sample_id": "1823A", "sample_name": "1823A-tissue"})
```

A quick summary of the samples can be displayed in Markdown ASCII or HTML rendered Markdown if run in an IPython environment:

```python
>>> sample_sheet.experimental_design
"""
| sample_id   | sample_name   | library_id   | description      |
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

If a column name for read structure can be inferred, then additional functionality is enabled.

```python
>>> first_sample, *_ = sample_sheet.samples
>>> first_sample.read_structure
ReadStructure(structure="151T8B151T")
>>> first_sample.read_structure.total_cycles
310
>>> first_sample.read_structure.tokens
['151T', '8B', '151T']
```

<br>

<h3 align="center">Command Line Tools</h3>

<p align="center">
  <a href="#sample-sheet-summary"><strong>sample-sheet-summary</strong></a>
</p>

#### [sample-sheet-summary](#sample-sheet-summary)

Prints a tabular summary of the sample sheet.

```bash
❯ sample-sheet-summary paired-end-single-index.csv
┌Header─────────────┬─────────────────────────────────┐
│ iem1_file_version │ 4                               │
│ investigator_name │ jdoe                            │
│ experiment_name   │ exp001                          │
│ date              │ 11/16/2017                      │
│ workflow          │ SureSelectXT                    │
│ application       │ NextSeq FASTQ Only              │
│ assay             │ SureSelectXT                    │
│ description       │ A description of this flow cell │
│ chemistry         │ Default                         │
└───────────────────┴─────────────────────────────────┘
┌Settings──────────────────────┬──────────┐
│ create_fastq_for_index_reads │ 1        │
│ barcode_mismatches           │ 2        │
│ reads                        │ 151, 151 │
└──────────────────────────────┴──────────┘
┌Identifiers┬──────────────┬────────────┬──────────┬────────┐
│ sample_id │ sample_name  │ library_id │ index    │ index2 │
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
│ sample_id │ description      │
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

