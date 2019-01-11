from sqlalchemy.orm import scoped_session

import stemerald
from stemerald.models import Client, Cryptocurrency
from stemerald.models.fund import Fund
from restfulpy.db import DatabaseManager
from restfulpy.orm import DBSession, session_factory, setup_schema, create_engine

app = stemerald.stemerald
app.configure()
# app.initialize_models()

with DatabaseManager() as m:
    m.drop_database()
    m.create_database()

engine = create_engine()
session = session_factory(bind=engine, expire_on_commit=True)
setup_schema(session)
session.commit()
session.close()

session0 = session_factory(bind=engine, expire_on_commit=True)

client1 = Client()
client1.email = 'practice1@test.com'
client1.password = '123456'
client1.is_active = True
session0.add(client1)

fund1 = Fund(
    currency=Cryptocurrency(name='a', code='b'),
    client=client1
)

fund2 = Fund(
    currency=Cryptocurrency(name='c', code='d'),
    client=client1
)

session0.add(fund1)
session0.add(fund2)
session0.commit()

print(fund1)
print(fund2)

session1 = session_factory(bind=engine, expire_on_commit=True)
session2 = session_factory(bind=engine, expire_on_commit=True)

f1 = session1.query(Fund).filter(Fund.currency_code == 'b').with_for_update().one()
print('salam1111')

f1.total_balance += 199
# session1.commit()


f2 = session2.query(Fund).filter(Fund.currency_code == 'b').with_for_update().one()
print('salam2222')

# f1.total_balance += 199
f2.total_balance += 299

print('salam3333')

session2.commit()
print('salam4444')

session1.commit()
print('salam5555')

print(session_factory(bind=engine, expire_on_commit=True).query(Fund.total_balance, Fund.blocked_balance).filter(
    Fund.currency_code == 'b').one())
print(session_factory(bind=engine, expire_on_commit=True).query(Fund.total_balance, Fund.blocked_balance).filter(
    Fund.currency_code == 'd').one())
