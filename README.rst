proxied
-------
proxied package can be use to defer initialization of object.

Suppose we have:

**__init__.py**

.. code-block:: python

    from config import Config, load_config

    config: Config = None

    def init_app():
        config = load_config()

If we try to import config in another file, i.e.

**cool_staff.py**

.. code-block:: python

    from . import config

    ...

    init_staff(config.db_url)

We will end up importing None. So, we will be forced to
make import not at the top of the file.

**Here comes the proxied package**

**__init__.py**

.. code-block:: python

    from typing import Union
    from proxy import Proxy
    from config import Config, load_config

    config: Union[Config, Proxy] = Proxy()

    def init_app():
        config.set_inner(load_config())

Now we can easily import config at the top of the file work with
proxy object as it was the object of type Config.

Installation
------------

.. code-block::

    pip install proxied

Proxy
-----------------------
Proxy class can be initialized with inner or inner_constructor.
If inner_constructor is supplied, then it will be called once,
and the result will be cached.

If Proxy class is initialized without inner and inner_constructor,
the inner should be set later with a help of ``proxy.set_inner`` method.

.. code-block:: python

    from proxy import Proxy
    proxy = Proxy()
    proxy.set_inner({})
    proxy["test_key"] = 10


It's possible to set values for multiple proxies.

.. code-block:: python

    from proxy import Proxy
    proxies = [Proxy(), Proxy(), Proxy(), Proxy()]
    values = [10, 11, list(), dict()]
    Proxy.set_proxies(proxies, values)

There is a check, if proxy is initialized with proxied value

.. code-block:: python

    from proxy import Proxy
    proxy = Proxy()

    if not proxy.initialized:
        data = get_needed_data(...)
        proxy.set_inner(data)

Example
-------
.. code-block:: python

    from proxy import Proxy
    class NotAvailableDuringImport:
        @property
        def data(self):
            return "Not Available during import"


    proxy: Union[NotAvailableDuringImport, Proxy] = Proxy()
    proxy.set_inner(NotAvailableDuringImport)
    assert proxy.data == "Not Available during import"

License
-------

Copyright Oleksii Petrenko, 2020.

Distributed under the terms of the `MIT`_ license,
json_modify is free and open source software.

.. _`MIT`: https://github.com/Enacero/proxied/blob/master/LICENSE