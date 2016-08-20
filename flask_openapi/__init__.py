"""


"""
import functools
import inspect
import logging
from contextlib import suppress
from pathlib import Path

import yaml
from flask import jsonify
from flask import request

from flask_openapi.utils import add_optional
from flask_openapi.utils import parse_contact_string
from flask_openapi.utils import parse_werkzeug_url
from flask_openapi.validators import OpenAPISchemaValidator


log = logging.getLogger(__name__)
handler = logging.StreamHandler()
log.addHandler(handler)
log.setLevel(logging.DEBUG)


class UnnamedDefinitionError(Exception):
    ...


class UnknownDefinitionError(Exception):
    ...


_DEFAULT_CONFIG = {
    'OPENAPI_BASE_PATH': None,
    'OPENAPI_INFO_TITLE': None,
    'OPENAPI_INFO_DESCRIPTION': None,
    'OPENAPI_INFO_TERMS_OF_SERVICE': None,
    'OPENAPI_INFO_CONTACT': None,
    'OPENAPI_INFO_LICENSE': None,
    'OPENAPI_INFO_VERSION': None,
    'OPENAPI_SHOW_HOST': False,
    'OPENAPI_SWAGGER_JSON_URL': '/swagger.json'
}


class OpenAPI:
    def __init__(self, app=None):
        self._definitions = {}
        self._tags = {}
        self._validatorgetter = OpenAPISchemaValidator
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        for key, value in _DEFAULT_CONFIG.items():
            app.config.setdefault(key, value)

        swagger_json_url = self._config('swagger_json_url')
        app.add_url_rule(swagger_json_url, 'swagger', self.swagger_handler)

    def swagger_handler(self):
        """
        Get `swagger.json` as a JSON response.

        """
        return jsonify(self.swagger)

    @property
    def swagger(self):
        """
        dict: The resulting `swagger.json` data.

        """
        data = {
            'swagger': '2.0',
            'info': self.info,
            'paths': self.paths
        }
        add_optional(data, 'host', self.host)
        add_optional(data, 'basePath', self.base_path)
        add_optional(data, 'schemes', self.schemes)
        add_optional(data, 'paths', self.paths)
        add_optional(data, 'definitions', self.definitions)
        add_optional(data, 'tags', self.tags)
        return data

    @property
    def info(self):
        data = {
            'title': self._config('info_title'),
            'version': self._config('info_version')
        }
        add_optional(data, 'description', self._config('info_description'))
        add_optional(
            data,
            'termsOfService',
            self._config('info_terms_of_service'))
        contact = self._config('info_contact')
        if isinstance(contact, str):
            contact = parse_contact_string(contact)
        add_optional(data, 'contact', contact)
        add_optional(data, 'license', self._config('info_license'))
        return data

    @property
    def host(self):
        """
        str: The server host name.

        This is only returned if ``show_host`` is `True`.

        """
        if self._config('show_host'):
            return self.app.config['SERVER_NAME']

    @property
    def base_path(self):
        """
        str: The relative URL prefix for all API calls.

        """
        return self._config('base_path')

    @property
    def schemes(self):
        scheme = self.app.config.get('PREFERRED_URL_SCHEME')
        if scheme:
            return [scheme]

    @property
    def tags(self):
        """
        list: A list of tag descriptions.

        """
        if self._tags:
            return sorted(self._tags.values(), key=lambda x: x['name'])

    @property
    def paths(self):
        paths = {}
        for rule in self.app.url_map.iter_rules():
            log.info('Processing %r', rule)
            url, parameters = parse_werkzeug_url(rule.rule)
            paths.setdefault(url, {})
            if parameters:
                paths[url]['parameters'] = parameters
            for method in rule.methods:
                if method in ('HEAD', 'OPTIONS'):
                    # XXX Do we want to process these?
                    continue
                paths[url][method.lower()] = self._process_rule(rule)
        return paths

    @property
    def definitions(self):
        if self._definitions:
            return self._definitions

    def add_definition(self, definition, title=None):
        if isinstance(definition, (str, Path)):
            with open(str(definition)) as f:
                definition = yaml.load(f)
        if not title:
            title = definition.get('title')
        if not title:
            raise UnnamedDefinitionError(title)
        self._definitions[title] = definition

    def schema(self, schema):
        """
        A decorator to validate a request using a `JSON schema`_.

        Args:
            schema (dict|str): Either a dict to use as a schema directly
                or a named schema. (See `add_definition`.)

        """
        def wrapper(fn):
            fn.schema = schema

            @functools.wraps(fn)
            def inner(*args, **kwargs):
                schema = fn.schema
                if isinstance(schema, str):
                    schema = self._definitions[schema]
                validator = self._validatorgetter(schema)
                validator.validate(request.json)
                return fn(*args, **kwargs)
            return inner
        return wrapper

    def tag(self, *tags):
        """
        A decorator to validate a request using a `JSON schema`_.

        Args:
            schema (dict|str): Either a dict to use as a schema directly
                or a named schema. (See `add_definition`.)

        """
        def wrapper(fn):
            if not hasattr(fn, 'tags'):
                fn.tags = set()
            fn.tags.update(tags)
            for tag in tags:
                if tag not in self._tags:
                    self._tags[tag] = {
                        'name': tag
                    }
            return fn
        return wrapper

    def validatorgetter(self, fn):
        """
        Mark a function as a getter function to get a validator.

        The function will be called with the JSON schema as a `dict`.

        """
        self._validatorgetter = fn
        return fn

    def _config(self, name):
        return self.app.config.get('OPENAPI_' + name.upper())

    def _process_rule(self, rule):
        path = {
            'responses': {
                '200': {
                    'description': 'OK'
                }
            }
        }
        view_func = self.app.view_functions[rule.endpoint]
        schema = self._extract_schema(view_func)
        if schema:
            path['parameters'] = [{
                'in': 'body',
                'name': 'payload',
                'schema': schema
            }]
        add_optional(path, 'description', self._extract_description(view_func))
        with suppress(AttributeError):
            path['tags'] = sorted(view_func.tags)
        return path

    def _extract_schema(self, view_func):
        try:
            schema = view_func.schema
        except AttributeError:
            return
        if isinstance(schema, dict):
            return schema
        if schema in self._definitions:
            return {'$ref': '#/definitions/' + schema}
        raise UnknownDefinitionError(schema)

    def _extract_description(self, view_func):
        doc = inspect.getdoc(view_func)
        return doc
