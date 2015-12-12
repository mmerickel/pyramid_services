import pyramid.testing
import unittest
from zope.interface import Interface
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
            DummyView(IFooService), context=Leaf, name='foo',
            renderer='string')
        config.add_view(
            DummyView(IBarService), context=Leaf, name='bar',
            renderer='string')
        config.add_view(
            DummyView(IBazService), context=Leaf, name='baz',
            renderer='string')

        app = self._makeApp()
        resp = app.get('/leaf/foo')
        self.assertEqual(resp.body, b'foo')
        resp = app.get('/leaf/bar')
        self.assertEqual(resp.body, b'bar')
        self.assertRaises(Exception, lambda: app.get('/leaf/baz'))

    def test_introspectable(self):
        config = self.config
        config.set_root_factory(root_factory)

        config.register_service(DummyService('foo'), IFooService)
        config.register_service(DummyService('foo'), IFooService, name="foo2")
        config.register_service(DummyService('bar'), IBarService, IFooService)

        introspector = config.registry.introspector
        intr = introspector.get(
            'pyramid_services',
            ('service factories', (IFooService, Interface, '')))
        self.assertEqual(intr.title, "('IFooService', 'Interface', '')")
        self.assertEqual(intr.type_name, "DummyService")
        self.assertEqual(intr["name"], "")
        self.assertEqual(intr["context"], Interface)
        self.assertEqual(intr["type"], IFooService)

        intr = introspector.get(
            'pyramid_services',
            ('service factories', (IFooService, Interface, 'foo2')))
        self.assertEqual(intr.title, "('IFooService', 'Interface', 'foo2')")
        self.assertEqual(intr.type_name, "DummyService")
        self.assertEqual(intr["name"], "foo2")
        self.assertEqual(intr["context"], Interface)
        self.assertEqual(intr["type"], IFooService)

        intr = introspector.get(
            'pyramid_services',
            ('service factories', (IBarService, IFooService, '')))
        self.assertEqual(intr.title, "('IBarService', 'IFooService', '')")
        self.assertEqual(intr.type_name, "DummyService")
        self.assertEqual(intr["name"], "")
        self.assertEqual(intr["context"], IFooService)
        self.assertEqual(intr["type"], IBarService)


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
        config.add_view(
            DummyView(context=None), context=Leaf, name='xyz',
            renderer='string')

        app = self._makeApp()
        resp = app.get('/')
        self.assertEqual(resp.body, b'foo')
        resp = app.get('/leaf')
        self.assertEqual(resp.body, b'bar')
        resp = app.get('/leaf/baz')
        self.assertEqual(resp.body, b'foo')
        resp = app.get('/leaf/xyz')
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
            DummyView(IFooService), context=Leaf, name='foo',
            renderer='string')
        config.add_view(
            DummyView(IBarService), context=Leaf, name='bar',
            renderer='string')
        config.add_view(
            DummyView(IBazService), context=Leaf, name='baz',
            renderer='string')

        app = self._makeApp()
        resp = app.get('/leaf/foo')
        self.assertEqual(resp.body, b'foo')
        resp = app.get('/leaf/bar')
        self.assertEqual(resp.body, b'bar')
        self.assertRaises(Exception, lambda: app.get('/leaf/baz'))

    def test_introspectable(self):
        config = self.config
        config.set_root_factory(root_factory)

        config.register_service_factory(
            DummyServiceFactory('foo'), IFooService)
        config.register_service_factory(
            DummyServiceFactory('foo'), IFooService, name="foo2")
        config.register_service_factory(
            DummyServiceFactory('bar'), IBarService, IFooService)

        introspector = config.registry.introspector
        intr = introspector.get(
            'pyramid_services',
            ('service factories', (IFooService, Interface, '')))
        self.assertEqual(intr.title, "('IFooService', 'Interface', '')")
        self.assertEqual(intr.type_name, "DummyServiceFactory")
        self.assertEqual(intr["name"], "")
        self.assertEqual(intr["context"], Interface)
        self.assertEqual(intr["type"], IFooService)

        intr = introspector.get(
            'pyramid_services',
            ('service factories', (IFooService, Interface, 'foo2')))
        self.assertEqual(intr.title, "('IFooService', 'Interface', 'foo2')")
        self.assertEqual(intr.type_name, "DummyServiceFactory")
        self.assertEqual(intr["name"], "foo2")
        self.assertEqual(intr["context"], Interface)
        self.assertEqual(intr["type"], IFooService)

        intr = introspector.get(
            'pyramid_services',
            ('service factories', (IBarService, IFooService, '')))
        self.assertEqual(intr.title, "('IBarService', 'IFooService', '')")
        self.assertEqual(intr.type_name, "DummyServiceFactory")
        self.assertEqual(intr["name"], "")
        self.assertEqual(intr["context"], IFooService)
        self.assertEqual(intr["type"], IBarService)

    def test_with_no_context(self):
        config = self.config
        config.register_service_factory(
            DummyServiceFactory('foo'), IFooService)
        config.add_view(DummyView(), context=Root, renderer='string')

        called = [False]
        def factory(request):
            called[0] = True
            svc = request.find_service(IFooService)
            self.assertEqual(svc.result, 'foo')
            return Root()
        config.set_root_factory(factory)

        app = self._makeApp()
        resp = app.get('/')
        self.assertEqual(resp.body, b'foo')
        self.assertEqual(called, [True])

class TestIntegration_find_service_factory(unittest.TestCase):
    def setUp(self):
        self.config = pyramid.testing.setUp()
        self.config.include('pyramid_services')

    def tearDown(self):
        pyramid.testing.tearDown()

    def test_find_service_factory(self):
        self.config.register_service_factory(DummyServiceFactory, IFooService)
        self.assertEqual(DummyServiceFactory, self.config.find_service_factory(IFooService))

    def test_find_service_factory_fail(self):
        self.assertRaises(ValueError, self.config.find_service_factory, IFooService)

    def test_find_service_factory_service(self):
        svc = DummyService('test')
        self.config.register_service(svc, IFooService)
        self.assertEqual(svc, self.config.find_service_factory(IFooService).service)


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
    def __init__(self, *a, **kw):
        self.a = a
        self.kw = kw

    def __call__(self, request):
        svc = request.find_service(*self.a, **self.kw)
        return svc()
