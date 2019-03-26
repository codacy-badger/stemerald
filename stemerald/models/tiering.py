class Tier:
    id = 0
    title = "tier0"

    asset_policies = []

    trading_policies = []


class TierAssetPolicy:
    tier_id = 0

    currency = None

    can_deposit = True

    can_withdraw = True

    deposit_min = None
    deposit_max = None

    withdraw_min = None
    withdraw_max = None

    deposit_fee_min = None
    deposit_fee_rate = None
    deposit_fee_max = None

    withdraw_fee_min = None
    withdraw_fee_rate = None
    withdraw_fee_max = None

    updated_at = None


class TierCryptoAssetPolicy(TierAssetPolicy):
    network = None  # TODO: Unique constraint with currency
    requires_confirmations = None


class TierFiatAssetPolicy(TierAssetPolicy):
    gateway = None  # TODO: Unique constraint with currency
    countries = None  # TODO: Unique constraint with currency


class TierTradingPolicy:
    tier_id = 0

    market = None

    can_buy_limit_order = True
    can_buy_market_order = True
    can_buy_stoploss_order = True

    can_sell_limit_order = True
    can_sell_market_order = True
    can_sell_stoploss_order = True

    buy_limit_order_min = None
    buy_limit_order_max = None
    buy_market_order_min = None
    buy_market_order_max = None
    buy_stoploss_order_min = None
    buy_stoploss_order_max = None

    sell_limit_order_min = None
    sell_limit_order_max = None
    sell_market_order_min = None
    sell_market_order_max = None
    sell_stoploss_order_min = None
    sell_stoploss_order_max = None

    buy_taker_fee_base = None
    buy_taker_fee_rate = None
    buy_taker_fee_max = None

    buy_maker_fee_base = None
    buy_maker_fee_rate = None
    buy_maker_fee_max = None

    sell_taker_fee_min = None
    sell_taker_fee_rate = None
    sell_taker_fee_max = None

    sell_maker_fee_min = None
    sell_maker_fee_rate = None
    sell_maker_fee_max = None
