import re

from werkzeug.routing import parse_rule


#: A mapping of werkzeug URL rule types to swagger path formats.
#:
#: See http://flask.pocoo.org/docs/0.11/quickstart/#variable-rules and
#: http://swagger.io/specification/#dataTypeFormat for details.
WERKZEUG_URL_SWAGGER_TYPE_MAP = {
    'default': 'string',  # 'default' is returned if no type is specified.
    'string': 'string',
    'int': 'integer',
    'float': 'number',
    'path': 'string',
    'any': 'string',
    'uuid': 'string'
}


#: This regular expression can be used to extract a name, email and url
#: from a string in the form::
#:
#:     name <email> (url)
AUTHOR_REGEX = re.compile(r"""
    ^[\s]*
    (?P<name>[^<(]+?)?        # name
    [\s]*
    (?:                       # optional
        <(?P<email>[^>(]+?)>  # <email>
    )?
    [\s]*
    (?:                       # optional
        \((?P<url>[^)]+?)\)   # (url)
    )?
    [\s]*$
    """, re.VERBOSE)


def add_optional(data, key, value):
    """
    Add a value to the data dict, but only if the value is not None.

    Args:
        data (dict): The dict to add the value to.
        key (str): The key to assign the value to in the data dict.
        value: The value to assign if it's not None.

    """
    if value not in (None, {}):
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
            'type': WERKZEUG_URL_SWAGGER_TYPE_MAP[typ]
        })
    return path, parameters


def parse_contact_string(string):
    """
    Convert a contact string to a matching dict.

    The contact string must be in the format::

        name <email> (url)

    *email* and *url* are optional.

    Args:
        string (str): The string to extract the contact information from.

    Returns:
        dict: A dict which holds the extracted contact information.

    """
    match = AUTHOR_REGEX.match(string)
    result = {}
    if match:
        add_optional(result, 'name', match.group('name'))
        add_optional(result, 'email', match.group('email'))
        add_optional(result, 'url', match.group('url'))
    return result
