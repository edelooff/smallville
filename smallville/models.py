import re

from sqlalchemy import inspect
from sqlalchemy.ext.declarative import (
    as_declarative,
    declared_attr)
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import (
    Column,
    ForeignKey,
    MetaData,
    UniqueConstraint)
from sqlalchemy.sql.sqltypes import (
    Integer,
    Date,
    Enum,
    Text)


# #############################################################################
# Declarative base and helper functions to simplify models
#
def cascading_key(reference, onupdate='CASCADE', ondelete='CASCADE', **kwds):
    """Returns a Foreign Key, fully cascading by default."""
    foreign_key = ForeignKey(reference, onupdate=onupdate, ondelete=ondelete)
    kwds.setdefault('index', True)
    return column(foreign_key, **kwds)


def column(*args, **kwds):
    """Returns a column, NOT nullable by default."""
    kwds.setdefault('nullable', False)
    return Column(*args, **kwds)


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
class Base(object):
    """Extended SQLAlchemy declarative base class."""
    id = Column(Integer, primary_key=True)

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
# Models
#
class City(Base):
    __repr_args__ = 'name', 'size_code'

    # Column definition
    name = column(Text, unique=True)
    size_code = column(Enum('S', 'M', 'L', 'XL', name='ck_city_size_type'))

    # Relationships
    citizens = relationship('Person', back_populates='city')
    companies = relationship('Company', back_populates='city')


class Company(Base):
    __repr_args__ = 'name', 'industry'

    # Column definition
    name = column(Text)
    industry = column(Text)
    city_id = cascading_key('city.id')

    # Relationships
    city = relationship('City', back_populates='companies')
    contracts = relationship('Employee', back_populates='company')
    employees = relationship('Person', secondary='employee', viewonly=True)


class Employee(Base):
    __repr_args__ = 'salary',
    __table_args__ = UniqueConstraint('person_id', 'company_id'),

    # Column definition
    person_id = cascading_key('person.id')
    company_id = cascading_key('company.id')
    role = column(Enum('director', 'manager', 'worker', name='ck_role_type'))
    salary = column(Integer)

    # Relationships
    person = relationship('Person', back_populates='employment')
    company = relationship('Company', back_populates='contracts')


class Person(Base):
    __repr_args__ = 'first_name', 'last_name', 'email'

    # Column definition
    first_name = column(Text)
    last_name = column(Text)
    birthday = column(Date)
    sex = column(Enum('f', 'm', 'x', name='ck_sex_type'))
    city_id = cascading_key('city.id')
    self_employment_income = column(Integer, nullable=True)

    # Relationships
    city = relationship('City', back_populates='citizens')
    employment = relationship('Employee', back_populates='person')
    employer = relationship(
        'Company',
        back_populates='employees',
        secondary='employee',
        uselist=False)
