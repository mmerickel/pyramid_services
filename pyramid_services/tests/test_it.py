import pyramid.testing
import unittest
from zope.interface import (
    Interface,
    implementer,
)
import webtest

class TestIntegration_register_service(unittest.TestCase):
    def setUp(self):
        self.config = pyramid.testing.setUp()
        self.config.include('pyramid_services')

    def tearDown(self):
        pyramid.testing.tearDown()

    def _makeApp(self):
        app = self.config.make_wsgi_app()
        return webtest.TestApp(app)

    def test_context_sensitive(self):
        config = self.config
        config.set_root_factory(root_factory)

        config.register_service(DummyService('foo'))
        config.register_service(DummyService('bar'), context=Leaf)

        config.add_view(DummyView(), context=Root, renderer='string')
        config.add_view(DummyView(), context=Leaf, renderer='string')
        config.add_view(
            DummyView(context=Root()), context=Leaf, name='baz',
            renderer='string')

        app = self._makeApp()
        resp = app.get('/')
        self.assertEqual(resp.body, b'foo')
        resp = app.get('/leaf')
        self.assertEqual(resp.body, b'bar')
        resp = app.get('/leaf/baz')
        self.assertEqual(resp.body, b'foo')

    def test_name(self):
        config = self.config
        config.set_root_factory(root_factory)

        config.register_service(DummyService('foo'), name='foo')
        config.register_service(DummyService('bar'), name='bar')

        config.add_view(
            DummyView(name='foo'), context=Leaf, name='foo', renderer='string')
        config.add_view(
            DummyView(name='bar'), context=Leaf, name='bar', renderer='string')

        app = self._makeApp()
        resp = app.get('/leaf/foo')
        self.assertEqual(resp.body, b'foo')
        resp = app.get('/leaf/bar')
        self.assertEqual(resp.body, b'bar')

    def test_iface(self):
        config = self.config
        config.set_root_factory(root_factory)

        config.register_service(DummyService('foo'), IFooService)
        config.register_service(DummyService('bar'), IBarService)

        config.add_view(
            DummyView(iface=IFooService), context=Leaf, name='foo',
            renderer='string')
        config.add_view(
            DummyView(iface=IBarService), context=Leaf, name='bar',
            renderer='string')
        config.add_view(
            DummyView(iface=IBazService), context=Leaf, name='baz',
            renderer='string')

        app = self._makeApp()
        resp = app.get('/leaf/foo')
        self.assertEqual(resp.body, b'foo')
        resp = app.get('/leaf/bar')
        self.assertEqual(resp.body, b'bar')
        self.assertRaises(Exception, lambda: app.get('/leaf/baz'))

class TestIntegration_register_service_factory(unittest.TestCase):
    def setUp(self):
        self.config = pyramid.testing.setUp()
        self.config.include('pyramid_services')

    def tearDown(self):
        pyramid.testing.tearDown()

    def _makeApp(self):
        app = self.config.make_wsgi_app()
        return webtest.TestApp(app)

    def test_context_sensitive(self):
        config = self.config
        config.set_root_factory(root_factory)

        config.register_service_factory(DummyServiceFactory('foo'))
        config.register_service_factory(
            DummyServiceFactory('bar'), context=Leaf)

        config.add_view(DummyView(), context=Root, renderer='string')
        config.add_view(DummyView(), context=Leaf, renderer='string')
        config.add_view(
            DummyView(context=Root()), context=Leaf, name='baz',
            renderer='string')

        app = self._makeApp()
        resp = app.get('/')
        self.assertEqual(resp.body, b'foo')
        resp = app.get('/leaf')
        self.assertEqual(resp.body, b'bar')
        resp = app.get('/leaf/baz')
        self.assertEqual(resp.body, b'foo')

    def test_name(self):
        config = self.config
        config.set_root_factory(root_factory)

        config.register_service_factory(DummyServiceFactory('foo'), name='foo')
        config.register_service_factory(DummyServiceFactory('bar'), name='bar')

        config.add_view(
            DummyView(name='foo'), context=Leaf, name='foo', renderer='string')
        config.add_view(
            DummyView(name='bar'), context=Leaf, name='bar', renderer='string')

        app = self._makeApp()
        resp = app.get('/leaf/foo')
        self.assertEqual(resp.body, b'foo')
        resp = app.get('/leaf/bar')
        self.assertEqual(resp.body, b'bar')

    def test_iface(self):
        config = self.config
        config.set_root_factory(root_factory)

        config.register_service_factory(
            DummyServiceFactory('foo'), IFooService)
        config.register_service_factory(
            DummyServiceFactory('bar'), IBarService)

        config.add_view(
            DummyView(iface=IFooService), context=Leaf, name='foo',
            renderer='string')
        config.add_view(
            DummyView(iface=IBarService), context=Leaf, name='bar',
            renderer='string')
        config.add_view(
            DummyView(iface=IBazService), context=Leaf, name='baz',
            renderer='string')

        app = self._makeApp()
        resp = app.get('/leaf/foo')
        self.assertEqual(resp.body, b'foo')
        resp = app.get('/leaf/bar')
        self.assertEqual(resp.body, b'bar')
        self.assertRaises(Exception, lambda: app.get('/leaf/baz'))

def root_factory(request):
    return Root()

class Root(object):
    def __getitem__(self, key):
        return Leaf()

class Leaf(object):
    pass

class IFooService(Interface):
    pass

class IBarService(IFooService):
    pass

class IBazService(IFooService):
    pass

class DummyService(object):
    def __init__(self, result):
        self.result = result

    def __call__(self):
        return self.result

class DummyServiceFactory(object):
    def __init__(self, result):
        self.result = DummyService(result)

    def __call__(self, context, request):
        self.context = context
        self.request = request
        return self.result

class DummyView(object):
    def __init__(self, iface=None, context=None, name=None):
        self.iface = iface
        self.context = context
        self.name = name

    def __call__(self, request):
        svc = request.find_service(
           self.iface, context=self.context, name=self.name)
        return svc()
