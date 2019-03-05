from os.path import join
from restfulpy.orm import DBSession
from sqlalchemy_media import store_manager

from stemerald.models import *

# noinspection PyArgumentList
from stemerald.tests import STUFF_DIR


# noinspection PyArgumentList
def insert_departments():  # pragma: no cover
    department1 = TicketDepartment()
    department1.title = 'Test Department 1'
    DBSession.add(department1)

    department2 = TicketDepartment()
    department2.title = 'Test Department 2'
    DBSession.add(department2)

    department3 = TicketDepartment()
    department3.title = 'Test Department 3'
    DBSession.add(department3)
    DBSession.flush()


# noinspection PyArgumentList
@store_manager(DBSession)
def insert():  # pragma: no cover
    insert_departments()

    iran = Country(name='Iran', code='ir', phone_prefix=98)
    tehran_state = State(name='Tehran', country=iran)
    tehran_city = City(name='Tehran', state=tehran_state)

    DBSession.add(tehran_city)
    DBSession.flush()

    # Members
    admin1 = Admin()
    admin1.email = 'admin1@test.com'
    admin1.password = '123456'
    admin1.is_active = True
    DBSession.add(admin1)

    client1 = Client()
    client1.email = 'client1@test.com'
    client1.password = '123456'
    client1.is_active = True
    DBSession.add(client1)

    client2 = Client()
    client2.email = 'client2@test.com'
    client2.password = '123456'
    client2.is_active = True
    client2.is_email_verified = True
    DBSession.add(client2)

    client3 = Client()
    client3.email = 'client3@test.com'
    client3.password = '123456'
    client3.is_active = True
    client3.is_email_verified = True
    client3.is_evidence_verified = True
    client3.evidence.first_name = 'FirstName3'
    client3.evidence.last_name = 'LastName3'
    client3.evidence.mobile_phone = '+111111111'
    client3.evidence.fixed_phone = '+222222222'
    client3.evidence.birthday = '2020-10-21'
    client3.evidence.address = 'Address3 - address3 - address3'
    client3.evidence.gender = 'male'
    client3.evidence.city = tehran_city
    client3.evidence.id_card = join(STUFF_DIR, 'test-image-1.jpg')
    client3.evidence.id_card_secondary = join(STUFF_DIR, 'test-image-2.png')
    DBSession.add(client3)

    DBSession.flush()

    # Markets
    tirr = Fiat(symbol='TIRR', name='Iran Rial', divide_by_ten=-8)
    tbtc = Cryptocurrency(symbol='TBTC', name='Bitcoin', wallet_id=1)
    teth = Cryptocurrency(symbol='TETH', name='Ethereum', wallet_id=1, divide_by_ten=-1)

    tirr_tbtc = Market(name='TIRR_TBTC', base_currency=tbtc, quote_currency=tirr)
    tirr_teth = Market(name='TIRR_TETH', base_currency=teth, quote_currency=tirr)
    tbtc_teth = Market(name='TBTC_TETH', base_currency=teth, quote_currency=tbtc)

    DBSession.add(tirr_tbtc)
    DBSession.add(tirr_teth)
    DBSession.add(tbtc_teth)

    DBSession.flush()

    # Funds
    # DBSession.add(Fund(client=client1, currency=btc, total_balance=0, blocked_balance=0))
    # DBSession.add(Fund(client=client2, currency=btc, total_balance=34700000, blocked_balance=14660000))
    # DBSession.add(Fund(client=client3, currency=btc, total_balance=10000000000, blocked_balance=0))
    # DBSession.add(Fund(client=client1, currency=irr, total_balance=0, blocked_balance=0))
    # DBSession.add(Fund(client=client2, currency=irr, total_balance=56000000, blocked_balance=158000))
    # DBSession.add(Fund(client=client3, currency=irr, total_balance=9872000000, blocked_balance=150578))

    DBSession.flush()
