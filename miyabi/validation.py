import miyabi.exceptions


def validate_response(request, response) -> None:
    try:
        schema = request.miyabi.get_response_schema(response.status_code)
    except AttributeError as e:
        raise miyabi.exceptions.DefinitionError() from e

    miyabi.schema.validate(schema, response.json)
