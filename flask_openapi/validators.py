"""
This module contains the `OpenAPISchemaValidator`.

The `OpenAPISchemaValidator` extends the `jsonschema.Draft4Validator`
with the functionalities as described in XXX.

"""
from jsonschema import Draft4Validator
from jsonschema.validators import extend


#: This extended validator implements the extra formats specified by the
#: Open API specification.
OpenAPISchemaValidator = extend(Draft4Validator, {})
