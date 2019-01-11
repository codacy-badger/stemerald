import os

import itertools
from nanohttp import context
from restfulpy.logging_ import get_logger

from stemerald import stemerald

stemerald.configure(files=os.environ.get('STSTEMERALD_CONFIG_FILE'))
stemerald.initialize_models()


def cross_origin_helper_app(environ, start_response):
    def better_start_response(status, headers):
        headers.append(('Access-Control-Allow-Origin', os.environ.get('STEMERALD_TRUSTED_HOSTS', '*')))
        start_response(status, headers)

    return stemerald(environ, better_start_response)


class LoggingMiddleware:
    def __init__(self, application):
        self.__application = application
        self.logger = get_logger('middleware')

    def __call__(self, environ, start_response):
        def _start_response(status, headers, *args):
            _result = start_response(status, headers, *args)
            self.logger.debug('REQUEST: %s FORM: %s', context.environ, context.form)
            self.logger.debug('RESPONSE STATUS: %s HEADERS: %s', status, headers)
            return _result

        raw_result = self.__application(environ, _start_response)
        result, result_to_log = itertools.tee(raw_result)
        self.logger.debug('RESPONSE BODY: %s', ''.join([c.decode() for c in result_to_log]))
        return result


# app = LoggingMiddleware(cross_origin_wildcard_helper_app)
app = LoggingMiddleware(stemerald)
