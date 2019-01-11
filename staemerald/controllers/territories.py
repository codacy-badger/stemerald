from nanohttp import json
from nanohttp.controllers import RestController
from restfulpy.controllers import ModelRestController
from restfulpy.validation import validate_form, prevent_form

from staemerald.models import City, State, Country


class CityController(ModelRestController):
    __model__ = City

    @json
    @validate_form(exact=['stateId'])
    @City.expose
    def get(self):
        # TODO: Make sure she choose a countryId to prevent getting the whole data
        return City.query


class StateController(ModelRestController):
    __model__ = State

    @json
    @validate_form(exact=['countryId'])
    @State.expose
    def get(self):
        # TODO: Make sure she choose a countryId to prevent getting the whole data
        return State.query


class CountryController(ModelRestController):
    __model__ = Country

    @json
    @prevent_form
    @Country.expose
    def get(self):
        return Country.query


class TerritoryController(RestController):
    cities = CityController()
    states = StateController()
    countries = CountryController()
