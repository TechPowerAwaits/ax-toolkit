==========
ax-invconv
==========

This script generates an Axelor-importable CSV file from an inventory list.

------------


Requirements
------------
- `Python 3.9 or later <https://www.python.org/downloads/>`_
- `openpyxl <https://pypi.org/project/openpyxl/>`_
- `progress <https://pypi.org/project/progress/>`_

Poetry is used to install the dependencies. Click `here <https://python-poetry.org/docs/>`_ for instructions on how to install Poetry.

Running the script
------------------
Before running the script, if you haven't already, run:

::

    poetry install

inside the project directory. This will install all dependencies.


Then to run the actual script:

::

    poetry run python ax-invconv.py

License
-------
Most of the script is licensed under the `0BSD <http://landley.net/toybox/license.html>`_ with the exception of cell_pos.py, which is partially licensed under the `Zlib <https://opensource.org/licenses/Zlib>`_ License.