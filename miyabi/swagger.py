from typing import (
    Any,
    Dict,
    List,
    Tuple,
)

import miyabi.libs


class Basic:
    def __init__(
            self, host: str, title: str, version: str, schemes: List[str], base_path: str) -> None:
        self.host = host
        self.title = title
        self.version = version
        self.schemes = schemes
        self.base_path = base_path


class Exporter:
    @classmethod
    def _schema_to_definition(cls, schema) -> Tuple[str, Dict[str, Any]]:
        return (
            schema.__class__.__name__,
            {
                'type': 'object',
                'properties': {
                    key: {
                        'type': value.__class__.__name__.lower(),
                    } for key, value in miyabi.libs.iter_attribute(schema)
                }
            }
        )

    @classmethod
    def generate(cls, basic: Basic, registry) -> Dict[str, Any]:
        swagger_definition = {
            'swagger': '2.0',
            'host': basic.host,
            'info': {
                'title': basic.title,
                'version': basic.version,
            },
            'schemes': basic.schemes,
            'basePath': basic.base_path,
            'produces': ['application/json'],
        }

        paths = {}
        definitions = {}
        for operation_id, (method, path, view_definition) in registry.operation_ids.items():
            if path not in paths:
                paths[path] = {}

            paths[path][method.lower()] = {
                'operationId': operation_id,
            }
            method_definiton = paths[path][method.lower()]
            parameter_definiton = []
            path_schema = view_definition.request_definition.path_schema
            if path_schema:
                for key, value in miyabi.libs.iter_attribute(path_schema):
                    parameter_definiton.append({
                        'name': key,
                        'in': 'path',
                        'type': value.__class__.__name__.lower(),
                        'required': True,
                    })

            body_schema = view_definition.request_definition.body_schema
            if body_schema:
                parameter_definiton.append({
                    'name': key,
                    'in': 'body',
                    'required': True,
                    'schema': {
                        '$ref': '#/definitions/{}'.format(body_schema.__class__.__name__)
                    }
                })
                definition_name, definition = cls._schema_to_definition(body_schema)
                definitions[definition_name] = definition

            if parameter_definiton:
                method_definiton['parameters'] = parameter_definiton

            response_definitions = view_definition.response_definitions
            method_definiton['responses'] = {
                int(status_code): {
                    'description': definition.description,
                    'schema': {
                        '$ref': '#/definitions/{}'.format(definition.schema.__class__.__name__)
                    }
                } for status_code, definition in response_definitions.iter_available()
            }

            for status_code, definition in response_definitions.iter_available():
                definition_name, _definition = cls._schema_to_definition(definition.schema)
                definitions[definition_name] = _definition

        swagger_definition['paths'] = paths
        swagger_definition['definitions'] = definitions

        return swagger_definition
