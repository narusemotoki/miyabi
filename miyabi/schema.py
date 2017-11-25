import abc
from typing import (
    Any,
    List,
)

import miyabi.exceptions


class SchemaType(abc.ABC):
    @abc.abstractmethod
    def validate(self, obj: Any) -> Any:
        ...

    @classmethod
    def is_schema_type(cls, obj: Any) -> bool:
        return isinstance(obj, SchemaType)


class Integer(SchemaType):
    python_type = int

    def validate(self, obj: Any) -> int:
        try:
            return int(obj)
        except ValueError as e:
            raise miyabi.exceptions.ValidationError() from e


class String(SchemaType):
    python_type = str

    def validate(self, obj: Any) -> int:
        return str(obj)


class ContainerType:
    @classmethod
    def is_container_type(cls, obj: Any) -> bool:
        return isinstance(obj, ContainerType)


class List(ContainerType):
    def __init__(self, child: SchemaType) -> None:
        self.child = child

    def validate(self, obj: Any) -> List[Any]:
        if not isinstance(obj, list):
            raise miyabi.exceptions.ValidationError()

        return [validate(self.child, element) for element in obj]


def validate(schema: Any, obj: Any) -> Any:
    if SchemaType.is_schema_type(schema):
        return schema.validate(obj)

    if ContainerType.is_container_type(schema):
        return schema.validate(obj)

    out = schema.__class__()
    for key, value in miyabi.libs.iter_attribute(schema):
        try:
            setattr(out, key, validate(value, obj[key]))
        except KeyError as e:
            raise miyabi.exceptions.ValidationError() from e

    return out
