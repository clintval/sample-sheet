Quick Start
===========

To demonstrate the features of this library we will use a test file at an HTTPS endpoint.
To follow along, ensure you have the `smart_open` library installed!

.. code-block:: python

   >>> from sample_sheet import SampleSheet
   >>> url = 'https://raw.githubusercontent.com/clintval/sample-sheet/master/tests/resources/paired-end-single-index.csv'
   >>> sample_sheet = SampleSheet(url)


The metadata of the sample sheet can be accessed with the ``Header``,
``Reads`` and, ``Settings`` attributes:

.. code-block:: python

   >>> sample_sheet.Header.Assay
   'SureSelectXT'
   >>> sample_sheet.Reads
   [151, 151]
   >>> sample_sheet.is_paired_end
   True
   >>> sample_sheet.Settings.BarcodeMismatches
   '2'

The samples can be accessed directly or *via* iteration:

.. code-block:: python

   >>> sample_sheet.samples
   [Sample({'Sample_ID': '1823A', 'Sample_Name': '1823A-tissue', 'index': 'GAATCTGA'}),
    Sample({'Sample_ID': '1823B', 'Sample_Name': '1823B-tissue', 'index': 'AGCAGGAA'}),
    Sample({'Sample_ID': '1824A', 'Sample_Name': '1824A-tissue', 'index': 'GAGCTGAA'}),
    Sample({'Sample_ID': '1825A', 'Sample_Name': '1825A-tissue', 'index': 'AAACATCG'}),
    Sample({'Sample_ID': '1826A', 'Sample_Name': '1826A-tissue', 'index': 'GAGTTAGC'}),
    Sample({'Sample_ID': '1826B', 'Sample_Name': '1823A-tissue', 'index': 'CGAACTTA'}),
    Sample({'Sample_ID': '1829A', 'Sample_Name': '1823B-tissue', 'index': 'GATAGACA'})]
   >>> first_sample, *other_samples = list(sample_sheet)
   >>> first_sample
   Sample({'Sample_ID': '1823A', 'Sample_Name': '1823A-tissue', 'index': 'GAATCTGA'})

Defining Sample Read Structures
-------------------------------

If a column labeled ``Read_Structure`` is provided *per* sample, then
additional functionality is enabled.

.. code-block:: python

   >>> first_sample, *_ = sample_sheet.samples
   >>> first_sample.Read_Structure
   ReadStructure(structure='151T8B151T')
   >>> first_sample.Read_Structure.total_cycles
   310
   >>> first_sample.Read_Structure.tokens
   ['151T', '8B', '151T']

Sample Sheet Creation
---------------------

Sample sheets can be created *de novo* and written to a file-like
object. The following snippet shows how to add attributes to mandatory
sections, add optional user-defined sections, and add samples before
writing to nowhere.

.. code-block:: python

   >>> import os
   >>> from sample_sheet import SampleSheet, Sample
   >>> sample_sheet = SampleSheet()

   # [Header] section
   # Adding an attribute with spaces must be done with the add_attr() method
   >>> sample_sheet.Header['IEM4FileVersion'] = 4
   >>> sample_sheet.Header['Investigator Name'] = 'jdoe'

   # [Settings] section
   >>> sample_sheet.Settings['CreateFastqForIndexReads'] = 1
   >>> sample_sheet.Settings['BarcodeMismatches'] = 2

   # Optional sample sheet sections can be added and then accessed
   >>> sample_sheet.add_section('Manifests')
   >>> sample_sheet.Manifests['PoolDNA'] = "DNAMatrix.txt"

   # Specify a paired-end kit with 151 template bases per read
   >>> sample_sheet.Reads = [151, 151]

   # Add a single-indexed sample with both a name, ID, and index
   >>> sample = Sample(dict(Sample_ID='1823A', Sample_Name='1823A-tissue', index='ACGT'))
   >>> sample_sheet.add_sample(sample)

   # Write the Sample Sheet!
   >>> sample_sheet.write(open(os.devnull, 'w'))
