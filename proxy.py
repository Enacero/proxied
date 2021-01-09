from typing import Any, List, Callable, TypeVar, Generic, Optional, Set

__all__ = ("Proxy",)

T = TypeVar("T")


class _LazyCall:
    NULL_OBJECT = object()

    def __init__(self, fn: Callable[..., T]):
        self.fn = fn
        self.value = _LazyCall.NULL_OBJECT

    def __call__(self):
        if self.value is _LazyCall.NULL_OBJECT:
            self.value = self.fn()
        return self.value


def _error_func():
    """Function that is assigned by default, if no inner value
    or inner constructor supplied"""
    raise ValueError("There should be initialized constructor or obj.")


def _get_proxy_field(proxy: "Proxy[T]", name: str) -> Callable[..., T]:
    """Helper function to get proxy field"""
    return object.__getattribute__(proxy, name)


_CONSTRUCT_FIELD: str = "_value_provider"

_proxy_attrs: Set[str] = {
    "_set_provider",
    "_get_provider",
    _CONSTRUCT_FIELD,
}


class Proxy(Generic[T]):
    CONSTRUCT_FIELD = _CONSTRUCT_FIELD

    _magic_methods: Set[str] = {
        # Rich Comparisons
        "__gt__",
        "__ge__",
        "__lt__",
        "__le__",
        "__eq__",
        "__ne__",
        "__hash__",
        "__dir__",
        # Attribute Access
        "__setattr__",
        "__delattr__",
        "__getattr__",
        # Container operations
        "__len__",
        "__getitem__",
        "__setitem__",
        "__delitem__",
        "__missing__",
        "__iter__",
        "__reversed__",
        "__contains__",
        # Numeric operations
        # "__add__",
        "__sub__",
        "__mul__",
        "__matmul__",
        "__truediv__",
        "__floordiv__",
        "__mod__",
        "__divmod__",
        "__pow__",
        "__lshift__",
        "__rshift__",
        "__and__",
        "__xor__",
        "__or__",
        # Reflected numeric operations
        "__radd__",
        "__rsub__",
        "__rmul__",
        "__rmatmul__",
        "__rtruediv__",
        "__rfloorfiv__",
        "__rmod__",
        "__rdivmod__",
        "__rpow__",
        "__rlshift__",
        "__rrshift__",
        "__rand__",
        "__rxor__",
        "__ror__",
        # Augmented numeric operations
        "__iadd__",
        "__isub__",
        "__imul__",
        "__imatmul__",
        "__itruediv__",
        "__ifloordiv__",
        "__imod__",
        "__idivmod__",
        "__ipow__",
        "__ilshift__",
        "__irshift__",
        "__iand__",
        "__ixor__",
        "__ior__",
        # Unary numeric operations
        "__neg__",
        "__pos__",
        "__abs__",
        "__invert__",
        # To numeric types
        "__complex__",
        "__int__",
        "__float__",
        "__index__",
        # Built in math functions
        "__round__",
        "__trunc__",
        "__floor__",
        "__ceil__",
        # Context managers
        "__enter__",
        "__exit__",
        # To string representations
        "__str__",
        "__repr__",
        "__bytes__",
        "__call__",
    }

    def __init__(
        self,
        value: T = None,
        value_provider: Callable[[], Optional[T]] = None,
        cached=True,
    ):
        """
        Proxy class
        :param value: object that should be proxied
        :param value_provider: callable, that returns object that should be proxied
        :param cached: bool, set False if you wants to call value_provider
            every time on access to proxy
        """
        if value and value_provider:
            raise ValueError("There should be one of obj or constructor, not both.")

        def _wrapper() -> Optional[T]:
            return value

        if value:
            value_provider = _wrapper
        elif value_provider:
            value_provider = _LazyCall(value_provider) if cached else value_provider
        else:
            value_provider = _error_func

        object.__setattr__(self, Proxy.CONSTRUCT_FIELD, value_provider)

    __slots__ = [CONSTRUCT_FIELD, "__weakref__"]

    def _set_provider(self, value_provider: Callable, cached=True) -> None:
        """Set value
        @param value: value, that should be proxied by proxy
        """
        provider = _LazyCall(value_provider) if cached else value_provider
        object.__setattr__(self, Proxy.CONSTRUCT_FIELD, provider)

    def _get_provider(self) -> Callable[..., T]:
        """Get proxied value"""
        return _get_proxy_field(self, Proxy.CONSTRUCT_FIELD)

    @classmethod
    def __new__(cls, *args, **kwargs):
        """Build new type of proxy, setting magic methods on it"""

        def make_method(name):
            def method(self, *args, **kwargs):
                return getattr(_get_proxy_field(self, Proxy.CONSTRUCT_FIELD)(), name)(
                    *args, **kwargs
                )

            return method

        namespace = {}
        for magic_method in cls._magic_methods:
            namespace[magic_method] = make_method(magic_method)

        new_type = type(cls.__name__, (cls,), namespace)
        return object.__new__(new_type)

    # TODO convert all magics to methods
    def __add__(self, other):
        return _get_proxy_field(self, Proxy.CONSTRUCT_FIELD)() + other

    def __getattribute__(self, name):
        if name in _proxy_attrs:
            return _get_proxy_field(self, name)

        return getattr(_get_proxy_field(self, Proxy.CONSTRUCT_FIELD)(), name)

    def __bool__(self):
        try:
            try:
                return getattr(
                    _get_proxy_field(self, Proxy.CONSTRUCT_FIELD)(), "__bool__"
                )()
            except AttributeError:
                pass
            try:
                return bool(
                    getattr(_get_proxy_field(self, Proxy.CONSTRUCT_FIELD)(), "__len__")()
                )
            except AttributeError:
                return True
        except ValueError:
            return False

    @staticmethod
    def set_value(proxy: "Proxy", value: Any, cached=True):
        provider = value if callable(value) else lambda: value
        proxy._set_provider(provider, cached)

    @staticmethod
    def get_value(proxy: "Proxy"):
        return proxy._get_provider()()

    @staticmethod
    def initialized(proxy: "Proxy"):
        return proxy._get_provider() is not _error_func

    @staticmethod
    def set_proxies(proxies: List["Proxy"], values: List[Any]) -> None:
        """Set inner values to proxies.
        @param proxies: list of proxy, to set inner value
        @param values: list of inner values to set on proxy
        """
        if not len(proxies) == len(values):
            raise ValueError("Length of proxies and length or values must be equal")

        for proxy, value in zip(proxies, values):
            Proxy.set_value(proxy, value)
