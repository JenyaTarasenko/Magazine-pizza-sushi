import base64
import json
import hashlib


class LiqPay:
    def __init__(self, public_key, private_key):
        self.public_key = public_key
        self.private_key = private_key

    def cnb_data(self, params):
        params["public_key"] = self.public_key
        json_string = json.dumps(params, separators=(',', ':'))
        return base64.b64encode(json_string.encode("utf-8")).decode("utf-8")
        # json_string = json.dumps(params)
        # return base64.b64encode(json_string.encode("utf-8")).decode("utf-8")

    # def cnb_signature(self, params):
    #     data = self.cnb_data(params)
    #     signature_str = self.private_key + data + self.private_key
    #     return base64.b64encode(
    #         hashlib.sha1(signature_str.encode("utf-8")).digest()
    #     ).decode("utf-8")
    def cnb_signature(self, data):
        # Подпись = base64(sha1(private_key + data + private_key))
        joined_row = self.private_key + data + self.private_key
        sha1_hash = hashlib.sha1(joined_row.encode("utf-8")).digest()
        return base64.b64encode(sha1_hash).decode("utf-8")

    def decode_data_from_str(self, data):
        decoded = base64.b64decode(data)
        return json.loads(decoded.decode("utf-8"))