import time

import binascii
from base64 import b32encode

import oath
from Crypto.Hash import SHA256
from nanohttp.configuration import settings


class Oath:
    def __init__(self, seed, derivate_seed_from=None):
        self.seed = seed
        self.window = settings.oath.window
        self.ocra_suite = settings.oath.ocra_suite
        self.time_interval = settings.oath.time_interval  # FIXME: Extract from ocra suite
        self.drift = 0

        if derivate_seed_from:
            self.seed = self._derivate_seed(self.seed, derivate_seed_from)

    def generate(self, challenge):
        ocra_client = oath.OCRAChallengeResponseClient(
            binascii.unhexlify(self.seed),
            self.ocra_suite,
            self.ocra_suite
        )

        kwargs = {'T': time.time(), 'T_precomputed': ''}
        rc = ocra_client.compute_response(challenge=challenge, **kwargs)

        return rc

    def verify(self, challenge, code):
        for i in range(max(-divmod(time.time(), self.time_interval)[0], -self.window),
                       self.window + 1):
            d = (self.drift + i) * self.time_interval
            ocra_server = oath.OCRAChallengeResponseServer(
                binascii.unhexlify(self.seed),
                self.ocra_suite,
                self.ocra_suite
            )
            kwargs = {'T': time.time() + d, 'T_precomputed': ''}
            ocra_server.compute_challenge()
            ocra_server.challenge = challenge
            if ocra_server.verify_response(response=code, **kwargs):
                return True, self.drift + i

        return False, 0

    def verify_google_auth(self, code):
        # FIXME: Read from google auth configurations (and make configuration for google auth!)
        is_valid, drift = oath.accept_totp(
            key=self.seed,
            response=code,
            period=30,
            format='dec6',
            hash='SHA1',
            drift=0,
            backward_drift=3,
            forward_drift=3
        )
        return is_valid, drift

    @staticmethod
    def _derivate_seed(base_seed, second_factor):
        sha = SHA256.new()
        sha.update(second_factor.encode())
        hashed = sha.digest()
        result = bytearray(binascii.unhexlify(base_seed))
        for i, b in enumerate(hashed):
            result[i] ^= b
        return binascii.hexlify(bytes(result)).decode()

    # FIXME: Fix this piece of shit
    def get_google_auth_uri(self, account_name, issuer='Stacrypt'):
        encoded_seed = b32encode(binascii.unhexlify(self.seed)).decode().replace('=', '')
        # FIXME: Get algo and ... from ocra suite
        return f'otpauth://totp/Stacrypt:{account_name}' \
               f'?secret={encoded_seed}' \
               f'&issuer={issuer}'
