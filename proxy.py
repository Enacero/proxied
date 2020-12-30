from typing import Any, List, Callable, TypeVar, Generic, Iterable, Optional

__all__ = ("Proxy",)

T = TypeVar("T")


class _lazy_call:
    STONE = object()

    def __init__(self, fn: Callable[..., T]):
        self.fn = fn
        self.value = _lazy_call.STONE

    def __call__(self):
        if self.value is _lazy_call.STONE:
            self.value = self.fn()
        return self.value


def _error_func():
    """Function that is assigned by default, if no inner value
    or inner constructor supplied"""
    raise ValueError("There should be initialized constructor or obj.")


def _get_proxy_field(proxy: "Proxy[T]", name: str) -> Callable[..., T]:
    """Helper function to get proxy field"""
    return object.__getattribute__(proxy, name)


class Proxy(Generic[T]):
    CONSTRUCT_FIELD: str = "_constructor"

    proxy_attrs: Iterable[str] = (
        "proxy_attrs",
        "initialized",
        "set_inner",
        "get_inner",
        CONSTRUCT_FIELD,
        "set_proxies",
    )

    _magic_methods: Iterable[str] = (
        # Rich Comparisons
        "__gt__",
        "__ge__",
        "__lt__",
        "__le__",
        "__eq__",
        "__ne__",
        "__hash__",
        "__bool__",
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
        "__add__",
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
    )

    def __init__(
        self, inner: T = None, inner_constructor: Callable[[], Optional[T]] = None
    ):
        """
        Proxy class
        :param inner: value that should be proxied
        :param inner_constructor: callable, that returns object that should be proxied
        """
        if inner and inner_constructor:
            raise ValueError("There should be one of obj or constructor, not both.")

        def _wrapper() -> Optional[T]:
            return inner

        if inner:
            inner_constructor = _wrapper
        elif inner_constructor:
            inner_constructor = _lazy_call(inner_constructor)
        else:
            inner_constructor = _error_func

        object.__setattr__(self, Proxy.CONSTRUCT_FIELD, inner_constructor)

    __slots__ = [CONSTRUCT_FIELD, "__weakref__"]

    @property
    def initialized(self) -> bool:
        """Check that proxy is initialized, and is ready to work"""
        return _get_proxy_field(self, Proxy.CONSTRUCT_FIELD) is not _error_func

    def set_inner(self, inner: T) -> None:
        """Set inner value
        @param inner: inner value, that should be proxied by proxy
        """
        object.__setattr__(self, Proxy.CONSTRUCT_FIELD, lambda: inner)

    def get_inner(self) -> Callable[..., T]:
        """Get inner constructor"""
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

    def __getattribute__(self, name):
        if name in _get_proxy_field(self, "proxy_attrs"):
            return _get_proxy_field(self, name)

        return getattr(_get_proxy_field(self, Proxy.CONSTRUCT_FIELD)(), name)

    @staticmethod
    def set_proxies(proxies: List["Proxy"], values: List[Any]) -> None:
        """Set inner values to proxies.
        @param proxies: list of proxy, to set inner value
        @param values: list of inner values to set on proxy
        """
        if not len(proxies) == len(values):
            raise ValueError("Length of proxies and length or values must be equal")

        for proxy, value in zip(proxies, values):
            proxy.set_inner(value)
