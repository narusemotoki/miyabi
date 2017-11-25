import http
from typing import (
    Iterator,
    Tuple,
)

import yaml
import pyramid.config
import pyramid.events
import pyramid.request
import pyramid.response
import pyramid.settings
import pyramid.tweens

import miyabi.libs
import miyabi.swagger
import miyabi.validation


__author__ = "Motoki Naruse"
__copyright__ = "Motoki Naruse"
__credits__ = ["Motoki Naruse"]
__email__ = "motoki@naru.se"
__license__ = "MIT"
__maintainer__ = "Motoki Naruse"
__version__ = '0.0.1'


class Miyabi:
    def __init__(self, config: pyramid.config.Configurator) -> None:
        self.config = config
        config.registry.miyabi = Registry()

    def add_route(self, name, path, *, request_method, view_definition, **kwargs) -> None:
        self.config.add_route(
            name, path, operation_id=name, request_method=request_method, **kwargs)
        self.config.registry.miyabi.add_operation_id(name, request_method, path, view_definition)

    def generate_swagger(self, basic: miyabi.swagger.Basic) -> None:
        swagger = miyabi.swagger.Exporter.generate(basic, self.config.registry.miyabi)

        with open('swagger.yaml', 'w') as f:
            f.write(yaml.dump(swagger, default_flow_style=False))


class OperationIDPredicate:
    def __init__(self, value: str, config) -> None:
        self.value = value

    def text(self) -> str:
        return "Operation ID = %s".format(self.value)

    phash = text

    def __call__(self, context, request) -> bool:
        request.miyabi.operation_id = self.value
        return True


class ViewDefinition:
    def __init__(self, *, request_definition, response_definitions):
        self.request_definition = request_definition
        self.response_definitions = response_definitions


class RequestDefinition:
    def __init__(
            self, *, consumes, schema, path_schema=None, body_schema=None, **kwargs
    ) -> None:
        self.consumes = consumes
        self.schema = schema
        self.path_schema = path_schema
        self.body_schema = body_schema

        # TODO: check schemas don't have duplicated attribute


class ResponseDefinition:
    def __init__(self, schema, description: str=None):
        self.description = schema.__doc__ if description is None else description
        self.schema = schema


class ResponseDefinitionContainer:
    def __init__(self, OK: ResponseDefinition) -> None:
        self.OK = OK

    def iter_available(self) -> Iterator[Tuple[int, ResponseDefinition]]:
        return iter(
            [
                (http.HTTPStatus.OK, self.OK),
            ]
        )

    def find_by_status_code(self, status_code: int) -> ResponseDefinition:
        for status, definition in self.iter_available():
            if int(status) == int(status_code):
                return definition
        raise KeyError()


class Registry:
    def __init__(self):
        self.operation_ids = {}

    def add_operation_id(
            self, operation_id: str, method: str, path: str, view_definition: ViewDefinition
    ) -> None:
        self.operation_ids[operation_id] = (method, path, view_definition)

    def get_view_definition(self, operation_id: str) -> ViewDefinition:
        return self.operation_ids[operation_id][2]


def combine_schemas(dest_schema, *schemas):
    given_attributes = {}
    for schema in schemas:
        for key in miyabi.libs.iter_attribute_key(schema):
            given_attributes[key] = getattr(schema, key)

    dest = dest_schema.__class__()
    for key in miyabi.libs.iter_attribute_key(dest):
        setattr(dest, key, given_attributes[key])

    return dest


def validate_path_schema(schema, request):
    if not schema:
        return None

    path_schema = schema.__class__()
    for key, value in miyabi.libs.iter_attribute(path_schema):
        try:
            setattr(path_schema, key, value.__class__(request.matchdict[key]))
        except KeyError:
            # TODO: Mark as BadRequest
            # Check optional
            pass

    return path_schema


def validate_body_schema(schema, request):
    if not schema:
        return None

    body_schema = schema.__class__()
    for key in miyabi.libs.iter_attribute_key(body_schema):
        try:
            # TODO: Type check
            setattr(body_schema, key, request.json[key])
        except KeyError:
            # TODO: Mark as BadRequest
            # Check optional
            pass

    return body_schema


def validate_request(event: pyramid.events.BeforeTraversal) -> None:
    print("validate_request", event.request.miyabi)
    request = event.request
    context = request.miyabi
    view_definition = request.registry.miyabi.get_view_definition(context.operation_id)
    dest_schema = view_definition.request_definition.schema
    path_schema = validate_path_schema(view_definition.request_definition.path_schema, request)
    body_schema = validate_body_schema(view_definition.request_definition.body_schema, request)

    context.request_schema = combine_schemas(
        dest_schema,
        *[schema for schema in [path_schema, body_schema] if schema]
    )


def validate_response(event: pyramid.events.NewResponse) -> None:
    print("validate_response", event.request.miyabi)
    miyabi.validation.validate_response(event.request, event.response)


class Context:
    def __init__(self, registry: Registry) -> None:
        self.operation_id = None
        self.registry = registry

    def get_response_schema(self, status_code: int):
        view_definition = self.registry.get_view_definition(self.operation_id)
        return view_definition.response_definitions.find_by_status_code(status_code).schema

    def response(self, status_code: int, model) -> pyramid.response.Response:
        return pyramid.response.Response(
            status=status_code,
            json={
                key: getattr(model, key)
                for key in miyabi.libs.iter_attribute_key(self.get_response_schema(status_code))
            }
        )


def tween_factory(handler, registry):
    def tween(request: pyramid.request.Request) -> pyramid.response.Response:
        request.miyabi = Context(registry.miyabi)
        return handler(request)
    return tween


def includeme(config: pyramid.config.Configurator) -> None:
    print("Miyabi Pyramid")
    miyabi = Miyabi(config)
    config.add_directive('miyabi', lambda config: miyabi)
    config.add_route_predicate('operation_id', OperationIDPredicate)
    config.add_subscriber(validate_request, pyramid.events.BeforeTraversal)
    config.add_subscriber(validate_response, pyramid.events.NewResponse)
    config.add_tween('miyabi.tween_factory')
