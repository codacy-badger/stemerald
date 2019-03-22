from firebase_admin import App
from nanohttp import settings

from stemerald.helpers import DeferredObject


def init_firebase():
    import firebase_admin
    from firebase_admin import credentials

    cred = credentials.Certificate(settings.firebase.service_account_key)
    return firebase_admin.initialize_app(cred)


firebase_client: App = DeferredObject(App)
