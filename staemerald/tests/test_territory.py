from stemerald.models import Country, State, City
from stemerald.tests.helpers import WebTestCase, As


class TerritoryTestCase(WebTestCase):
    url = '/apiv1/territories'

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        iran = Country(name='Iran', code='ir', phone_prefix=98)
        tehran_state = State(name='Tehran', country=iran)
        tehran_city = City(name='Tehran', state=tehran_state)

        cls.session.add(tehran_city)

        cls.session.commit()

        cls.country1_id = iran.id
        cls.state1_id = tehran_state.id
        cls.city1_id = tehran_city.id

    def test_territory(self):
        result, ___ = self.request(As.anonymous, 'GET', f'{self.url}/countries')

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], self.country1_id)
        self.assertEqual(result[0]['name'], 'Iran')
        self.assertEqual(result[0]['code'], 'ir')

        result, ___ = self.request(
            As.anonymous, 'GET', f'{self.url}/states',
            query_string={'countryId': result[0]['id']}
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], self.state1_id)
        self.assertEqual(result[0]['countryId'], self.country1_id)
        self.assertEqual(result[0]['name'], 'Tehran')

        result, ___ = self.request(
            As.anonymous, 'GET', f'{self.url}/cities',
            query_string={'stateId': result[0]['id']}
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], self.city1_id)
        self.assertEqual(result[0]['stateId'], self.state1_id)
        self.assertEqual(result[0]['name'], 'Tehran')
