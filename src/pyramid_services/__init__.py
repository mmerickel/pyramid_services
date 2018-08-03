from pyramid.config import PHASE2_CONFIG
from pyramid.interfaces import IRequest
from wired import ServiceRegistry
from zope.interface import Interface


_marker = object()


class IServiceRegistry(Interface):
    """ A marker interface for the service registry."""


class SingletonServiceWrapper:
    def __init__(self, service):
        self.service = service

    def __call__(self, context, request):
        return self.service


class ProxyFactory:
    def __init__(self, factory):
        self.factory = factory

    def __call__(self, container):
        request = container.get(IRequest)
        return self.factory(container.context, request)


class NewServiceContainer:
    """
    Event emitted when a request creates a service container.

    This is useful for registering any per-request services like as a way
    to inject ``request.tm`` into your container as the transaction manager.

    :ivar container: The service container.
    :ivar request: The request.

    """
    def __init__(self, container, request):
        self.container = container
        self.request = request


def includeme(config):
    config.add_request_method(find_service_factory)
    config.add_request_method(find_service)
    config.add_request_method(get_services, 'services', reify=True)

    config.add_directive('set_service_registry', set_service_registry)
    config.add_directive('register_service', register_service)
    config.add_directive('register_service_factory', register_service_factory)
    config.add_directive('find_service_factory', find_service_factory)

    config.set_service_registry(ServiceRegistry())


def set_service_registry(config, registry):
    def register():
        config.registry.registerUtility(registry, IServiceRegistry)
    intr = config.introspectable(
        category_name='service registry',
        discriminator='service registry',
        title='service registry',
        type_name='service registry',
    )
    intr['registry'] = registry
    config.action(
        'service registry',
        register,
        introspectables=(intr,),
        order=PHASE2_CONFIG,
    )


def register_service(
    config,
    service,
    iface=Interface,
    context=None,
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
    context=None,
    name='',
):
    service_factory = config.maybe_dotted(service_factory)
    iface = config.maybe_dotted(iface)
    context = config.maybe_dotted(context)

    def register():
        registry = config.registry.getUtility(IServiceRegistry)
        registry.register_factory(
            ProxyFactory(service_factory),
            iface,
            context=context,
            name=name,
        )

    discriminator = ('service factories', (iface, context, name))
    if isinstance(service_factory, SingletonServiceWrapper):
        type_name = _type_name(service_factory.service)
    else:
        type_name = _type_name(service_factory)

    intr = config.introspectable(
        category_name='pyramid_services',
        discriminator=discriminator,
        title=str((_type_name(iface), _type_name(context), name)),
        type_name=type_name,
    )
    intr['name'] = name
    intr['type'] = iface
    intr['context'] = context
    config.action(discriminator, register, introspectables=(intr,))


def find_service_factory(
    config_or_request,
    iface=Interface,
    context=None,
    name='',
):
    registry = config_or_request.registry.getUtility(IServiceRegistry)
    factory = registry.find_factory(iface, context=context, name=name)
    if factory is None:
        raise LookupError('could not find registered service')
    if isinstance(factory, ProxyFactory):
        return factory.factory
    return factory


def get_services(request):
    registry = request.registry.getUtility(IServiceRegistry)
    container = registry.create_container()
    container.set(request, IRequest)

    request.registry.notify(NewServiceContainer(container, request))
    return container


def find_service(request, iface=Interface, context=_marker, name=''):
    if context is _marker:
        context = getattr(request, 'context', None)
    return request.services.get(iface, context=context, name=name)


def _type_name(obj):
    name = getattr(obj, '__name__', None)
    if name is None:
        name = type(obj).__name__
    return name
