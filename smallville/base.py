import re

from sqlalchemy import inspect
from sqlalchemy.ext.declarative import (
    as_declarative,
    declared_attr)
from sqlalchemy.sql.schema import (
    Column,
    ForeignKey,
    MetaData)


# #############################################################################
# Declarative base, naming convention etc
#
def metadata():
    """Returns shared metadata instance with naming convention."""
    naming_convention = {
        'ix': 'ix_%(column_0_label)s',
        'uq': 'uq_%(table_name)s_%(column_0_name)s',
        'ck': 'ck_%(table_name)s_%(constraint_name)s',
        'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
        'pk': 'pk_%(table_name)s'}
    return MetaData(naming_convention=naming_convention)


@as_declarative(metadata=metadata())
class Base:
    """Extended SQLAlchemy declarative base class."""
    @declared_attr
    def __tablename__(cls):
        """Returns a table name with words separated by underscores."""
        return re.sub('(?!^)([A-Z]+)', r'_\1', cls.__name__).lower()

    def __repr__(self):
        """Simple object representation with option to render args.

        Attributes that should be included in the representation should be
        assigned to the __repr_args__ (tuple) class variable.
        """
        identity = inspect(self).identity
        if identity is not None:
            identity = ', '.join(map(str, identity))
        model_name = type(self).__name__
        if hasattr(self, '__repr_args__'):
            args = [(arg, getattr(self, arg)) for arg in self.__repr_args__]
            argstring = ', '.join('{}={!r}'.format(*pair) for pair in args)
            return f'<{model_name} [{identity}], {argstring}>'
        return f'<{model_name} [{identity}]>'


# #############################################################################
# column definition utility functions
#
def column(*args, **kwds):
    """Returns a column, NOT nullable by default."""
    kwds.setdefault('nullable', False)
    return Column(*args, **kwds)


def foreign_key(reference, onupdate='CASCADE', ondelete='CASCADE', **kwds):
    """Returns a Foreign Key, fully cascading by default."""
    foreign_key = ForeignKey(reference, onupdate=onupdate, ondelete=ondelete)
    kwds.setdefault('index', True)
    return column(foreign_key, **kwds)
