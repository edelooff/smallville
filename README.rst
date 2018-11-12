SmallVille
##########

A collection of SQLAlchemy_ models and scripts to create a small-scale model for a society.


Design goals
============

* Creating a database to model aspects of a small society, as a source for SQL query exploration;
* A simple set of ORM classes to model tables, and explore individual objects interactively.


Requirements
============

To play along at home, you'll need the following:

* Python 3 (developed against py3.6)
* Postgresql (developed against 10)


Installation
============

To start using ``SmallVille``, the easiest way is to clone this repository and install the package into a fresh Python `virtualenv`_. This keeps it separate from other system Python packages and avoids requiring elevated permissions. The following commands will clone the project and install it (assuming recent Ubuntu linux):

.. code-block:: bash

    git clone https://github.com/edelooff/smallville.git
    cd smallville
    virtualenv -p python3 env
    source env/bin/activate
    pip install -e .


Creating the database
---------------------

The seed script will connect to a database named ``smallville`` as the current user, and assume to be able to drop/create tables in it. The steps below will create a database and set the owner to the current user. They're assuming a Ubuntu environment, but should be mostly portable:

.. code-block:: bash

    sudo -u postgres createdb smallville -O $(whoami)


Running the seed script
-----------------------

Once the database is created, the seed script can be used to populate it. For this, activate the virtualenv, run the seed script and either start a Python session to interact using SQLAlchemy, or connect using psql_.

.. code-block:: bash

    cd /path/to/smallville
    source env/bin/activate
    python scripts/seed.py
    psql smallville


..  _psql: https://www.postgresql.org/docs/9.2/static/app-psql.html
..  _sqlalchemy: https://www.sqlalchemy.org/
..  _virtualenv: http://docs.python-guide.org/en/latest/dev/virtualenvs/
