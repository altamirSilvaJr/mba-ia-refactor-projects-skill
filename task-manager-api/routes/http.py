from flask import jsonify


def respond(result):
    payload, status = result
    return jsonify(payload), status
