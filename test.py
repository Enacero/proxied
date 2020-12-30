from contextlib import contextmanager
import math
import pytest

from proxy import Proxy

INT_TEST_VALUE = 10
INT_TEST_VALUE_PLUS_1 = 11
INT_TEST_VALUE_MINUS_1 = 9
STR_TEST_VALUE = "10"


def test_inner_init():
    proxy = Proxy(inner=INT_TEST_VALUE)
    assert proxy == INT_TEST_VALUE


def test_inner_constructor_init():
    proxy = Proxy(inner_constructor=lambda: INT_TEST_VALUE)

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
    proxy.set_inner(INT_TEST_VALUE)
    assert proxy == INT_TEST_VALUE


def test_get_inner():
    proxy = Proxy(INT_TEST_VALUE)
    assert proxy.get_inner()() == INT_TEST_VALUE


def test_initialized():
    proxy = Proxy()
    assert not proxy.initialized
    proxy.set_inner(INT_TEST_VALUE)
    assert proxy.initialized


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
    proxy = Proxy(inner_constructor=expensive)
    assert not proxy == INT_TEST_VALUE
    assert not proxy == STR_TEST_VALUE
    expensive.assert_called_once()


def test_with():
    glob_dict = {}

    @contextmanager
    def test_func():
        glob_dict[INT_TEST_VALUE] = INT_TEST_VALUE
        yield glob_dict
        del glob_dict[INT_TEST_VALUE]

    proxy = Proxy(test_func)

    with proxy() as value:
        assert value[INT_TEST_VALUE] == INT_TEST_VALUE
    assert not len(glob_dict.items())


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
    proxy = Proxy(INT_TEST_VALUE)
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

    assert next(iter(proxy)) == next(iter(proxy.get_inner()()))


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

    # Not working assert 2 // proxy == 2 // INT_TEST_VALUE

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


def _fuck(proxied):
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

    _fuck(TestA().get_proxy())
    _fuck(TestB().get_proxy())
