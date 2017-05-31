from zope.interface import (
    Interface,
    implementedBy,
    providedBy,
)
from zope.interface.interface import InterfaceClass
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


class ServiceInfo(object):
    def __init__(self, factory, context_iface):
        self.factory = factory
        self.context_iface = context_iface


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
    orig_iface = config.maybe_dotted(iface)
    context = config.maybe_dotted(context)

    if not IInterface.providedBy(context):
        context_iface = implementedBy(context)
    else:
        context_iface = context

    iface = _resolve_iface(orig_iface)

    info = ServiceInfo(service_factory, context_iface)

    def register():
        adapters = config.registry.adapters
        adapters.register(
            (IServiceClassifier, context_iface),
            iface,
            name,
            info,
        )

    discriminator = ('service factories', (orig_iface, context, name))
    if isinstance(service_factory, SingletonServiceWrapper):
        type_name = _type_name(service_factory.service)
    else:
        type_name = _type_name(service_factory)

    intr = config.introspectable(
        category_name='pyramid_services',
        discriminator=discriminator,
        title=str((_type_name(orig_iface), _type_name(context), name)),
        type_name=type_name,
    )
    intr['name'] = name
    intr['type'] = orig_iface
    intr['context'] = context
    config.action(discriminator, register, introspectables=(intr,))


def find_service(request, iface=Interface, context=_marker, name=''):
    if context is _marker:
        context = getattr(request, 'context', None)

    iface = _resolve_iface(iface)
    context_iface = providedBy(context)
    svc_types = (IServiceClassifier, context_iface)

    cache = request.service_cache
    svc = cache.lookup(svc_types, iface, name=name, default=None)
    if svc is None:
        adapters = request.registry.adapters
        info = adapters.lookup(svc_types, iface, name=name)
        if info is None:
            raise ValueError('could not find registered service')
        svc = info.factory(context, request)
        cache.register(
            (IServiceClassifier, info.context_iface),
            iface,
            name,
            svc,
        )
    return svc


def find_service_factory(
    config_or_request,
    iface=Interface,
    context=None,
    name='',
):
    iface = _resolve_iface(iface)
    context_iface = providedBy(context)
    svc_types = (IServiceClassifier, context_iface)

    adapters = config_or_request.registry.adapters
    info = adapters.lookup(svc_types, iface, name=name)
    if info is None:
        raise ValueError('could not find registered service')
    return info.factory


def _resolve_iface(obj):
    # if the object is an interface then we can quit early
    if IInterface.providedBy(obj):
        return obj

    # look for a cached iface
    iface = obj.__dict__.get('_service_iface', None)
    if iface is not None:
        return iface

    # make a new iface and cache it on the object
    name = _type_name(obj)
    iface = InterfaceClass(
        '%s_IService' % name,
        __doc__='pyramid_services generated interface',
    )
    obj._service_iface = iface
    return iface


def _type_name(obj):
    name = getattr(obj, '__name__', None)
    if name is None:
        name = type(obj).__name__
    return name
