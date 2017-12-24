<h1 align="center">sample-sheet</h2>

<p align="center">A Python 3.6 library for handling Illumina sample sheets</p>

<p align="center">
  <a href="#installation"><strong>Installation</strong></a>
  ·
  <a href="#examples"><strong>Examples</strong></a>
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

<h2 align="center">Installation</h3>

Until this package is released on PyPi, one can install directly from the `master` branch with the following command:

```
❯ pip install git@github.com:clintval/sample-sheet.git
```

<br>

<h2 align="center">Examples</h3>

An example sample sheet can be found at [`tests/resources/paired-end-single-index.csv`](tests/resources/paired-end-single-index.csv). This sample sheet will be used for demonstrating the library.

```python
>>> from sample_sheet import SampleSheet

>>> infile = 'tests/resources/paired-end-single-index.csv'
>>> sample_sheet = SampleSheet(infile)
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

The samples of the sample sheet can be accessed directly or _via_ iteration:

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
>>>     print(repr(sample)); break
Sample({"index": "GAATCTGA", "sample_id": "1823A", "sample_name": "1823A-tissue"})
```

If a column name for read structure can be inferred for the samples then additional functionality is enabled.

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

<h2 align="center">Command Line Tools</h3>

<p align="center">
  <a href="#sample-sheet-summary"><strong>sample-sheet-summary</strong></a>
</p>

#### [sample-sheet-summary](#sample-sheet-summary)

Prints a unicode table summary of the sample sheet.

> Note currently broken.
> Output below to give you an idea of what the final result will look like.

```bash
❯ sample-sheet-summary paired-end-single-index.csv
┌Header─────────────┬──┐
│ IEM1FileVersion   │  │
│ Investigator Name │  │
│ Experiment Name   │  │
│ Date              │  │
│ Workflow          │  │
│ Application       │  │
│ Assay             │  │
│ Description       │  │
│ Chemistry         │  │
└───────────────────┴──┘
┌Settings──────────────────┬──────────┐
│ CreateFastqForIndexReads │          │
│ BarcodeMismatches        │          │
│ Reads                    │ 151, 151 │
└──────────────────────────┴──────────┘
┌Identifiers┬──────────────┬────────────┬─────────────┬──────────┬─────────────┬────────┐
│ sample_id │ sample_name  │ library_id │ i7_index_id │ index    │ i5_index_id │ index2 │
├───────────┼──────────────┼────────────┼─────────────┼──────────┼─────────────┼────────┤
│ 1823A     │ 1823A-tissue │ 2017-01-20 │             │ GAATCTGA │             │        │
│ 1823B     │ 1823B-tissue │ 2017-01-20 │             │ AGCAGGAA │             │        │
│ 1824A     │ 1824A-tissue │ 2017-01-20 │             │ GAGCTGAA │             │        │
│ 1825A     │ 1825A-tissue │ 2017-01-20 │             │ AAACATCG │             │        │
│ 1826A     │ 1826A-tissue │ 2017-01-20 │             │ GAGTTAGC │             │        │
│ 1826B     │ 1823A-tissue │ 2017-01-17 │             │ CGAACTTA │             │        │
│ 1829A     │ 1823B-tissue │ 2017-01-17 │             │ GATAGACA │             │        │
└───────────┴──────────────┴────────────┴─────────────┴──────────┴─────────────┴────────┘
```

<br>

<h2 align="center">Contributing</h3>

Pull requests and issues welcome! Before submitting a pull request please ensure your code is tested and that the tests run OK. To use the helper function `run-tests` you must have the test libraries installed. A development install also helps:

```bash
❯ git clone git@github.com:clintval/sample-sheet.git
❯ pip install -e sample-sheet\[test\]
```

To run the tests:

```
❯ ./sample-sheet/run-tests
Name                            Stmts   Miss  Cover
---------------------------------------------------
sample_sheet/__init__.py            1      0   100%
sample_sheet/_sample_sheet.py     272     10    96%
---------------------------------------------------
TOTAL                             273     10    96%

OK!  47 tests, 0 failures, 0 errors in 0.0s
```


