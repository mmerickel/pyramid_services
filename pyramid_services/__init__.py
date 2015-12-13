from zope.interface import (
    Interface,
    implementedBy,
    providedBy,
)
from zope.interface.interfaces import IInterface
from zope.interface.adapter import AdapterRegistry

_marker = object()

class IServiceClassifier(Interface):
    """ A marker interface to differentiate services from other objects
    in a shared registry."""

def includeme(config):
    config.add_request_method(find_service_factory)
    config.add_request_method(find_service)
    config.add_request_method(
        lambda _: AdapterRegistry(),
        'service_cache',
        reify=True,
    )

    config.add_directive('register_service', register_service)
    config.add_directive('register_service_factory', register_service_factory)
    config.add_directive('find_service_factory', find_service_factory)

class SingletonServiceWrapper(object):
    def __init__(self, service):
        self.service = service

    def __call__(self, context, request):
        return self.service

def register_service(
    config,
    service,
    iface=Interface,
    context=Interface,
    name='',
):
    service = config.maybe_dotted(service)
    service_factory = SingletonServiceWrapper(service)
    config.register_service_factory(
        service_factory,
        iface,
        context=context,
        name=name,
    )

def register_service_factory(
    config,
    service_factory,
    iface=Interface,
    context=Interface,
    name='',
):
    service_factory = config.maybe_dotted(service_factory)
    iface = config.maybe_dotted(iface)
    context = config.maybe_dotted(context)

    if not IInterface.providedBy(context):
        context_iface = implementedBy(context)
    else:
        context_iface = context

    def register():
        adapters = config.registry.adapters
        adapters.register(
            (IServiceClassifier, context_iface),
            iface,
            name,
            service_factory,
        )

    discriminator = ('service factories', (iface, context, name))
    if isinstance(service_factory, SingletonServiceWrapper):
        type_name = type(service_factory.service).__name__
    else:
        type_name = type(service_factory).__name__

    intr = config.introspectable(
        category_name='pyramid_services',
        discriminator=discriminator,
        title=str((iface.__name__, context.__name__, name)),
        type_name=type_name,
    )
    intr['name'] = name
    intr['type'] = iface
    intr['context'] = context
    config.action(discriminator, register, introspectables=(intr,))

def find_service(request, iface=Interface, context=_marker, name=''):
    if context is _marker:
        context = getattr(request, 'context', None)

    context_iface = providedBy(context)
    svc_types = (IServiceClassifier, context_iface)

    cache = request.service_cache
    svc = cache.lookup(svc_types, iface, name=name, default=None)
    if svc is None:
        adapters = request.registry.adapters
        svc_factory = adapters.lookup(svc_types, iface, name=name)
        if svc_factory is None:
            raise ValueError('could not find registered service')
        svc = svc_factory(context, request)
        cache.register(svc_types, iface, name, svc)
    return svc

def find_service_factory(
    config_or_request,
    iface=Interface,
    context=None,
    name='',
):
    context_iface = providedBy(context)
    svc_types = (IServiceClassifier, context_iface)

    adapters = config_or_request.registry.adapters
    svc_factory = adapters.lookup(svc_types, iface, name=name)
    if svc_factory is None:
        raise ValueError('could not find registered service')
    return svc_factory
