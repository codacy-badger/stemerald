import time
from decimal import getcontext, Decimal

from nanohttp import settings
from restfulpy.logging_ import get_logger
from restfulpy.orm import session_factory

from stemerald import stawallet_client, stexchange_client
from stemerald.controllers.wallet import deposit_to_dict
from stemerald.models import Cryptocurrency, Notification
from stemerald.stexchange import RepeatUpdateException

logger = get_logger('looper')


def stawallet_sync_looper():
    isolated_session = session_factory(expire_on_commit=False)
    context = {'counter': 0}

    while True:

        logger.info("Trying to sync wallet, Counter: %s" % context['counter'])
        cryptocurrencies = isolated_session.query(Cryptocurrency).all()
        for cryptocurrency in cryptocurrencies:
            # Get latest synced deposit update time
            try:

                page = 0

                while True:
                    new_sync_time = int(time.time())
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
                        change_amount_normalized = cryptocurrency.smallest_unit_to_normalized(deposit['netAmount'])
                        change_amount_output = cryptocurrency.smallest_unit_to_output(deposit['netAmount'])
                        deposit = deposit_to_dict(cryptocurrency, deposit)

                        # TODO: Check the range
                        # TODO: Calculate the commission
                        # TODO: Check the purpose (e.g. be 'deposit', not 'charge')

                        if deposit['user'] is None:
                            # FIXME: Unknown (or 'charge')
                            # TODO: Inform and handle
                            pass
                        else:

                            try:

                                getcontext().prec = 8
                                if deposit['isConfirmed'] is True and deposit['error'] is None:
                                    # TODO: Check whether the user is admin (charge) or user (deposit)?
                                    wallet_update_respones = stexchange_client.balance_update(
                                        user_id=int(deposit['user']),
                                        asset=cryptocurrency.wallet_id,
                                        business='deposit',  # TODO: Are you sure?
                                        business_id=int(deposit['id']),  # TODO: Are you sure?
                                        change=change_amount_normalized,
                                        # TODO: Make sure is greater than 0
                                        detail={}  # TODO
                                    )

                                # TODO: Notify the user
                                notification = Notification()
                                notification.member_id = int(deposit['user'])

                                if deposit['isConfirmed'] is True:
                                    notification.title = 'Your balance has been increased'
                                    notification.description = f'Your new deposit has just completely confirmed. ' \
                                        f'You balance has been increased ' \
                                        f'{change_amount_output} {cryptocurrency.wallet_id} '

                                elif deposit['status'].lower() == 'orphan':
                                    notification.title = 'New deposit discovered'
                                    notification.description = f'Your new deposit has just been found. ' \
                                        f'Please be patient for your transaction to be mined and get ' \
                                        f'{deposit["confirmationsLeft"]} more confirmations '

                                else:
                                    notification.title = 'New deposit in the way'
                                    notification.description = f'Your new deposit has just got it\'s first ' \
                                        f'confirmation. You will have full access to it as soon as it receives ' \
                                        f'{deposit["confirmationsLeft"]} more confirmations '

                                isolated_session.add(notification)

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
                try:
                    isolated_session.rollback()
                except:
                    logger.exception(f'Error rolling back the iteration\'s session.')

        context['counter'] += 1
        time.sleep(settings.stawallet.sync_gap)
