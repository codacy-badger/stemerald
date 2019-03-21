import time
from datetime import datetime

from nanohttp import settings
from restfulpy.logging_ import get_logger
from restfulpy.orm import session_factory

from stemerald import stawallet_client, stexchange_client
from stemerald.controllers.wallet import deposit_to_dict
from stemerald.models import Cryptocurrency
from stemerald.stexchange import RepeatUpdateException

logger = get_logger('looper')


def stawallet_sync_looper():
    isolated_session = session_factory(expire_on_commit=False)
    context = {'counter': 0}

    while True:

        logger.info("Trying to sync wallet, Counter: %s" % context['counter'])
        cryptocurrencies = Cryptocurrency.query.all()
        for cryptocurrency in cryptocurrencies:
            # Get latest synced deposit update time
            try:

                page = 0

                while True:
                    new_sync_time = datetime.now()
                    new_deposits = stawallet_client.get_deposits(
                        wallet_id=cryptocurrency.wallet_id,
                        user_id="*",
                        asc=True,
                        after=cryptocurrency.wallet_latest_sync,
                        page=page
                    )
                    if len(new_deposits) == 0:
                        break

                    for deposit in new_deposits:
                        # Try to update the stexchange
                        deposit = deposit_to_dict(deposit)

                        # TODO: Check the range
                        # TODO: Calculate the commission
                        # TODO: Check the purpose (e.g. be 'deposit', not 'charge')

                        if deposit['user'] is None:
                            # FIXME: Unknown (or 'charge')
                            # TODO: Inform and handle
                            pass
                        else:

                            try:

                                if deposit['isConfirmed'] is True and deposit['error'] is None:
                                    # TODO: Check whether the user is admin (charge) or user (deposit)?
                                    wallet_update_respones = stexchange_client.balance_update(
                                        user_id=deposit['user'],
                                        asset=cryptocurrency.wallet_id,
                                        business='deposit',  # TODO: Are you sure?
                                        business_id=deposit['id'],  # TODO: Are you sure?
                                        change=deposit['netAmount'],  # TODO: Make sure is greater than 0
                                        detail=''  # TODO
                                    )
                                else:
                                    # TODO: Notify the user
                                    pass

                            except RepeatUpdateException as e:
                                # TODO: Log
                                pass

                    # Next page:
                    page += 1

                cryptocurrency.wallet_latest_sync = new_sync_time
                isolated_session.commit()

                logger.exception(f'Wallet {cryptocurrency.wallet_id} synced successfully.')
            except:
                logger.exception(f'Error syncing {cryptocurrency.wallet_id} wallet.')

        context['counter'] += 1
        time.sleep(settings.stawallet.sync_gap)
