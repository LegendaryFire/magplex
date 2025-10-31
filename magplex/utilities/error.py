from http import HTTPStatus

from flask import Response, jsonify


class ErrorResponse(Response):
    def __init__(self, message, status=HTTPStatus.BAD_REQUEST):
        self.message = message
        self.status_code = status.value
        super().__init__(response=self._build_json(), status=self.status_code, mimetype='application/json')

    def _build_json(self):
        data = {
            "error": {
                "name": HTTPStatus(self.status_code).name,
                "code": self.status_code,
                "message": self.message
            }
        }
        return jsonify(data).get_data()