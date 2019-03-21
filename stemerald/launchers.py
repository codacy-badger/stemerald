import signal
import sys
import threading

from restfulpy import Launcher


class WalletSyncLauncher(Launcher):  # pragma: no cover

    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser('syncwallet', help='Start wallet sync looper')
        return parser

    def launch(self):
        from stemerald.loopers import stawallet_sync_looper

        signal.signal(signal.SIGINT, self.kill_signal_handler)
        signal.signal(signal.SIGTERM, self.kill_signal_handler)

        t = threading.Thread(
            target=stawallet_sync_looper,
            name='stawallet-sync-looper',
            daemon=True,
            kwargs=dict()
        )
        t.start()

        print(f'Stawallet sync looper started!')
        print('Press Ctrl+C to terminate looper')
        signal.pause()

    # noinspection PyUnusedLocal
    @staticmethod
    def kill_signal_handler(signal_number, frame):

        if signal_number == signal.SIGINT:
            print('You pressed Ctrl+C!')
        elif signal_number in (signal.SIGTERM, signal.SIGKILL):
            print('OS Killed Me!')

        sys.stdin.close()
        sys.stderr.close()
        sys.stdout.close()
        sys.exit(1)
