# How to Contribute

Pull requests, feature requests, and issues welcome!
The complete test suite is configured through `Tox`:

```bash
❯ cd sample-sheet
❯ pip install tox
❯ tox  # Run entire dynamic / static analysis test suite
```

List all environments with:

```
❯ tox -av
using tox.ini: .../sample-sheet/tox.ini
using tox-3.1.2 from ../tox/__init__.py
default environments:
py36      -> run the test suite with (basepython)
py36-lint -> check the code style
py36-type -> type check the library
py36-docs -> test building of HTML docs

additional environments:
dev       -> the official sample_sheet development environment
```

To run just one environment:

```bash
❯ tox -e py36
```

To pass in positional arguments to a specified environment:

```bash
❯ tox -e py36 -- -x tests/test_sample_sheet.py
```
