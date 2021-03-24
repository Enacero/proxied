import copy
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
    "__dict__",
}


class Proxy(Generic[T]):
    CONSTRUCT_FIELD = _CONSTRUCT_FIELD

    def __init__(
        self,
        value: T = None,
        value_provider: Callable[[], Optional[T]] = None,
        cached: bool = True,
    ):
        """
        Proxy class

        :param value: object that should be proxied
        :param value_provider: callable, that returns object that should be proxied
        :param cached: set False if you wants to call value_provider
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

    @staticmethod
    def set_value(proxy: "Proxy", value: Any, cached: bool = True) -> None:
        """Set inner value to proxy

        :param proxy: Proxy object
        :param value: value, that must be set
        :param cached: set False if you wants to call value_provider
            every time on access to proxy
        """
        proxy._set_provider(lambda: value, cached)

    @staticmethod
    def set_provider(proxy: "Proxy", provider: Callable, cached: bool = True) -> None:
        """Set callable, that on call return values to be proxied

        :param proxy: Proxy object
        :param provider: value provider that can produce proxied values
        :param cached: set False if you wants to call value_provider
            every time on access to proxy
        """
        proxy._set_provider(provider, cached)

    @staticmethod
    def get_value(proxy: "Proxy") -> Any:
        """Returns value from proxy"""
        return proxy._get_provider()()

    @staticmethod
    def is_initialized(proxy: "Proxy") -> bool:
        """Check, whether proxy is initialized with value or value constructor"""
        return proxy._get_provider() is not _error_func

    @staticmethod
    def set_proxies_values(proxies: List["Proxy"], values: List[Any]) -> None:
        """Set inner values to proxies.

        :param proxies: list of proxies, to set inner values
        :param values: list of inner values to set on proxies
        """
        if not len(proxies) == len(values):
            raise ValueError("Length of proxies and length or values must be equal")

        for proxy, value in zip(proxies, values):
            Proxy.set_value(proxy, value)

    @staticmethod
    def set_proxies_providers(
        proxies: List["Proxy"], providers: List[Callable], cached: bool = True
    ) -> None:
        """Set value providers to proxies.

        :param proxies: list of proxies, to set value providers
        :param providers: list of value providers to set on proxies
        :param cached: set False if you wants to call value_provider
            every time on access to proxy
        """
        if not len(proxies) == len(providers):
            raise ValueError("Length of proxies and length or values must be equal")

        if not all(callable(provider) for provider in providers):
            raise ValueError("Providers must be callable")

        for proxy, provider in zip(proxies, providers):
            Proxy.set_provider(proxy, provider, cached)

    __slots__ = [CONSTRUCT_FIELD, "__weakref__"]

    def _set_provider(self, value_provider: Callable, cached: bool = True) -> None:
        """Set value of proxy
        :param value_provider: Callable, that after return must return value,
            that will be stored in proxy
        :param cached: set False if you wants to call value_provider
            every time on access to proxy
        """
        provider = _LazyCall(value_provider) if cached else value_provider
        object.__setattr__(self, Proxy.CONSTRUCT_FIELD, provider)

    def _get_provider(self) -> Callable[..., T]:
        """Get value provider"""
        return _get_proxy_field(self, Proxy.CONSTRUCT_FIELD)

    @property
    def __dict__(self):
        try:
            return self._get_provider()().__dict__
        except ValueError:
            raise AttributeError("__dict__")

    def __dir__(self):
        try:
            return dir(self._get_provider()())
        except ValueError:
            return []

    def __setitem__(self, key, value):
        self._get_provider()()[key] = value

    def __delitem__(self, key):
        del self._get_provider()()[key]

    def __setattr__(self, key, value):
        return setattr(self._get_provider()(), key, value)

    def __delattr__(self, item):
        return delattr(self._get_provider()(), item)

    def __str__(self):
        return str(self._get_provider()())

    def __repr__(self):
        return repr(self._get_provider()())

    def __bytes__(self):
        return bytes(self._get_provider()())

    def __lt__(self, other):
        return self._get_provider()() < other

    def __le__(self, other):
        return self._get_provider()() <= other

    def __eq__(self, other):
        return self._get_provider()() == other

    def __ne__(self, other):
        return self._get_provider()() != other

    def __gt__(self, other):
        return self._get_provider()() > other

    def __ge__(self, other):
        return self._get_provider()() >= other

    def __hash__(self):
        return hash(self._get_provider()())

    def __call__(self, *args, **kwargs):
        return self._get_provider()()(*args, **kwargs)

    def __len__(self):
        return len(self._get_provider()())

    def __getitem__(self, item):
        return self._get_provider()()[item]

    def __iter__(self):
        return iter(self._get_provider()())

    def __next__(self):
        return next(self._get_provider()())

    def __contains__(self, item):
        return item in self._get_provider()()

    def __add__(self, other):
        return self._get_provider()() + other

    def __sub__(self, other):
        return self._get_provider()() - other

    def __mul__(self, other):
        return self._get_provider()() * other

    def __floordiv__(self, other):
        return self._get_provider()() // other

    def __mod__(self, other):
        return self._get_provider()() % other

    def __divmod__(self, other):
        return divmod(self._get_provider()(), other)

    def __pow__(self, power):
        return self._get_provider()() ** power

    def __lshift__(self, other):
        return self._get_provider()() << other

    def __rshift__(self, other):
        return self._get_provider()() >> other

    def __and__(self, other):
        return self._get_provider()() & other

    def __xor__(self, other):
        return self._get_provider()() ^ other

    def __or__(self, other):
        return self._get_provider()() | other

    def __truediv__(self, other):
        return self._get_provider()() / other

    def __neg__(self):
        return -(self._get_provider()())

    def __pos__(self):
        return +(self._get_provider()())

    def __abs__(self):
        return abs(self._get_provider()())

    def __invert__(self):
        return ~(self._get_provider()())

    def __complex__(self):
        return complex(self._get_provider()())

    def __int__(self):
        return int(self._get_provider()())

    def __float__(self):
        return float(self._get_provider()())

    def __index__(self):
        return self._get_provider()().__index__()

    def __enter__(self):
        return self._get_provider()().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._get_provider()().__exit__(exc_type, exc_val, exc_tb)

    def __radd__(self, other):
        return other + self._get_provider()()

    def __rsub__(self, other):
        return other - self._get_provider()()

    def __rmul__(self, other):
        return other * self._get_provider()()

    def __rtruediv__(self, other):
        return other / self._get_provider()()

    def __rfloordiv__(self, other):
        return other // self._get_provider()()

    def __rmod__(self, other):
        return other % self._get_provider()()

    def __rdivmod__(self, other):
        return divmod(other, self._get_provider()())

    def __copy__(self):
        return copy.copy(self._get_provider()())

    def __round__(self, n=None):
        return round(self._get_provider()(), n)

    def __trunc__(self):
        return self._get_provider()().__trunc__()

    def __reversed__(self):
        return reversed(self._get_provider()())

    def __rpow__(self, other):
        return other ** self._get_provider()()

    def __rlshift__(self, other):
        return other << self._get_provider()()

    def __rrshift__(self, other):
        return other >> self._get_provider()()

    def __rand__(self, other):
        return other & self._get_provider()()

    def __rxor__(self, other):
        return other ^ self._get_provider()()

    def __ror__(self, other):
        return other | self._get_provider()()

    def __getattribute__(self, name):
        if name in _proxy_attrs:
            return _get_proxy_field(self, name)

        return getattr(_get_proxy_field(self, Proxy.CONSTRUCT_FIELD)(), name)

    def __bool__(self) -> bool:
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
