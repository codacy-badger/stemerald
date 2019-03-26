from decimal import Decimal

from restfulpy.orm import DBSession
from sqlalchemy_media import store_manager

from stemerald.models import *


# FIXME: It is not base-data, this is mock-data. Fix it!

# noinspection PyArgumentList
@store_manager(DBSession)
def insert():  # pragma: no cover

    # Currencies
    tirr = Fiat(
        symbol='TIRR',
        name='Iran Rial',
        normalization_scale=-8,
        smallest_unit_scale=0
    )

    tbtc = Cryptocurrency(
        symbol='TBTC',
        name='Bitcoin',
        wallet_id="TBTC",
        normalization_scale=0,
        smallest_unit_scale=-8
    )

    teth = Cryptocurrency(
        symbol='TETH',
        name='Ethereum',
        wallet_id="TETH",
        normalization_scale=-1,
        smallest_unit_scale=-18
    )

    ttry = Fiat(
        symbol='TTRY',
        name='Turkish Lita',
        normalization_scale=-4,
        smallest_unit_scale=-2
    )

    # Markets
    tirr_tbtc = Market(name='TIRR_TBTC', base_currency=tbtc, quote_currency=tirr)
    tirr_teth = Market(name='TIRR_TETH', base_currency=teth, quote_currency=tirr)
    tbtc_teth = Market(name='TBTC_TETH', base_currency=teth, quote_currency=tbtc)
    ttry_tbtc = Market(name='TTRY_TBTC', base_currency=tbtc, quote_currency=ttry)
    DBSession.add(tirr_tbtc)
    DBSession.add(tirr_teth)
    DBSession.add(tbtc_teth)
    DBSession.add(ttry_tbtc)

    # Territories
    iran = Country(name='Iran', code='ir', phone_prefix=98)
    tehran_state = State(name='Tehran', country=iran)
    tehran_city = City(name='Tehran', state=tehran_state)
    turkey = Country(name='Turkey', code='tr', phone_prefix=90)
    ankara_state = State(name='Ankara', country=turkey)
    istanbul_state = State(name='Istanbul', country=turkey)
    istanbul_avrupa_city = City(name='Istanbul (Avrupa)', state=istanbul_state)
    istanbul_asia_city = City(name='Istanbul (Asia)', state=istanbul_state)
    ankara_city = City(name='Tehran', state=ankara_state)
    DBSession.add(tehran_city)
    DBSession.add(istanbul_avrupa_city)
    DBSession.add(istanbul_asia_city)
    DBSession.add(ankara_city)
    DBSession.flush()

    # Payment Gateways
    shaparak = PaymentGateway()
    shaparak.name = "tshaparak"
    shaparak.fiat_symbol = "TIRR"
    # shaparak.cashin_min = Decimal('10000'),
    # shaparak.cashin_max = Decimal('0'),
    # shaparak.cashin_static_commission = Decimal('0'),
    # shaparak.cashin_commission_rate = '0.0',
    # shaparak.cashin_max_commission = Decimal('0'),
    DBSession.add(shaparak)
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
    DBSession.flush()

    # Ticketing Departments
    verification_department = TicketDepartment()
    verification_department.title = 'Verification'
    DBSession.add(verification_department)
    financial_department = TicketDepartment()
    financial_department.title = 'Financial'
    DBSession.add(financial_department)
    technical_department = TicketDepartment()
    technical_department.title = 'Technical'
    DBSession.add(technical_department)
    general_department = TicketDepartment()
    general_department.title = 'General'
    DBSession.add(general_department)
    DBSession.flush()

    # 1. Currencies
    # Fiat
    # irr = Fiat(code='IRR', name='Iran Rial')
    # usd = Currency(code='usd', name='USA Dollar', type='fiat')
    # eur = Currency(code='eur', name='Euro', type='fiat')
    # rur = Currency(code='rur', name='Russian Ruble', type='fiat')

    # Cryptocurrency
    # btc = Cryptocurrency(code='BTC', name='Bitcoin')
    # ltc = Cryptocurrency(code='ltc', name='Litecoin', type='crypto')
    # nmc = Cryptocurrency(code='nmc', name='Namecoin', type='crypto')
    # nvc = Cryptocurrency(code='nvc', name='Novacoin', type='crypto')
    # ppc = Cryptocurrency(code='ppc', name='Peercoin', type='crypto')
    # dsh = Cryptocurrency(code='dsh', name='Dashcoin', type='crypto')
    # eth = Cryptocurrency(code='eth', name='Ethereum', type='crypto')
    # bch = Cryptocurrency(code='bch', name='Bitcoin Cash', type='crypto')
    # zec = Cryptocurrency(code='zec', name='Zcash', type='crypto')

    # # E-Money
    # wm = Currency(code='wm', name='Web Money', type='emoney')
    # pm = Currency(code='pm', name='Perfect Money', type='emoney')

    # for currency in [irr, usd, eur, rur, btc, ltc, nmc, nvc, ppc, dsh, eth, bch, zec, wm, pm]:
    #     DBSession.add(currency)

    # DBSession.add(irr)
    # DBSession.add(btc)

    # 2. Markets
    # btc_irr = Market(base_currency=btc, quote_currency=irr, price_latest=10000)
    # btc_usd = Market(base_currency=btc, quote_currency=usd, min_trading_size=10)
    # btc_rur = Market(base_currency=btc, quote_currency=rur, min_trading_size=10)
    # btc_eur = Market(base_currency=btc, quote_currency=eur, min_trading_size=10)
    # ltc_btc = Market(base_currency=ltc, quote_currency=btc, min_trading_size=10)
    # ltc_usd = Market(base_currency=ltc, quote_currency=usd, min_trading_size=10)
    # ltc_rur = Market(base_currency=ltc, quote_currency=rur, min_trading_size=10)
    # ltc_eur = Market(base_currency=ltc, quote_currency=eur, min_trading_size=10)
    # nmc_btc = Market(base_currency=nmc, quote_currency=btc, min_trading_size=10)
    # nmc_usd = Market(base_currency=nmc, quote_currency=usd, min_trading_size=10)
    # nvc_btc = Market(base_currency=nvc, quote_currency=btc, min_trading_size=10)
    # nvc_usd = Market(base_currency=nvc, quote_currency=usd, min_trading_size=10)
    # usd_rur = Market(base_currency=usd, quote_currency=rur, min_trading_size=10)
    # eur_usd = Market(base_currency=eur, quote_currency=usd, min_trading_size=10)
    # eur_rur = Market(base_currency=eur, quote_currency=rur, min_trading_size=10)
    # ppc_btc = Market(base_currency=ppc, quote_currency=btc, min_trading_size=10)
    # ppc_usd = Market(base_currency=ppc, quote_currency=usd, min_trading_size=10)
    # dsh_btc = Market(base_currency=dsh, quote_currency=btc, min_trading_size=10)
    # dsh_usd = Market(base_currency=dsh, quote_currency=usd, min_trading_size=10)
    # dsh_rur = Market(base_currency=dsh, quote_currency=rur, min_trading_size=10)
    # dsh_eur = Market(base_currency=dsh, quote_currency=eur, min_trading_size=10)
    # dsh_ltc = Market(base_currency=dsh, quote_currency=ltc, min_trading_size=10)
    # dsh_eth = Market(base_currency=dsh, quote_currency=eth, min_trading_size=10)
    # eth_btc = Market(base_currency=eth, quote_currency=btc, min_trading_size=10)
    # eth_usd = Market(base_currency=eth, quote_currency=usd, min_trading_size=10)
    # eth_eur = Market(base_currency=eth, quote_currency=eur, min_trading_size=10)
    # eth_ltc = Market(base_currency=eth, quote_currency=ltc, min_trading_size=10)
    # eth_rur = Market(base_currency=eth, quote_currency=rur, min_trading_size=10)
    # bch_usd = Market(base_currency=bch, quote_currency=usd, min_trading_size=10)
    # bch_btc = Market(base_currency=bch, quote_currency=btc, min_trading_size=10)
    # bch_rur = Market(base_currency=bch, quote_currency=rur, min_trading_size=10)
    # bch_eur = Market(base_currency=bch, quote_currency=eur, min_trading_size=10)
    # bch_ltc = Market(base_currency=bch, quote_currency=ltc, min_trading_size=10)
    # bch_eth = Market(base_currency=bch, quote_currency=eth, min_trading_size=10)
    # bch_dsh = Market(base_currency=bch, quote_currency=dsh, min_trading_size=10)
    # zec_btc = Market(base_currency=zec, quote_currency=btc, min_trading_size=10)
    # zec_usd = Market(base_currency=usd, quote_currency=usd, min_trading_size=10)

    # for currency in [btc_usd, btc_rur, btc_eur, ltc_btc, ltc_usd, ltc_rur, ltc_eur, nmc_btc, nmc_usd, nvc_btc,
    #  nvc_usd, usd_rur, eur_usd, eur_rur, ppc_btc, ppc_usd, dsh_btc, dsh_usd, dsh_rur, dsh_eur, dsh_ltc,
    #  dsh_eth, eth_btc, eth_usd, eth_eur, eth_ltc, eth_rur, bch_usd, bch_btc, bch_rur, bch_eur, bch_ltc,
    #  bch_eth, bch_dsh, zec_btc, zec_usd]:
    #     DBSession.add(currency)

    # DBSession.add(btc_irr)
