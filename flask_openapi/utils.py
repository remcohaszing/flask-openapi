from werkzeug.routing import parse_rule


#: A mapping of werkzeug URL rule types to swagger path formats.
#:
#: See http://flask.pocoo.org/docs/0.11/quickstart/#variable-rules and
#: http://swagger.io/specification/#dataTypeFormat for details.
WERKZEUG_URL_SWAGGER_TYPE_MAP = {
    None: 'string',
    'string': 'string',
    'int': 'integer',
    'float': 'number',
    'path': 'string',
    'any': 'string',
    'uuid': 'string'
}


def add_optional(data, key, value):
    """
    Add a value to the data dict, but only if the value is not None.

    Args:
        data (dict): The dict to add the value to.
        key (str): The key to assign the value to in the data dict.
        value: The value to assign if it's not None.

    """
    if value is not None:
        data[key] = value


def parse_werkzeug_url(url):
    """
    Process a werkzeug URL rule.

    Args:
        url (str): The werkzeug URL rule to process.

    Returns:
        tuple: A tuple containing the OpenAPI formatted URL and a list
            of path segment descriptions.

    """
    path = ''
    parameters = []
    for typ, default, segment in parse_rule(url):
        if not typ:
            path += segment
            continue
        path += '{' + segment + '}'
        parameters.append({
            'name': segment,
            'in': 'path',
            'required': True,
            'type': WERKZEUG_URL_SWAGGER_TYPE_MAP.get(typ)
        })
    return path, parameters
