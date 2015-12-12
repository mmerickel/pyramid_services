================
pyramid_services
================

.. image:: https://travis-ci.org/mmerickel/pyramid_services.svg?branch=master
   :alt: Travis-CI Build Status
   :target: https://travis-ci.org/mmerickel/pyramid_services

The core of a service layer that integrates with the
`Pyramid Web Framework <https://docs.pylonsproject.org/projects/pyramid>`__.

``pyramid_services`` defines a pattern and helper methods for accessing a
pluggable service layer from within your Pyramid apps.

Installation
============

Install from `PyPI <https://pypi.python.org/pyramid_services>`__ using
``pip`` or ``easy_install`` inside a virtual environment.

.. code-block:: bash

  $ $VENV/bin/pip install pyramid_services

Or install directly from source.

.. code-block:: bash

  $ git clone https://github.com/mmerickel/pyramid_services.git
  $ cd pyramid_services
  $ $VENV/bin/pip install -e .

Setup
=====

Activate ``pyramid_services`` by including it into your pyramid application.

.. code-block:: python

  config.include('pyramid_services')

This will add some new directives to your ``Configurator``.

- ``config.register_service(obj, iface=Interface, context=Interface, name='')``

  This method will register a service object for the supplied
  ``iface``, ``context``, and ``name``. This effectively registers a
  singleton for your application as the ``obj`` will always be returned when
  looking for a service.

- ``config.register_service_factory(factory, iface=Interface, context=Interface, name='')``

  This method will register a factory for the supplied ``iface``,
  ``context``, and ``name``. The factory should be a callable accepting a
  ``context`` and a ``request`` and should return a service object. The
  factory will be used at most once per ``request``/``context``/``name``
  combination.

Usage
=====

After registering services with the ``Configurator``, they are now
accessible from the ``request`` object during a request lifecycle via the
``request.find_service(iface=Interface, context=_marker, name='')``
method. Unless a custom ``context`` is passed to ``find_service``, the
lookup will default to using ``request.context``. The ``context`` will default
to ``None`` if a service is searched for during or before traversal in Pyramid
when there may not be a ``request.context``.

.. code-block:: python

  svc = request.find_service(ILoginService)

Examples
========

Let's create a login service by progressively building up from scratch what
we want to use in our app.

Basically all of the steps in configuring an interface are optional, but
they are shown here as best practices.

.. code-block:: python

  # myapp/interfaces.py

  from zope.interface import Interface

  class ILoginService(Interface):
    def create_token_for_login(name):
      pass

With our interface we can now define a conforming instance.

.. code-block:: python

  # myapp/services.py

  class DummyLoginService(object):
    def create_token_for_login(self, name):
      return 'u:{0}'.format(name)

Let's hook it up to our application.

.. code-block:: python

  # myapp/main.py

  from pyramid.config import Configurator

  from myapp.services import DummyLoginService

  def main(global_config, **settings):
    config = Configurator()
    config.include('pyramid_services')

    config.register_service(DummyLoginService(), ILoginService)

    config.add_route('home', '/')
    config.scan('.views')
    return config.make_wsgi_app()

Finally, let's create our view that utilizes the service.

.. code-block:: python

  # myapp/views.py

  @view_config(route_name='home', renderer='json')
  def home_view(request):
    name = request.params.get('name', 'bob')

    login_svc = request.find_service(ILoginService)
    token = login_svc.create_token_for_login(name)

    return {'access_token': token}

If you start up this application, you will find that you can access
the home url and get custom tokens!

This is cool, but what's even better is swapping in a new service without
changing our view at all. Let's define a new ``PersistentLoginService``
that gets tokens from a database. We're going to need to setup some
database handling, but again nothing changes in the view.

.. code-block:: python

  # myapp/services.py

  from uuid import uuid4

  from myapp.model import AccessToken

  class PersistentLoginService(object):
    def __init__(self, dbsession):
      self.dbsession = dbsession

    def create_token_for_login(self, name):
      token = AccessToken(key=uuid4(), user=name)
      self.dbsession.add(token)
      return token.key

Below is some boilerplate for configuring a model using the excellent
`SQLAlchemy ORM <http://docs.sqlalchemy.org>`__.

.. code-block:: python

  # myapp/model.py

  from sqlalchemy import engine_from_config
  from sqlalchemy.ext.declarative import declarative_base
  from sqlalchemy.orm import sessionmaker
  from sqlalchemy.schema import Column
  from sqlalchemy.types import Text

  Base = declarative_base()

  def init_model(settings):
    engine = engine_from_config(settings)
    dbmaker = sessionmaker()
    dbmaker.configure(bind=engine)
    return dbmaker

  class AccessToken(Base):
    __tablename__ = 'access_token'

    key = Column(Text, primary_key=True)
    user = Column(Text, nullable=False)

Now we will update the application to use the new ``PersistentLoginService``.
However, we may have other services and it'd be silly to create a new
database connection for each service in a request. So we'll also add a
service that encapsulates the database connection. Using this technique
we can wire services together in the service layer.

.. code-block:: python

  # myapp/main.py

  from pyramid.config import Configurator
  import transaction
  import zope.sqlalchemy

  from myapp.model import init_model
  from myapp.services import PersistentLoginService

  def main(global_config, **settings):
    config = Configurator()
    config.include('pyramid_services')
    config.include('pyramid_tm')

    dbmaker = init_model(settings)

    def dbsession_factory(context, request):
      dbsession = dbmaker()
      # register the session with pyramid_tm for managing transactions
      zope.sqlalchemy.register(dbsession, transaction_manager=request.tm)
      return dbsession

    config.register_service_factory(dbsession_factory, name='db')

    def login_factory(context, request):
      dbsession = request.find_service(name='db')
      svc = PersistentLoginService(dbsession)
      return svc

    config.register_service_factory(login_factory, ILoginService)

    config.add_route('home', '/')
    config.scan('.views')
    return config.make_wsgi_app()

And finally the home view will remain unchanged.

.. code-block:: python

  # myapp/views.py

  @view_config(route_name='home', renderer='json')
  def home_view(request):
    name = request.params.get('name', 'bob')

    login_svc = request.find_service(ILoginService)
    token = login_svc.create_token_for_login(name)

    return {'access_token': token}

Hopefully this pattern is clear. It has several advantages over most basic
Pyramid tutorials.

- The model is completely abstracted from the views, making both easy to
  test on their own.

- The service layer can be developed independently of the views, allowing
  for dummy implementations for easy creation of templates and frontend
  logic. Later, the real service layer can be swapped in as it's developed,
  building out the backend functionality.

- Most services may be implemented in such a way that they do not depend on
  Pyramid or a particular request object.

- Different services may be returned based on a context, such as the
  result of traversal or some other application-defined discriminator.

Testing Examples
================

If you are writing an application that uses ``pyramid_services`` you may want
to do some integration testing that verifies that your application has
successfully called ``register_service`` or ``register_service_factory``. Using
``Pyramid``'s ``testing`` module to create a ``Configurator`` and after calling
``config.include('pyramid_services')`` you may use ``find_service_factory`` to
get information about a registered service.

Take as an example this test that verifies that ``dbsession_factory`` has been
correctly registered. This assumes you have a ``myapp.services`` package that
contains an ``includeme()`` function.

.. code-block:: python

  # myapp/tests/test_integration.py

  from myapp.services import dbsession_factory, login_factory, ILoginService

  class TestIntegration_services(unittest.TestCase):
    def setUp(self):
      self.config = pyramid.testing.setUp()
      self.config.include('pyramid_services')
      self.config.include('myapp.services')

    def tearDown(self):
      pyramid.testing.tearDown()

    def test_db_maker(self):
      result = self.config.find_service_factory(name='db')
      self.assertEqual(result, dbsession_factory)

    def test_login_factory(self):
      result = self.config.find_service_factory(ILoginService)
      self.assertEqual(result, login_factory)
