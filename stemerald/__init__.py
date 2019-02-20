from os.path import join, dirname

import functools
from nanohttp import settings, context
from restfulpy.application import Application as BaseApplication
from restfulpy.orm import DBSession
from sqlalchemy_media import StoreManager, FileSystemStore

from stemerald import basedata, mockups
from stemerald.mockups import mockup
from stemerald.authentication import Authenticator
from stemerald.controllers.root import Root
from stemerald.stexchange import stexchange_client

__version__ = '2.0.1'


class Application(BaseApplication):
    __authenticator__ = Authenticator()
    builtin_configuration = """
    
    db:
      url: postgresql://postgres:postgres@localhost/stemerald_dev
      test_url: postgresql://postgres:postgres@localhost/stemerald_test
      administrative_url: postgresql://postgres:postgres@localhost/postgres
    
    redis:
      host: localhost
      port: 6379
      password: ~
      db: 0
    
    media_storage:
      file_system_dir: %(root_path)s/data/media-storage
      base_url: http://localhost:8081/media
      
    messaging:
      default_sender: Stemerald
      template_dirs:
        - %(root_path)s/stemerald/templates
        
    reset_password:
      secret: email-verification-secret
      max_age: 3600  # seconds
      url: https://stacrypt.io/reset_password
        
    email_verification:
      secret: email-verification-secret
      max_age: 3600  # seconds
      url: https://stacrypt.io/email_verification
      
    shaparak:
      provider: stemerald.shaparak.PayIrProvider
      
      pay_ir:
        api_key: 2bf8727eb3772b28ce4a0707bf4ee456
        gateway_url: https://pay.ir/payment/gateway/{transactionId}
        post_redirect_url: https://stacrypt.io/apiv2/transactions/shaparak-ins/pay-irs
        result_redirect_url: https://stacrypt.io/payment_redirect

    sms:
      provider: stemerald.sms.KavenegarSmsProvider

      kavenegar:
        verification_code_url: https://api.kavenegar.com/v1/3277760553034736E260553055303470553034736E2356413D3D/verify/lookup.json
        
    oath:
      window: 3
      ocra_suite: OCRA-1:HOTP-SHA256-6:QA40-T1M
      time_interval: 60 # Seconds 
    
    mobile_phone_verification:
      template: mobile
      seed: B35F868F5F868F59A3D9F98B68F56AAA215F868F59A39F98B215F868F59A39F9
    
    fixed_phone_verification:
      template: fixed
      seed: 68F59A3D9F98B68FF98B68F56AAA2A28B68F56AAA268F59A3D9F98B68F56AAA2

    trader:
      price_threshold_permille: 50
      gap: 3 # Seconds

    watcher:
      gap: 30
      retry_limit: 5
      sleep_between_retries: 1
      
    membership:
      invitation_code_required: false
      second_factor_seed: A3D9F98B8FF98B68F56AAA2A28B68F56AAA268F593D9F98B68FF98B68F56AAA2
      
    cdn: 
      # remote_address_key: REMOTE_ADDR
      remote_address_key: HTTP_CF_CONNECTING_IP

    stexchange: 
      rpc_url: "http://localhost:8080"

    stawallet: 
      rest_url: "http://localhost:8080"

    """

    def __init__(self):
        super().__init__(
            'stemerald',
            root=Root(),
            root_path=join(dirname(__file__), '..'),
            version=__version__,
        )

    # noinspection PyArgumentList
    def insert_basedata(self):
        basedata.insert()
        DBSession.commit()

    # noinspection PyArgumentList
    def insert_mockup(self):
        mockup.insert()
        DBSession.commit()

    def begin_response(self):
        if settings.debug:
            context.response_headers.add_header(
                'Access-Control-Allow-Methods',
                'GET, POST, METADATA, ADD, REMOVE, CLAIM, REGISTER, ACTIVATE, DEACTIVATE, SCHEDULE, VERIFY, TERMINATE'
                ', SUBMIT, ACCEPT, REJECT, CHANGE, RESET, EDIT, CREATE, APPEND, CLOSE, PRESENT, SHOW, RENEW, CHECK'
                ', MAKE, SIGN, PUSH, ENABLE, DISABLE, PROVISION, CALCULATE, CANCEL, LIST, SUMMARY, STATUS, LAST'
                ', OVERVIEW, PEEK')
            context.response_headers.add_header(
                'Access-Control-Allow-Headers',
                'Content-Type, Authorization, Content-Length, Connection, If-Match, If-None-Match'
            )
            context.response_headers.add_header(
                'Access-Control-Expose-Headers',
                'Content-Type, Content-Length, X-Pagination-Count, X-Pagination-Skip, X-Pagination-Take, '
                'X-New-JWT-Token, ETag, X-Reason'
            )
            context.response_headers.add_header('Access-Control-Allow-Credentials', 'true')
            # context.response_headers.add_header('Access-Control-Allow-Origin', 'http://localhost:3000')

    def configure(self, files=None, context=None, **kwargs):
        super().configure(files, context, **kwargs)
        stexchange_client.initialize(server_url=settings.stexchange.rpc_url, force=True)

    def initialize_models(self, session=None):
        StoreManager.register(
            'fs',
            functools.partial(
                FileSystemStore,
                settings.media_storage.file_system_dir,
                base_url=settings.media_storage.base_url
            ),
            default=True
        )
        super().initialize_models(session=session)


stemerald = Application()
