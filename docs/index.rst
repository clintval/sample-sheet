Welcome to the ``sample-sheet`` Documentation!
==============================================

Parse Illumina sample sheets with Python.

.. code-block:: bash

    ❯ pip install sample-sheet

Or install with the Conda package manager after setting up your `Bioconda channels <https://bioconda.github.io/user/install.html#set-up-channels>`_:

.. code-block:: bash

    ❯ conda install sample-sheet

Which should be equivalent to:

.. code-block:: bash

    ❯ conda install -c bioconda -c conda-forge -c defaults sample-sheet

Features
--------

- Roundtrip reading, editing, and writing of Sample Sheets
- *de novo* creation creation of Sample Sheets
- Exporting Sample Sheets to JSON
- Can programmatically replace `Illumina's Experiment Manager <https://support.illumina.com/sequencing/sequencing_software/experiment_manager.html>`_

Documentation
-------------

.. toctree::
   :maxdepth: 2

   quick-start
   sample_sheet
   CONTRIBUTING
