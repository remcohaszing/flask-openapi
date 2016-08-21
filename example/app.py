#!/usr/bin/env python3
from glob import glob

from flask import Flask
from flask import jsonify
from flask import request
from flask_openapi import OpenAPI


app = Flask(__name__)
app.debug = True
app.config.update(
    OPENAPI_INFO_VERSION='1.2.3'
)
openapi = OpenAPI(app)

for filename in glob('*.schema.yaml'):
    openapi.add_definition(filename)


beverages = []


@app.route('/beer', methods=['POST'])
@openapi.deprecated
@openapi.schema('Beer')
def create_beer():
    """
    Create a new beer object.

    Please use the all new `beverages` API. This supports more than just
    beer.

    """
    return jsonify(beverages.append(dict(request.json, type='beer')))


@app.route('/beverage', methods=['POST'])
@openapi.schema('Beverage')
def create_beverage():
    """
    Create a new beverage.

    """
    return jsonify(beverages.append(request.json))


@app.route('/beverage')
@openapi.schema('Beverage')
def list_beverages():
    """
    Get an array of all beverages.

    """
    return jsonify(beverages)


if __name__ == '__main__':
    app.run()
