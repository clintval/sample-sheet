# Tutorial


To demonstrate the features of this library we will use a test file available at this remote location:

- [`sample-sheet/tests/resources/paired-end-single-index.csv`](tests/resources/paired-end-single-index.csv)

```python
from sample_sheet import SampleSheet

url = 'https://raw.githubusercontent.com/clintval/sample-sheet/master/tests/resources/paired-end-single-index.csv'

sample_sheet = SampleSheet(url)
```

The metadata of the sample sheet can be accessed with the `Header`, `Reads` and, `Settings` attributes:

```python
>>> sample_sheet.Header.Assay
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

Sample sheets can be created _de novo_ and written to a file-like object. The following snippet shows how to add attributes to mandatory sections, add optional user-defined sections, and add samples before writing to the standard output.

```python
import sys

sample_sheet = SampleSheet()

# [Header] section
# Adding an attribute with spaces must be done with the add_attr() method
sample_sheet.Header.IEM4FileVersion = 4
sample_sheet.Header.add_attr(attr='Investigator_Name', value='jdoe', name='Investigator Name')

# [Settings] section
sample_sheet.Settings.CreateFastqForIndexReads = 1
sample_sheet.Settings.BarcodeMismatches = 2

# Optional sample sheet sections can be added and then accessed
sample_sheet.add_section('Manifests')
sample_sheet.Manifests.PoolDNA = "DNAMatrix.txt"

# Specify a paired-end kit with 151 template bases per read
sample_sheet.Reads = [151, 151]

# Add a single-indexed sample with both a name, ID, and index
sample = Sample(dict(Sample_ID='1823A', Sample_Name='1823A-tissue', index='ACGT'))
sample_sheet.add_sample(sample)

# Write to standard outpout!
sample_sheet.write(sys.stdout)
```

```python
"""
[Header],,
IEM4FileVersion,4,
Investigator Name,jdoe,
,,
[Reads],,
151,,
151,,
,,
[Manifests],,
PoolDNA,DNAMatrix.txt,
,,
[Settings],,
CreateFastqForIndexReads,1,
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

#### Using the CLI App

Along with an option for pretty-printing the sample sheet to terminal (`sample_sheet totable`), one can stream the sample sheet into JSON:

```bash
❯ sample-sheet tojson paired-end-single-index.csv | jq
{
  "Header": {
    "IEM1FileVersion": "4",
    "Investigator Name": "jdoe",
    "Experiment Name": "exp001",
    "Date": "11/16/2017",
    "Workflow": "SureSelectXT",
    "Application": "NextSeq FASTQ Only",
    "Assay": "SureSelectXT",
    "Description": "A description of this flow cell",
    "Chemistry": "Default"
  },
  "Reads": [
    151,
    151
  ],
  "Settings": {
    "CreateFastqForIndexReads": "1",
    "BarcodeMismatches": "2"
  },
  "Data": [
    {
      "Sample_Project": "exp001",
      "Description": "0.5x treatment",
      "Reference_Name": "mm10",
      "Sample_Name": "1823A-tissue",
      "index": "GAATCTGA",
      "Library_ID": "2017-01-20",
      "Read_Structure": "151T8B151T",
      "Sample_ID": "1823A",
      "Target_Set": "Intervals-001"
    },
    ...
  ]
}
```

