"""
Tests for `flask_openapi.utils`.

"""
import pytest

from flask_openapi import utils


@pytest.mark.parametrize('data,key,value,expected', [
    ({}, 'foo', None, {}),
    ({}, 'foo', {}, {}),
    ({}, 'foo', 'bar', {'foo': 'bar'})
])
def test_add_optional(data, key, value, expected):
    """
    Test if a value is added to the dict if it is not None.

    """
    utils.add_optional(data, key, value)
    assert data == expected


@pytest.mark.parametrize('url,path,parameters', [
    ('/items/<id>', '/items/{id}', [{
        'name': 'id',
        'in': 'path',
        'required': True,
        'type': 'string'
    }]),
    ('/items/<string:id>', '/items/{id}', [{
        'name': 'id',
        'in': 'path',
        'required': True,
        'type': 'string'
    }]),
    ('/items/<int:id>', '/items/{id}', [{
        'name': 'id',
        'in': 'path',
        'required': True,
        'type': 'integer'
    }]),
    ('/items/<float:id>', '/items/{id}', [{
        'name': 'id',
        'in': 'path',
        'required': True,
        'type': 'number'
    }]),
    ('/items/<path:id>', '/items/{id}', [{
        'name': 'id',
        'in': 'path',
        'required': True,
        'type': 'string'
    }]),
    ('/items/<any:id>', '/items/{id}', [{
        'name': 'id',
        'in': 'path',
        'required': True,
        'type': 'string'
    }]),
    ('/items/<uuid:id>', '/items/{id}', [{
        'name': 'id',
        'in': 'path',
        'required': True,
        'type': 'string'
    }])
])
def test_parse_werkzeug_url(url, path, parameters):
    """
    Test if parse_werkzeug_url processes the url and converts types.

    """
    result_path, result_parameters = utils.parse_werkzeug_url(url)
    assert result_path == path
    assert result_parameters == parameters


@pytest.mark.parametrize('input,expected', [
    ('Oak <oak@pallettown.kanto> (http://pallettown.kanto/oak)', {
        'name': 'Oak',
        'email': 'oak@pallettown.kanto',
        'url': 'http://pallettown.kanto/oak'
    }),
    ('Elm <elm@newbarktown.johto>', {
        'name': 'Elm',
        'email': 'elm@newbarktown.johto'
    }),
    ('Birch (http://littleroottown.hoenn/birch)', {
        'name': 'Birch',
        'url': 'http://littleroottown.hoenn/birch'
    }),
    ('<>', {}),
    ('', {})
])
def test_parse_contact_string(input, expected):
    """
    Test if contact information is properly extracted.

    """
    result = utils.parse_contact_string(input)
    assert result == expected
