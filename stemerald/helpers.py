class ObjectAlreadyInitializedError(Exception):
    pass


class ObjectNotInitializedError(Exception):
    pass


class ObjectProxy(object):
    """
    A simple object proxy to let deferred object's initialize later (for example: just after import):
    This class encapsulates some tricky codes to resolve the proxied object members using the
    `__getattribute__` and '__getattr__'. SO TAKE CARE about modifying the code, to prevent
    infinite loops and stack-overflow situations.

    Module: fancy_module

        deferred_object = None  # Will be initialized later.
        def init():
            global deferred_object
            deferred_object = AnyValue()
        proxy = ObjectProxy(lambda: deferred_object)

    In another module:

        from fancy_module import proxy, init
        def my_very_own_function():
            try:
                return proxy.any_attr_or_method()
            except: ObjectNotInitializedError:
                init()
                return my_very_own_function()

    """

    def __init__(self, resolver):
        object.__setattr__(self, '_resolver', resolver)

    @property
    def proxied_object(self):
        o = object.__getattribute__(self, '_resolver')()
        # if still is none, raise the exception
        if o is None:
            raise ObjectNotInitializedError("Client is not initialized yet.")
        return o

    def __getattr__(self, key):
        if key.startswith('_'):  # Exclude protected and private methods
            return self.__dict__[key]
        return getattr(object.__getattribute__(self, 'proxied_object'), key)

    def __setattr__(self, key, value):
        if key.startswith('_'):  # Exclude protected and private methods
            self.__dict__[key] = value
            return
        setattr(object.__getattribute__(self, 'proxied_object'), key, value)


class DeferredObject(ObjectProxy):
    _instance = None

    def __init__(self, backend_factory):
        super(DeferredObject, self).__init__(
            self._get_instance
        )
        self._backend_factory = backend_factory

    def _get_instance(self):
        return self._instance

    def _set_instance(self, v):
        self._instance = v

    def initialize(self, force=False, **kw):
        instance = self._get_instance()
        if not force and instance is not None:
            raise ObjectAlreadyInitializedError("Object is already initialized.")

        self._set_instance(self._backend_factory(**kw))
