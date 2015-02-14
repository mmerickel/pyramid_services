from pyramid.interfaces import IRequest
from zope.interface.registry import Components

def includeme(config):
    config.add_request_method(find_service)
    config.add_request_method(lambda _: Components(), 'service_cache',
                              reify=True)

    config.add_directive('register_service', register_service)
    config.add_directive('register_service_factory', register_service_factory)

def register_service(
    config,
    service,
    type_or_iface,
    name='',
):
    service = config.maybe_dotted(service)
    def service_factory(request):
        return service
    config.register_service_factory(service_factory, type_or_iface, name=name)

def register_service_factory(
    config,
    service_factory,
    type_or_iface,
    name='',
):
    service_factory = config.maybe_dotted(service_factory)
    type_or_iface = config.maybe_dotted(type_or_iface)
    def register():
        registry = config.registry
        registry.registerAdapter(
            service_factory, (IRequest,), type_or_iface, name=name)
    config.action(('service factory', type_or_iface), register)

def find_service(request, type_or_iface, name=''):
    cache = request.service_cache
    svc = cache.queryUtility(type_or_iface, name=name)
    if svc is None:
        registry = request.registry
        svc = registry.queryAdapter(request, type_or_iface, name=name)
        cache.registerUtility(svc, type_or_iface, name=name)
    return svc
