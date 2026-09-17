import base64
import hashlib
import json
import unittest

from orders.liqpay import LiqPay


class TestLiqPayInit(unittest.TestCase):
    """Тесты __init__"""

    def test_init_stores_keys(self):
        """public_key и private_key сохраняются при инициализации"""
        lp = LiqPay('pub_key', 'priv_key')
        self.assertEqual(lp.public_key, 'pub_key')
        self.assertEqual(lp.private_key, 'priv_key')

    def test_init_different_keys(self):
        """Значения ключей сохраняются как есть"""
        lp = LiqPay('public_123', 'private_456')
        self.assertEqual(lp.public_key, 'public_123')
        self.assertEqual(lp.private_key, 'private_456')

    def test_init_empty_strings(self):
        """Пустые строки допустимы"""
        lp = LiqPay('', '')
        self.assertEqual(lp.public_key, '')
        self.assertEqual(lp.private_key, '')


class TestLiqPayPrepareParams(unittest.TestCase):
    """Тесты _prepare_params"""

    def test_prepare_adds_public_key(self):
        """_prepare_params добавляет public_key в параметры"""
        lp = LiqPay('pk_1', 'sk_1')
        result = lp._prepare_params({'amount': '100'})
        self.assertIn('public_key', result)
        self.assertEqual(result['public_key'], 'pk_1')

    def test_prepare_keeps_original_params(self):
        """_prepare_params сохраняет исходные параметры"""
        lp = LiqPay('pk_1', 'sk_1')
        result = lp._prepare_params({'amount': '100', 'currency': 'UAH'})
        self.assertEqual(result['amount'], '100')
        self.assertEqual(result['currency'], 'UAH')

    def test_prepare_does_not_modify_original(self):
        """_prepare_params не изменяет исходный словарь"""
        lp = LiqPay('pk_1', 'sk_1')
        params = {'amount': '100', 'currency': 'UAH'}
        original = dict(params)
        lp._prepare_params(params)
        self.assertEqual(params, original)
        self.assertNotIn('public_key', params)

    def test_prepare_returns_copy(self):
        """_prepare_params возвращает копию, а не исходный словарь"""
        lp = LiqPay('pk_1', 'sk_1')
        params = {'amount': '100'}
        result = lp._prepare_params(params)
        self.assertIsNot(result, params)


class TestLiqPayCnbData(unittest.TestCase):
    """Тесты cnb_data"""

    def setUp(self):
        self.lp = LiqPay('test_public_key', 'test_private_key')

    def test_cnb_data_returns_string(self):
        """cnb_data возвращает строку"""
        data = self.lp.cnb_data({'amount': '100'})
        self.assertIsInstance(data, str)

    def test_cnb_data_is_base64(self):
        """Результат cnb_data - валидная Base64 строка"""
        data = self.lp.cnb_data({'amount': '100'})
        decoded = base64.b64decode(data)
        self.assertIsInstance(decoded, bytes)

    def test_cnb_data_decodes_to_json(self):
        """Base64 содержит валидный JSON"""
        data = self.lp.cnb_data({'amount': '100'})
        decoded = json.loads(base64.b64decode(data).decode('utf-8'))
        self.assertIsInstance(decoded, dict)

    def test_cnb_data_adds_public_key(self):
        """cnb_data добавляет public_key внутрь данных"""
        data = self.lp.cnb_data({'amount': '100'})
        decoded = json.loads(base64.b64decode(data).decode('utf-8'))
        self.assertIn('public_key', decoded)
        self.assertEqual(decoded['public_key'], 'test_public_key')

    def test_cnb_data_adds_actual_public_key(self):
        """Добавляется именно public_key текущего экземпляра"""
        lp = LiqPay('another_key', 'sk')
        data = lp.cnb_data({'amount': '100'})
        decoded = json.loads(base64.b64decode(data).decode('utf-8'))
        self.assertEqual(decoded['public_key'], 'another_key')

    def test_cnb_data_preserves_params(self):
        """Все исходные параметры сохраняются в данных"""
        params = {
            'amount': '250.50',
            'currency': 'UAH',
            'description': 'Оплата заказа',
        }
        data = self.lp.cnb_data(params)
        decoded = json.loads(base64.b64decode(data).decode('utf-8'))
        self.assertEqual(decoded['amount'], '250.50')
        self.assertEqual(decoded['currency'], 'UAH')
        self.assertEqual(decoded['description'], 'Оплата заказа')

    def test_cnb_data_does_not_modify_original(self):
        """cnb_data не изменяет исходный словарь"""
        params = {'amount': '100', 'currency': 'UAH'}
        original = dict(params)
        self.lp.cnb_data(params)
        self.assertEqual(params, original)
        self.assertNotIn('public_key', params)

    def test_cnb_data_compact_json(self):
        """JSON компактный: без пробелов и переводов строк"""
        data = self.lp.cnb_data({'key': 'value', 'number': 123})
        raw = base64.b64decode(data).decode('utf-8')
        self.assertNotIn(' ', raw)
        self.assertNotIn('\n', raw)

    def test_cnb_data_unicode_cyrillic(self):
        """Кириллица и unicode сохраняются корректно"""
        params = {'description': 'Оплата заказа №123'}
        data = self.lp.cnb_data(params)
        decoded = json.loads(base64.b64decode(data).decode('utf-8'))
        self.assertEqual(decoded['description'], 'Оплата заказа №123')

    def test_cnb_data_empty_params(self):
        """Пустой словарь - данные содержат только public_key"""
        data = self.lp.cnb_data({})
        decoded = json.loads(base64.b64decode(data).decode('utf-8'))
        self.assertEqual(decoded, {'public_key': 'test_public_key'})


class TestLiqPayCnbSignature(unittest.TestCase):
    """Тесты cnb_signature"""

    def setUp(self):
        self.lp = LiqPay('pub', 'private_key')

    def test_cnb_signature_returns_string(self):
        """cnb_signature принимает params и возвращает строку"""
        sig = self.lp.cnb_signature({'amount': '100'})
        self.assertIsInstance(sig, str)

    def test_cnb_signature_is_base64_of_sha1(self):
        """Подпись - Base64 от SHA1 (20 байт)"""
        sig = self.lp.cnb_signature({'amount': '100'})
        digest = base64.b64decode(sig)
        self.assertEqual(len(digest), 20)

    def test_cnb_signature_same_for_same_params(self):
        """Одинаковые параметры дают одинаковую подпись"""
        params = {'amount': '100', 'currency': 'UAH'}
        sig1 = self.lp.cnb_signature(params)
        sig2 = self.lp.cnb_signature({'amount': '100', 'currency': 'UAH'})
        self.assertEqual(sig1, sig2)

    def test_cnb_signature_differs_on_data_change(self):
        """Изменение данных меняет подпись"""
        sig1 = self.lp.cnb_signature({'amount': '100', 'currency': 'UAH'})
        sig2 = self.lp.cnb_signature({'amount': '150', 'currency': 'UAH'})
        self.assertNotEqual(sig1, sig2)

    def test_cnb_signature_differs_on_public_key(self):
        """Изменение public_key меняет подпись (меняет data)"""
        lp2 = LiqPay('other_pub', 'private_key')
        sig1 = self.lp.cnb_signature({'amount': '100'})
        sig2 = lp2.cnb_signature({'amount': '100'})
        self.assertNotEqual(sig1, sig2)

    def test_cnb_signature_differs_on_private_key(self):
        """Изменение private_key меняет подпись"""
        lp2 = LiqPay('pub', 'other_private_key')
        params = {'amount': '100'}
        sig1 = self.lp.cnb_signature(params)
        sig2 = lp2.cnb_signature(dict(params))
        self.assertNotEqual(sig1, sig2)

    def test_cnb_signature_algorithm(self):
        """Формула: base64(sha1(private_key + data + private_key))"""
        params = {'amount': '100', 'currency': 'UAH'}
        data = self.lp.cnb_data(params)
        expected = base64.b64encode(
            hashlib.sha1(
                ('private_key' + data + 'private_key').encode('utf-8')
            ).digest()
        ).decode('utf-8')
        self.assertEqual(self.lp.cnb_signature(params), expected)

    def test_cnb_signature_uses_base64_data_not_json(self):
        """Подпись строится по base64 data, а не по исходному JSON"""
        params = {'amount': '100'}
        data = self.lp.cnb_data(params)
        json_str = json.dumps(
            {'amount': '100', 'public_key': 'pub'},
            separators=(',', ':'),
            ensure_ascii=False,
        )
        sig = self.lp.cnb_signature(params)
        sig_from_data = base64.b64encode(
            hashlib.sha1(
                ('private_key' + data + 'private_key').encode('utf-8')
            ).digest()
        ).decode('utf-8')
        sig_from_json = base64.b64encode(
            hashlib.sha1(
                ('private_key' + json_str + 'private_key').encode('utf-8')
            ).digest()
        ).decode('utf-8')
        self.assertEqual(sig, sig_from_data)
        self.assertNotEqual(sig, sig_from_json)


class TestLiqPayDecodeData(unittest.TestCase):
    """Тесты decode_data_from_str"""

    def setUp(self):
        self.lp = LiqPay('pub', 'priv')

    def test_decode_returns_dict(self):
        """decode_data_from_str возвращает словарь"""
        data = self.lp.cnb_data({'amount': '100'})
        result = self.lp.decode_data_from_str(data)
        self.assertIsInstance(result, dict)

    def test_decode_back_to_original(self):
        """decode возвращает исходные параметры + public_key"""
        params = {'amount': '150.50', 'currency': 'UAH', 'order_id': '12345'}
        data = self.lp.cnb_data(params)
        decoded = self.lp.decode_data_from_str(data)
        self.assertEqual(decoded['amount'], '150.50')
        self.assertEqual(decoded['currency'], 'UAH')
        self.assertEqual(decoded['order_id'], '12345')
        self.assertEqual(decoded['public_key'], 'pub')

    def test_decode_cyrillic(self):
        """Кириллица корректно декодируется"""
        data = self.lp.cnb_data({'description': 'Тест кириллица'})
        decoded = self.lp.decode_data_from_str(data)
        self.assertEqual(decoded['description'], 'Тест кириллица')

    def test_decode_invalid_base64_raises(self):
        """Некорректный Base64 вызывает ошибку"""
        with self.assertRaises(Exception):
            self.lp.decode_data_from_str('!!!not_base64!!!')

    def test_decode_empty_string_raises(self):
        """Пустая строка вызывает ошибку"""
        with self.assertRaises(Exception):
            self.lp.decode_data_from_str('')


class TestLiqPayRoundTrip(unittest.TestCase):
    """Полный round-trip: params -> data -> decode"""

    def setUp(self):
        self.lp = LiqPay('pk_roundtrip', 'sk_roundtrip')

    def test_full_round_trip(self):
        """params -> cnb_data -> decode возвращает params и public_key"""
        params = {
            'action': 'pay',
            'amount': '100.00',
            'currency': 'UAH',
            'description': 'Оплата заказа №5',
            'order_id': '5',
            'version': '3',
            'sandbox': 1,
        }
        original = dict(params)
        data = self.lp.cnb_data(params)
        decoded = self.lp.decode_data_from_str(data)
        for key, value in params.items():
            self.assertEqual(decoded[key], value)
        self.assertEqual(decoded['public_key'], 'pk_roundtrip')
        self.assertEqual(params, original)

    def test_round_trip_with_signature(self):
        """Полный поток: data + signature логически согласованы"""
        params = {'action': 'pay', 'amount': '99.99', 'currency': 'UAH'}
        data = self.lp.cnb_data(params)
        signature = self.lp.cnb_signature(params)

        expected_signature = base64.b64encode(
            hashlib.sha1(
                ('sk_roundtrip' + data + 'sk_roundtrip').encode('utf-8')
            ).digest()
        ).decode('utf-8')
        self.assertEqual(signature, expected_signature)

        decoded = self.lp.decode_data_from_str(data)
        self.assertEqual(decoded['amount'], '99.99')


if __name__ == '__main__':
    unittest.main()