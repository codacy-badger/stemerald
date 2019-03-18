"""
    PerfectMoney class usage example
"""
from stemerald.perfectmoney import PerfectMoney


def print_history(account, password, startmonth, startday, startyear, endmonth, endday, endyear):
    pm = PerfectMoney(account, password)
    res = pm.history(startmonth, startday, startyear, endmonth, endday, endyear)
    if pm.error:
        print(pm.error)
        return
    print(res)


def print_ev(account, password):
    pm = PerfectMoney(account, password)
    res = pm.evcsv()
    if pm.error:
        print(pm.error)
        return
    print(res)


def get_balance(account, password):
    pm = PerfectMoney(account, password)
    res = pm.balance()
    if pm.error:
        print(pm.error)
        return
    print(res)


def create_ev(account, password, payer, amount):
    pm = PerfectMoney(account, password)
    res = pm.ev_create(payer, amount)
    if pm.error:
        print(pm.error)
        return
    print(res)


def transfer_money(account, password, payer, payee, amount, memo, payment_id):
    pm = PerfectMoney(account, password)
    res = pm.transfer(payer, payee, amount, memo, payment_id)
    if pm.error:
        print(pm.error)
        return
    print(res)


def main():
    account = '12345'
    password = 'password'
    payer = 'U123232'

    get_balance(account, password)


#    create_ev(account, password, payer, 0.05)
#    print_ev(account, password)
#    print_history(account, password, 6, 1, 2009, 6, 27, 2009)
#    transfer_money(account, password, payer, 'U123123', 0.01, 'test', 123)

if __name__ == '__main__':
    exit(main())
