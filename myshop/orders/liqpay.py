# import base64
# import json
# import hashlib


# class LiqPay:
#     def __init__(self, public_key, private_key):
#         self.public_key = public_key
#         self.private_key = private_key

#     def cnb_data(self, params):
#         params["public_key"] = self.public_key
#         json_string = json.dumps(params, separators=(',', ':'))
#         return base64.b64encode(json_string.encode("utf-8")).decode("utf-8")
    
#     def cnb_signature(self, data):
   
#         joined_row = self.private_key + data + self.private_key
#         sha1_hash = hashlib.sha1(joined_row.encode("utf-8")).digest()
#         return base64.b64encode(sha1_hash).decode("utf-8")

#     def decode_data_from_str(self, data):
#         decoded = base64.b64decode(data)
#         return json.loads(decoded.decode("utf-8"))


import base64
import hashlib
import json


class LiqPay:
    def __init__(self, public_key, private_key):
        self.public_key = public_key
        self.private_key = private_key

    def _prepare_params(self, params):
        """
        Добавляет public_key к параметрам.
        Исходный словарь не изменяется.
        """
        prepared = params.copy()
        prepared["public_key"] = self.public_key
        return prepared

    def cnb_data(self, params):
        """
        Формирует Base64-строку с JSON-параметрами платежа.
        """
        prepared = self._prepare_params(params)

        json_string = json.dumps(
            prepared,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return base64.b64encode(
            json_string.encode("utf-8")
        ).decode("utf-8")

    def cnb_signature(self, params):
        """
        Формирует подпись данных платежа.
        """
        data = self.cnb_data(params)

        signature_string = (
            self.private_key
            + data
            + self.private_key
        )

        digest = hashlib.sha1(
            signature_string.encode("utf-8")
        ).digest()

        return base64.b64encode(digest).decode("utf-8")

    def decode_data_from_str(self, data):
        """
        Декодирует Base64 data, полученный от LiqPay.
        """
        decoded = base64.b64decode(data)

        return json.loads(
            decoded.decode("utf-8")
        )

    def callback_signature(self, data):
        signature_string = (
            self.private_key
            + data
            + self.private_key
        )

        digest = hashlib.sha1(
            signature_string.encode("utf-8")
        ).digest()

        return base64.b64encode(digest).decode("utf-8")