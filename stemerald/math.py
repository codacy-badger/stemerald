from _decimal import ROUND_HALF_EVEN
from decimal import getcontext, Decimal

SUPPORTING_PREC = 18
SHOWING_PREC = 8

getcontext().prec = SUPPORTING_PREC
getcontext().rounding = ROUND_HALF_EVEN


def parse_lowest_unit(number: str, lowest_unit_ten_pow: int, normalizing_ten_pow: int):
    """

    For exp. for 'BTC' we'll use:
    lowest_unit_ten_pow = -8
    normalizing_ten_pow = 0

    For exp. for 'ETH' we'll use:
    lowest_unit_ten_pow = -18
    normalizing_ten_pow = -1

    For exp. for 'IRR' we'll use:
    lowest_unit_ten_pow = 0
    normalizing_ten_pow = -8

    :param lowest_unit_pre:
    :param normalizing_divide_by_ten:
    :return:
    """
    return Decimal(number).scaleb(lowest_unit_ten_pow + normalizing_ten_pow)


def format_dec(decimal):
    if decimal is None:
        return None
    if not isinstance(decimal, Decimal):
        raise ValueError('Just Decimals are accepted')
    return ('{:.' + str(SHOWING_PREC) + 'f}').format(decimal)


def format_number_to_pretty(number):
    if number is None:
        return None
    if isinstance(number, (float, int)):
        number = str(number)
    if not isinstance(number, str):
        raise ValueError('Just strings are accepted')
    return format_dec(Decimal(number))
