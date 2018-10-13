from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import (
    Integer,
    Date,
    Enum,
    Text)

from . base import (
    Base,
    column,
    foreign_key)


# #############################################################################
# Models
#
class City(Base):
    __repr_args__ = 'name', 'size_code'

    # Column definition
    id = column(Integer, primary_key=True)
    name = column(Text, unique=True)
    size_code = column(Enum('S', 'M', 'L', 'XL', name='ck_city_size_type'))

    # Relationships
    citizens = relationship('Person', back_populates='city')
    companies = relationship('Company', back_populates='city')


class Company(Base):
    __repr_args__ = 'name', 'industry'

    # Column definition
    id = column(Integer, primary_key=True)
    name = column(Text)
    industry = column(Text)
    city_id = foreign_key('city.id')

    # Relationships
    city = relationship('City', back_populates='companies')
    contracts = relationship('Employee', back_populates='company')
    employees = relationship('Person', secondary='employee', viewonly=True)


class Employee(Base):
    __repr_args__ = 'salary',

    # Column definition
    person_id = foreign_key('person.id', index=False, primary_key=True)
    company_id = foreign_key('company.id', primary_key=True)
    role = column(Enum('director', 'manager', 'worker', name='ck_role_type'))
    salary = column(Integer)

    # Relationships
    person = relationship('Person', back_populates='employment')
    company = relationship('Company', back_populates='contracts')


class Person(Base):
    __repr_args__ = 'first_name', 'last_name', 'email'

    # Column definition
    id = column(Integer, primary_key=True)
    first_name = column(Text)
    last_name = column(Text)
    birthday = column(Date)
    sex = column(Enum('f', 'm', 'x', name='ck_sex_type'))
    city_id = foreign_key('city.id')
    self_employment_income = column(Integer, nullable=True)

    # Relationships
    city = relationship('City', back_populates='citizens')
    employment = relationship('Employee', back_populates='person')
    employer = relationship(
        'Company',
        back_populates='employees',
        secondary='employee',
        uselist=False)
