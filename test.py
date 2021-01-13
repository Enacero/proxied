import copy
import math
import pytest

from proxy import Proxy

INT_TEST_VALUE = 10
INT_TEST_VALUE_PLUS_1 = 11
INT_TEST_VALUE_MINUS_1 = 9
STR_TEST_VALUE = "10"


def test_inner_init():
    proxy = Proxy(value=INT_TEST_VALUE)
    assert proxy == INT_TEST_VALUE


def test_value_provider_init():
    proxy = Proxy(value_provider=lambda: INT_TEST_VALUE)

    assert proxy == INT_TEST_VALUE


def test_both_init_raises():
    with pytest.raises(ValueError):
        Proxy(INT_TEST_VALUE, lambda: INT_TEST_VALUE)


def test_access_to_not_initialized():
    proxy = Proxy()
    with pytest.raises(ValueError):
        assert not proxy.data


def test_set_inner():
    proxy = Proxy()
    Proxy.set_value(proxy, INT_TEST_VALUE)
    assert proxy == INT_TEST_VALUE


def test_get_inner():
    proxy = Proxy(INT_TEST_VALUE)
    assert Proxy.get_value(proxy) == INT_TEST_VALUE


def test_initialized():
    proxy = Proxy()
    assert not Proxy.initialized(proxy)
    Proxy.set_value(proxy, INT_TEST_VALUE)
    assert Proxy.initialized(proxy)


def test_cached():
    first = Proxy()
    second = Proxy()

    class Fib:
        def __init__(self, first, second):
            self.first = first
            self.second = second

        def __call__(self, *args, **kwargs):
            next = self.first + self.second
            self.second = self.first
            self.first = next
            return next

    fib = Fib(first, second)
    fib_func = Proxy(value_provider=fib, cached=False)
    Proxy.set_value(first, 0)
    Proxy.set_value(second, 1)

    assert fib_func == 1
    assert fib_func == 1
    assert fib_func == 2
    assert fib_func == 3
    assert fib_func == 5


def test__dict__():
    class Test:
        pass

    proxy = Proxy()
    with pytest.raises(AttributeError):
        proxy.__dict__

    Proxy.set_value(proxy, Test())
    assert proxy.__dict__ == {}


def test_set_proxies():
    proxies = [Proxy(), Proxy(), Proxy()]
    values = [INT_TEST_VALUE_MINUS_1, INT_TEST_VALUE, INT_TEST_VALUE_PLUS_1]
    Proxy.set_proxies(proxies, values)
    for proxy, value in zip(proxies, values):
        assert proxy == value

    with pytest.raises(ValueError):
        Proxy.set_proxies(proxies, [1, 2])


def test_expensive_constructor_called_once(mocker):
    expensive = mocker.Mock()
    proxy = Proxy(value_provider=expensive)
    assert not proxy == INT_TEST_VALUE
    assert not proxy == STR_TEST_VALUE
    expensive.assert_called_once()


def test_with():
    glob_dict = {}

    class Test:
        def __enter__(self):
            glob_dict[INT_TEST_VALUE] = INT_TEST_VALUE
            return glob_dict

        def __exit__(self, exc_type, exc_val, exc_tb):
            del glob_dict[INT_TEST_VALUE]

    proxy = Proxy(Test())
    with proxy as value:
        assert value[INT_TEST_VALUE] == INT_TEST_VALUE
    assert not len(glob_dict.items())


def test_conversions():
    proxy = Proxy(STR_TEST_VALUE)
    assert int(proxy) == int(STR_TEST_VALUE)
    assert float(proxy) == float(STR_TEST_VALUE)
    assert complex(proxy) == complex(STR_TEST_VALUE)
    Proxy.set_value(proxy, INT_TEST_VALUE)
    assert hex(proxy) == hex(INT_TEST_VALUE)


def test_comparisons():
    proxy = Proxy(INT_TEST_VALUE)
    assert INT_TEST_VALUE_PLUS_1 > proxy
    assert INT_TEST_VALUE_MINUS_1 < proxy
    assert INT_TEST_VALUE == proxy
    assert INT_TEST_VALUE_PLUS_1 != proxy
    assert proxy >= INT_TEST_VALUE_MINUS_1
    assert proxy <= INT_TEST_VALUE_PLUS_1


def test_str():
    class Test:
        def __bytes__(self):
            return bytes(INT_TEST_VALUE)

    proxy = Proxy(INT_TEST_VALUE)
    assert str(proxy) == STR_TEST_VALUE
    assert repr(proxy) == STR_TEST_VALUE
    test_obj = Test()
    proxy = Proxy(test_obj)
    assert bytes(proxy) == bytes(test_obj)


def test_hash():
    proxy = Proxy(INT_TEST_VALUE)
    assert hash(INT_TEST_VALUE) == hash(proxy)


def test_bool():
    proxy = Proxy(INT_TEST_VALUE)
    assert bool(proxy) == bool(INT_TEST_VALUE)

    class Test:
        pass

    proxy = Proxy(Test())
    assert bool(proxy)

    class Test:
        def __init__(self, val):
            self.val = [] if not val else [val]

        def __len__(self):
            return len(self.val)

    proxy = Proxy(Test(0))
    assert not proxy

    proxy = Proxy(Test(INT_TEST_VALUE))
    assert proxy


def test_dir():
    proxy = Proxy()

    assert dir(proxy) == []

    Proxy.set_value(proxy, INT_TEST_VALUE)
    assert dir(proxy) == dir(INT_TEST_VALUE)


def test_descriptors():
    class Test:
        @property
        def data(self):
            return INT_TEST_VALUE

    proxy = Proxy(Test())

    assert proxy.data == INT_TEST_VALUE

    proxy = Proxy(property)

    class Test:
        @proxy
        def data(self):
            return INT_TEST_VALUE

    assert Test().data == INT_TEST_VALUE


def test_list():
    proxy = Proxy([INT_TEST_VALUE, INT_TEST_VALUE_PLUS_1])
    assert len(proxy)
    assert list(reversed(proxy)) == [INT_TEST_VALUE_PLUS_1, INT_TEST_VALUE]

    assert proxy[0:] == [INT_TEST_VALUE, INT_TEST_VALUE_PLUS_1]
    assert proxy[0] == INT_TEST_VALUE
    proxy[0] = INT_TEST_VALUE_PLUS_1
    assert proxy[0] == INT_TEST_VALUE_PLUS_1


def test_dict():
    proxy = Proxy({INT_TEST_VALUE: INT_TEST_VALUE})
    assert proxy[INT_TEST_VALUE] == INT_TEST_VALUE

    assert proxy.get(INT_TEST_VALUE) == INT_TEST_VALUE
    assert INT_TEST_VALUE in proxy

    with pytest.raises(KeyError):
        _ = proxy[INT_TEST_VALUE_PLUS_1]

    assert next(iter(proxy)) == next(iter(Proxy.get_value(proxy)))

    del proxy[INT_TEST_VALUE]


def test_next():
    proxy = Proxy(iter([INT_TEST_VALUE]))

    assert next(proxy) == INT_TEST_VALUE


def test_numeric_operations():
    proxy = Proxy(INT_TEST_VALUE)
    assert proxy + 1 == INT_TEST_VALUE + 1
    assert proxy - 1 == INT_TEST_VALUE - 1
    assert proxy * 2 == 2 * INT_TEST_VALUE
    assert proxy / 2 == INT_TEST_VALUE / 2
    assert proxy // 2 == INT_TEST_VALUE // 2
    assert proxy % 2 == INT_TEST_VALUE % 2
    assert divmod(proxy, 2) == divmod(INT_TEST_VALUE, 2)
    assert proxy ** 2 == INT_TEST_VALUE ** 2
    assert proxy << 2 == INT_TEST_VALUE << 2
    assert proxy >> 2 == INT_TEST_VALUE >> 2
    assert proxy & 2 == INT_TEST_VALUE & 2
    assert proxy ^ 2 == INT_TEST_VALUE ^ 2
    assert proxy | 2 == INT_TEST_VALUE | 2


def test_reverse_numeric_operations():
    proxy = Proxy(INT_TEST_VALUE)
    assert 1 + proxy == INT_TEST_VALUE + 1
    assert 1 - proxy == 1 - INT_TEST_VALUE
    assert 2 * proxy == 2 * INT_TEST_VALUE
    assert 2 / proxy == 2 / INT_TEST_VALUE

    assert 2 // proxy == 2 // INT_TEST_VALUE

    assert 2 % proxy == 2 % INT_TEST_VALUE
    assert divmod(2, proxy) == divmod(2, INT_TEST_VALUE)
    assert 2 ** proxy == 2 ** INT_TEST_VALUE
    assert 2 << proxy == 2 << INT_TEST_VALUE
    assert 2 >> proxy == 2 >> INT_TEST_VALUE
    assert 2 & proxy == 2 & INT_TEST_VALUE
    assert 2 ^ proxy == 2 ^ INT_TEST_VALUE
    assert 2 | proxy == 2 | INT_TEST_VALUE


def test_unary_numeric_operations():
    proxy = Proxy(INT_TEST_VALUE)
    assert +proxy == +INT_TEST_VALUE
    assert -proxy == -INT_TEST_VALUE
    assert abs(-proxy) == abs(-INT_TEST_VALUE)
    assert ~proxy == ~INT_TEST_VALUE


def test_builtin_math():
    proxy = Proxy(INT_TEST_VALUE)
    assert round(proxy) == round(INT_TEST_VALUE)
    assert math.ceil(proxy) == math.ceil(INT_TEST_VALUE)
    assert math.floor(proxy) == math.floor(INT_TEST_VALUE)
    assert math.trunc(proxy) == math.trunc(INT_TEST_VALUE)
    assert abs(proxy) == abs(INT_TEST_VALUE)


def _test_func(proxied):
    return proxied


def test_return_proxy():
    class TestA:
        def __init__(self):
            self._proxied = Proxy()

        def get_proxy(self):
            return self._proxied

    class TestB:
        _proxied = Proxy()

        def get_proxy(self):
            return self._proxied

    _test_func(TestA().get_proxy())
    _test_func(TestB().get_proxy())


def test_copy():
    value = {INT_TEST_VALUE: [INT_TEST_VALUE]}
    proxy = Proxy(value)
    assert copy.copy(proxy) is not Proxy.get_value(proxy)
    assert copy.copy(proxy) == Proxy.get_value(proxy)


def test_attrs():
    class Test:
        pass

    proxy = Proxy(Test())
    proxy.x = INT_TEST_VALUE
    assert proxy.x == INT_TEST_VALUE
    del proxy.x
