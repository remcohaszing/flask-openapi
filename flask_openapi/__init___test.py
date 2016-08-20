"""
Tests for `flask_openapi`.

"""
from pathlib import Path
from unittest.mock import ANY

import pytest
import yaml
from flask import Flask
from jsonschema.exceptions import ValidationError

from flask_openapi import OpenAPI


@pytest.fixture
def app(request):
    """
    Get a Flask debug app named after the current test.

    """
    app = Flask(request.node.originalname or request.node.name)
    app.debug = True
    return app


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

    @app.route('/', methods=['post'])
    @openapi.schema('Spam')
    def handler():
        ...

    assert handler.schema == 'Spam'
    with pytest.raises(ValidationError):
        client.post('/', data='{}')


def test_schema_validation_unnamed(app, client):
    """
    Test if the unnamed schema is validated before continuing the request.

    """
    openapi = OpenAPI(app)

    @app.route('/', methods=['post'])
    @openapi.schema({
        'type': 'object',
        'required': ['spam']
    })
    def handler():
        ...

    assert handler.schema == {
        'type': 'object',
        'required': ['spam']
    }
    with pytest.raises(ValidationError):
        client.post('/', data='{}')