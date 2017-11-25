from typing import (
    Any,
    Iterator,
)


def iter_attribute(obj: Any) -> Iterator[str]:
    return ((key, getattr(obj, key)) for key in iter_attribute_key(obj))


def iter_attribute_key(obj: Any) -> Iterator[str]:
    return (key for key in dir(obj) if not key.startswith('_'))
