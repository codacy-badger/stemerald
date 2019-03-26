from _decimal import ROUND_HALF_EVEN
from decimal import getcontext, Decimal

SUPPORTING_PREC = 28
SHOWING_PREC = 8

getcontext().prec = SUPPORTING_PREC
getcontext().rounding = ROUND_HALF_EVEN


def parse_lowest_unit(number: str, smallest_unit_scale: int, normalization_scale: int):
    """

    For exp. for 'BTC' we'll use:
    smallest_unit_scale = -8
    normalization_scale = 0

    For exp. for 'ETH' we'll use:
    smallest_unit_scale = -18
    normalization_scale = -1

    For exp. for 'IRR' we'll use:
    smallest_unit_scale = 0
    normalization_scale = -8

    :param number:
    :param smallest_unit_scale:
    :param normalization_scale:
    :return:
    """
    return Decimal(number).scaleb(smallest_unit_scale + normalization_scale)


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
