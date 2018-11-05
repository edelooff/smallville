from itertools import chain

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
    _links_higher = relationship(
        'TransportLink',
        back_populates='lower_city',
        foreign_keys='TransportLink.lower_city_id')
    _links_lower = relationship(
        'TransportLink',
        back_populates='higher_city',
        foreign_keys='TransportLink.higher_city_id')

    @property
    def transport_links(self):
        """Mapping of all transport links and associated costs."""
        def link_getter(relative):
            for link in getattr(self, f'_links_{relative}'):
                yield getattr(link, f'{relative}_city'), link.distance
        return dict(chain(link_getter('higher'), link_getter('lower')))


class Company(Base):
    __repr_args__ = 'name', 'industry'

    # Column definition
    id = column(Integer, primary_key=True)
    name = column(Text)
    industry = column(Text)
    city_id = foreign_key('city.id')

    # Relationships
    city = relationship('City', back_populates='companies')
    contracts = relationship('Employment', back_populates='company')
    employees = relationship('Person', secondary='employment', viewonly=True)


class Employment(Base):
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
    __repr_args__ = 'first_name', 'last_name', 'gender'

    # Column definition
    id = column(Integer, primary_key=True)
    first_name = column(Text)
    last_name = column(Text)
    birthday = column(Date)
    gender = column(Enum('f', 'm', 'x', name='ck_gender_type'))
    city_id = foreign_key('city.id')
    self_employment_income = column(Integer, nullable=True)

    # Relationships
    city = relationship('City', back_populates='citizens')
    employment = relationship('Employment', back_populates='person')
    employer = relationship(
        'Company',
        back_populates='employees',
        secondary='employment',
        uselist=False)


class TransportLink(Base):
    __repr_args__ = 'lower_city_id', 'higher_city_id', 'distance'

    # Column definition
    lower_city_id = foreign_key('city.id', index=False, primary_key=True)
    higher_city_id = foreign_key('city.id', primary_key=True)
    distance = column(Integer)

    # Relationships
    lower_city = relationship(
        'City',
        back_populates='_links_higher',
        foreign_keys=lower_city_id)
    higher_city = relationship(
        'City',
        back_populates='_links_lower',
        foreign_keys=higher_city_id)
