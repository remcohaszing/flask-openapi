project = 'Flask-OpenAPI'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx.ext.todo'
]

default_role = 'any'
html_theme = 'sphinx_rtd_theme'
master_doc = 'index'
nitpicky = True

intersphinx_mapping = dict(
    flask=('http://flask.pocoo.org/docs', None),
    jsonschema=('https://python-jsonschema.readthedocs.io/en/latest', None),
    python=('https://docs.python.org/3.5', None),
    werkzeug=('http://werkzeug.pocoo.org/docs', None)
)

todo_include_todos = True
