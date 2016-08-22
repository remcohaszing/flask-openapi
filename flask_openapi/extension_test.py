"""
Tests for `flask_openapi`.

"""
from pathlib import Path
from unittest.mock import ANY
from unittest.mock import call
from unittest.mock import Mock

import pytest
import yaml
from flask import Flask
from jsonschema.exceptions import ValidationError

from flask_openapi import OpenAPI
from flask_openapi.extension import UnknownDefinitionError
from flask_openapi.extension import UnnamedDefinitionError


@pytest.fixture
def app(request):
    """
    Get a Flask debug app named after the current test.

    """
    app = Flask(request.node.originalname or request.node.name)
    app.debug = True
    return app


def test_swagger_handler(app, client):
    """
    Test if the handler returns the swagger dict as a JSON response.

    """
    openapi = OpenAPI(app)
    response = client.get('/swagger.json')
    assert response.content_type == 'application/json'
    assert response.json == openapi.swagger


def test_swagger_minimal(app):
    """
    Test a swagger config for a minimal setup.

    """
    app.config['OPENAPI_INFO_VERSION'] = '1.2.3'
    openapi = OpenAPI(app)
    assert openapi.swagger == {
        'swagger': '2.0',
        'info': {
            'title': 'test_swagger_minimal',
            'version': '1.2.3'
        },
        'paths': ANY,
        'schemes': ['http'],
    }


def test_swagger_full(app):
    """
    Test a swagger config for a fully configured setup.

    """
    app.config.update(
        SERVER_NAME='api.example.com',
        OPENAPI_SHOW_HOST=True,
        OPENAPI_INFO_VERSION='1.2.3'
    )
    openapi = OpenAPI(app)
    assert openapi.swagger == {
        'swagger': '2.0',
        'info': {
            'title': 'test_swagger_full',
            'version': '1.2.3'
        },
        'paths': ANY,
        'host': 'api.example.com',
        'schemes': ['http']
    }


@pytest.mark.parametrize('config,expected', [
    ({
        'OPENAPI_INFO_TITLE': 'test',
        'OPENAPI_INFO_VERSION': '0.0.0'
    }, {
        'title': 'test',
        'version': '0.0.0'
    }),
    ({
        'OPENAPI_INFO_TITLE': 'test',
        'OPENAPI_INFO_VERSION': '0.0.0',
        'OPENAPI_INFO_DESCRIPTION': 'A nice API'
    }, {
        'title': 'test',
        'version': '0.0.0',
        'description': 'A nice API'
    }),
    ({
        'OPENAPI_INFO_TITLE': 'test',
        'OPENAPI_INFO_VERSION': '0.0.0',
        'OPENAPI_INFO_TERMS_OF_SERVICE': 'Only use this if you are awesome'
    }, {
        'title': 'test',
        'version': '0.0.0',
        'termsOfService': 'Only use this if you are awesome'
    }),
    ({
        'OPENAPI_INFO_TITLE': 'test',
        'OPENAPI_INFO_VERSION': '0.0.0',
        'OPENAPI_INFO_CONTACT': (
            'Remco Haszing'
            ' <remcohaszing@gmail.com>'
            ' (https://github.com/remcohaszing)'
        )
    }, {
        'title': 'test',
        'version': '0.0.0',
        'contact': {
            'name': 'Remco Haszing',
            'url': 'https://github.com/remcohaszing',
            'email': 'remcohaszing@gmail.com'
        }
    }),
    ({
        'OPENAPI_INFO_TITLE': 'test',
        'OPENAPI_INFO_VERSION': '0.0.0',
        'OPENAPI_INFO_CONTACT': {
            'name': 'Remco Haszing',
            'url': 'https://github.com/remcohaszing',
            'email': 'remcohaszing@gmail.com'
        }
    }, {
        'title': 'test',
        'version': '0.0.0',
        'contact': {
            'name': 'Remco Haszing',
            'url': 'https://github.com/remcohaszing',
            'email': 'remcohaszing@gmail.com'
        }
    }),
    ({
        'OPENAPI_INFO_TITLE': 'test',
        'OPENAPI_INFO_VERSION': '0.0.0',
        'OPENAPI_INFO_LICENSE': 'Beer ware'
    }, {
        'title': 'test',
        'version': '0.0.0',
        'license': 'Beer ware'
    })
])
def test_info(app, config, expected):
    """
    Test if all info data is read from the Flask config.

    """
    app.config.update(config)
    openapi = OpenAPI(app)
    assert openapi.info == expected


@pytest.mark.parametrize('show_host,server_name,expected', [
    (True, 'www.example.com', 'www.example.com'),
    (False, 'www.example.com', None)
])
def test_host(app, show_host, server_name, expected):
    """
    Test if the server name is returned depending on ``OPENAPI_SHOW_HOST``.

    """
    app.config.update(
        OPENAPI_SHOW_HOST=show_host,
        SERVER_NAME=server_name
    )
    openapi = OpenAPI(app)
    assert openapi.host == expected


def test_base_path(app):
    """
    Test if this returns the ``OPENAPI_BASE_PATH`` configuration option.

    """
    app.config['OPENAPI_BASE_PATH'] = '/v1'
    openapi = OpenAPI(app)
    assert openapi.base_path == '/v1'


@pytest.mark.parametrize('scheme,expected', [
    (None, None),
    ('http', ['http']),
    ('https', ['https'])
])
def test_schemes(app, scheme, expected):
    """
    Test if the preferred scheme is read from the Flask config.

    """
    app.config['PREFERRED_URL_SCHEME'] = scheme
    openapi = OpenAPI(app)
    assert openapi.schemes == expected


def test_tags():
    """
    Test if this added tags are returned.

    """
    openapi = OpenAPI()

    @openapi.tag('foo', 'bar')
    @openapi.tag('baz')
    def handler():
        ...

    assert handler.tags == {'foo', 'bar', 'baz'}
    assert openapi.tags == [
        {'name': 'bar'},
        {'name': 'baz'},
        {'name': 'foo'}
    ]


def test_no_tags():
    """
    Test if not tags result in None.

    """
    openapi = OpenAPI()
    assert openapi.tags is None


def test_paths(app):
    """
    Test if paths are generated from Flask routes and openapi decorators.

    """
    openapi = OpenAPI(app)

    openapi.add_definition({'type': 'object'}, 'POKéMON')

    @app.route('/pokemon', methods=['POST'])
    @openapi.tag('create', 'pokemon')
    @openapi.schema('POKéMON')
    def create_pokemon():
        ...

    @app.route('/pokemon')
    @openapi.tag('query', 'pokemon')
    def query_pokemon():
        ...

    @app.route('/pokemon/<id>')
    @openapi.tag('get', 'pokemon')
    @openapi.deprecated
    def get_one_pokemon():
        ...

    @app.route('/pokemon/<id>', methods=['PUT'])
    @openapi.tag('update', 'pokemon')
    @openapi.schema({'type': 'object'})
    def update_pokemon():
        ...

    assert openapi.paths == {
        '/pokemon': {
            'get': {
                'responses': {
                    '200': {
                        'description': 'OK'
                    }
                },
                'tags': ['pokemon', 'query']
            },
            'post': {
                'parameters': [
                    {
                        'in': 'body',
                        'name': 'payload',
                        'schema': {
                            '$ref': '#/definitions/POKéMON'
                        }
                    }
                ],
                'responses': {
                    '200': {
                        'description': 'OK'
                    }
                },
                'tags': ['create', 'pokemon']
            }
        },
        '/pokemon/{id}': {
            'get': {
                'deprecated': True,
                'responses': {
                    '200': {
                        'description': 'OK'
                    }
                },
                'tags': ['get', 'pokemon']
            },
            'parameters': [
                {
                    'in': 'path',
                    'name': 'id',
                    'required': True,
                    'type': 'string'
                }
            ],
            'put': {
                'parameters': [
                    {
                        'in': 'body',
                        'name': 'payload',
                        'schema': {
                            'type': 'object'
                        }
                    }
                ],
                'responses': {
                    '200': {
                        'description': 'OK'
                    }
                },
                'tags': ['pokemon', 'update']
            }
        },
        '/static/{filename}': {
            'get': {
                'description': ANY,
                'responses': {
                    '200': {
                        'description': 'OK'
                    }
                }
            },
            'parameters': [
                {
                    'in': 'path',
                    'name': 'filename',
                    'required': True,
                    'type': 'string'
                }
            ]
        },
        '/swagger.json': {
            'get': {
                'description': 'Get `swagger.json` as a JSON response.',
                'responses': {
                    '200': {
                        'description': 'OK'
                    }
                }
            }
        }
    }


def test_paths_missing_definition(app):
    """
    Test if a missing definition raises an error.

    """
    openapi = OpenAPI(app)

    @app.route('/', methods=['POST'])
    @openapi.schema('Missing')
    def handler():
        ...

    with pytest.raises(UnknownDefinitionError) as e:
        openapi.paths
    assert str(e.value) == 'UnknownDefinitionError(Missing)'


def test_no_definitions():
    """
    Test if an empty definitions object results in None.

    """
    openapi = OpenAPI()
    assert openapi.definitions is None


def test_add_definition_explicit_title():
    """
    Test if a title can be specified to name a model.

    """
    openapi = OpenAPI()
    openapi.add_definition({'type': 'object'}, 'Object')
    assert openapi.definitions == {
        'Object': {
            'type': 'object'
        }
    }


def test_add_definition_implicit_title():
    """
    Test if a JSON schema title can be specified to name a model.

    """
    openapi = OpenAPI()
    openapi.add_definition({'title': 'Object', 'type': 'object'})
    assert openapi.definitions == {
        'Object': {
            'title': 'Object',
            'type': 'object'
        }
    }


def test_add_definition_from_filename(tmpdir):
    """
    Test if a schema can be read from file when a filename is specified.

    """
    openapi = OpenAPI()
    f = tmpdir.join('object.yaml')
    f.write(yaml.dump({'title': 'Object', 'type': 'object'}))
    openapi.add_definition(str(f))
    assert openapi.definitions == {
        'Object': {
            'title': 'Object',
            'type': 'object'
        }
    }


def test_add_definition_unnamed(tmpdir):
    """
    Test if adding an unnamed schema definition raises an error.

    """
    openapi = OpenAPI()
    with pytest.raises(UnnamedDefinitionError) as e:
        openapi.add_definition({'type': 'object'})
    assert str(e.value) == "UnnamedDefinitionError({'type': 'object'})"


def test_add_definition_from_path(tmpdir):
    """
    Test if a schema can be read from file when a Path object is specified.

    """
    openapi = OpenAPI()
    f = tmpdir.join('object.yaml')
    f.write(yaml.dump({'title': 'Object', 'type': 'object'}))
    openapi.add_definition(Path(str(f)))
    assert openapi.definitions == {
        'Object': {
            'title': 'Object',
            'type': 'object'
        }
    }


def test_schema_validation_named(app, client):
    """
    Test if the named schema is validated before continuing the request.

    """
    openapi = OpenAPI(app)
    openapi.add_definition({
        'type': 'object',
        'required': ['spam']
    }, 'Spam')
    mock = Mock()

    @app.route('/', methods=['post'])
    @openapi.schema('Spam')
    def handler():
        mock()

    assert handler.schema == 'Spam'
    with pytest.raises(ValidationError):
        client.post('/', content_type='application/json', data='{}')
    assert not mock.called


def test_schema_validation_unnamed(app, client):
    """
    Test if the unnamed schema is validated before continuing the request.

    """
    openapi = OpenAPI(app)
    mock = Mock()

    @app.route('/', methods=['post'])
    @openapi.schema({
        'type': 'object',
        'required': ['spam']
    })
    def handler():
        mock()

    assert handler.schema == {
        'type': 'object',
        'required': ['spam']
    }
    with pytest.raises(ValidationError):
        client.post('/', content_type='application/json', data='{}')
    assert not mock.called


def test_schema_validation_ok(app, client):
    """
    Test if a handler is called when the input passes the schema.

    """
    openapi = OpenAPI(app)
    mock = Mock()

    @app.route('/', methods=['post'])
    @openapi.schema({
        'type': 'object',
        'required': ['spam']
    })
    def handler():
        mock()
        return ''

    client.post('/', content_type='application/json', data='{"spam": "bacon"}')
    assert mock.called


def test_custom_validator_getter(app, client):
    """
    Test if a custom validationgetter can be set using a decorator.

    """
    openapi = OpenAPI(app)
    mock = Mock()

    @openapi.validatorgetter
    def get_validator(schema):
        return mock(schema)

    @app.route('/', methods=['POST'])
    @openapi.schema({'type': 'object'})
    def handler():
        return ''
    client.post('/', content_type='application/json', data='{}')
    assert mock.call_args == call({'type': 'object'})
    assert mock.return_value.validate.call_args == call({})


def test_deprecated_warn(app, client, mocker):
    """
    Test if deprecated issues a warning if ``OPENAPI_WARN_DEPRECATED`` is warn.

    """
    warn = mocker.patch('warnings.warn')
    app.config['OPENAPI_WARN_DEPRECATED'] = 'warn'
    openapi = OpenAPI(app)

    @app.route('/')
    @openapi.deprecated
    def handler():
        return ''
    assert handler.deprecated
    client.get('/')
    assert warn.call_args == call(
        'Called deprecated GET http://localhost/',
        DeprecationWarning)


def test_deprecated_log(app, client, mocker):
    """
    Test if deprecated logs a warning if ``OPENAPI_WARN_DEPRECATED`` is log.

    """
    warning = mocker.patch('logging.Logger.warning')
    app.config['OPENAPI_WARN_DEPRECATED'] = 'log'
    openapi = OpenAPI(app)

    @app.route('/')
    @openapi.deprecated
    def handler():
        return ''
    assert handler.deprecated
    client.get('/')
    assert warning.call_args == call(
        'Called deprecated %s %s',
        'GET',
        'http://localhost/')
