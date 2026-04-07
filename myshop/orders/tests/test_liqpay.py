import pytest
import base64
import json
import hashlib
from decimal import Decimal

from orders.liqpay import LiqPay


class TestLiqPayInit:
    """Тесты инициализации класса LiqPay"""

    def test_init_with_keys(self, liqpay):
        """Тест инициализации с ключами"""
        assert liqpay.public_key == 'test_public_key'
        assert liqpay.private_key == 'test_private_key'

    def test_init_different_keys(self):
        """Тест разных ключей"""
        lp = LiqPay('pub_123', 'priv_456')
        assert lp.public_key == 'pub_123'
        assert lp.private_key == 'priv_456'

    def test_init_empty_strings(self):
        """Тест пустых строк"""
        lp = LiqPay('', '')
        assert lp.public_key == ''
        assert lp.private_key == ''


class TestLiqPayCnbData:
    """Тесты метода cnb_data"""

    def test_cnb_data_basic(self, liqpay):
        """Тест базового шифрования данных"""
        params = {
            'amount': '100.00',
            'currency': 'UAH',
            'description': 'Test payment'
        }
        data = liqpay.cnb_data(params)
        assert data is not None
        assert isinstance(data, str)

    def test_cnb_data_is_base64(self, liqpay):
        """Тест что результат - валидный base64"""
        params = {'amount': '100', 'currency': 'UAH'}
        data = liqpay.cnb_data(params)
        decoded = base64.b64decode(data)
        assert isinstance(decoded, bytes)

    def test_cnb_data_contains_public_key(self, liqpay):
        """Тест что public_key добавлен в данные"""
        params = {'amount': '100'}
        data = liqpay.cnb_data(params)
        decoded = json.loads(base64.b64decode(data).decode('utf-8'))
        assert 'public_key' in decoded
        assert decoded['public_key'] == 'test_public_key'

    def test_cnb_data_preserves_original_params(self, liqpay):
        """Тест что оригинальные параметры сохранены"""
        params = {
            'amount': '250.50',
            'currency': 'UAH',
            'description': 'Оплата заказа'
        }
        data = liqpay.cnb_data(params)
        decoded = json.loads(base64.b64decode(data).decode('utf-8'))
        assert decoded['amount'] == '250.50'
        assert decoded['currency'] == 'UAH'
        assert decoded['description'] == 'Оплата заказа'

    def test_cnb_data_json_format(self, liqpay):
        """Тест компактного JSON формата (без пробелов)"""
        params = {'key': 'value', 'number': 123}
        data = liqpay.cnb_data(params)
        decoded = base64.b64decode(data).decode('utf-8')
        assert ' ' not in decoded
        assert '\n' not in decoded

    def test_cnb_data_unicode(self, liqpay):
        """Тест с unicode символами"""
        params = {
            'description': 'Оплата заказа №123'
        }
        data = liqpay.cnb_data(params)
        decoded = json.loads(base64.b64decode(data).decode('utf-8'))
        assert 'Оплата заказа №123' in decoded['description']

    def test_cnb_data_empty_params(self, liqpay):
        """Тест с пустыми параметрами"""
        params = {}
        data = liqpay.cnb_data(params)
        decoded = json.loads(base64.b64decode(data).decode('utf-8'))
        assert 'public_key' in decoded

    def test_cnb_data_cyrillic_in_params(self, liqpay):
        """Тест кириллицы в параметрах"""
        params = {
            'description': 'Тест кириллица: Привет мир',
            'name': 'Иван'
        }
        data = liqpay.cnb_data(params)
        decoded = json.loads(base64.b64decode(data).decode('utf-8'))
        assert 'Тест кириллица: Привет мир' in decoded['description']

    def test_cnb_data_different_key(self):
        """Тест с другим публичным ключом"""
        lp = LiqPay('another_public_key_123', 'another_private_key_456')
        params = {'amount': '100'}
        data = lp.cnb_data(params)
        decoded = json.loads(base64.b64decode(data).decode('utf-8'))
        assert decoded['public_key'] == 'another_public_key_123'


class TestLiqPayCnbSignature:
    """Тесты метода cnb_signature"""

    def test_cnb_signature_returns_string(self, liqpay):
        """Тест что подпись - строка"""
        data = 'test_data_string'
        signature = liqpay.cnb_signature(data)
        assert isinstance(signature, str)

    def test_cnb_signature_is_base64(self, liqpay):
        """Тест что подпись - валидный base64"""
        data = 'some_data'
        signature = liqpay.cnb_signature(data)
        decoded = base64.b64decode(signature)
        assert isinstance(decoded, bytes)

    def test_cnb_signature_length(self, liqpay):
        """Тест длины подписи (sha1 = 20 байт, base64 ~27 символов)"""
        data = 'test'
        signature = liqpay.cnb_signature(data)
        decoded = base64.b64decode(signature)
        assert len(decoded) == 20  # SHA1 produces 20 bytes

    def test_cnb_signature_deterministic(self, liqpay):
        """Тест детерминированности подписи"""
        data = 'consistent_data'
        sig1 = liqpay.cnb_signature(data)
        sig2 = liqpay.cnb_signature(data)
        assert sig1 == sig2

    def test_cnb_signature_different_data(self, liqpay):
        """Тест разных подписей для разных данных"""
        sig1 = liqpay.cnb_signature('data1')
        sig2 = liqpay.cnb_signature('data2')
        assert sig1 != sig2

    def test_cnb_signature_empty_data(self, liqpay):
        """Тест подписи пустых данных"""
        signature = liqpay.cnb_signature('')
        assert isinstance(signature, str)
        assert len(signature) > 0

    def test_cnb_signature_uses_private_key(self):
        """Тест что подпись зависит от private_key"""
        lp1 = LiqPay('pub', 'private1')
        lp2 = LiqPay('pub', 'private2')
        data = 'same_data'
        sig1 = lp1.cnb_signature(data)
        sig2 = lp2.cnb_signature(data)
        assert sig1 != sig2

    def test_cnb_signature_unicode_data(self, liqpay):
        """Тест подписи с unicode данными"""
        data = 'Данные на кириллице'
        signature = liqpay.cnb_signature(data)
        assert isinstance(signature, str)
        assert len(signature) > 0


class TestLiqPayDecodeData:
    """Тесты метода decode_data_from_str"""

    def test_decode_valid_data(self, liqpay):
        """Тест декодирования валидных данных"""
        params = {'key': 'value', 'number': 123}
        encoded = liqpay.cnb_data(params)
        decoded = liqpay.decode_data_from_str(encoded)
        assert decoded['key'] == 'value'
        assert decoded['number'] == 123

    def test_decode_roundtrip(self, liqpay):
        """Тест что encode -> decode возвращает исходные данные"""
        original = {
            'amount': '150.50',
            'currency': 'UAH',
            'order_id': '12345',
            'status': 'success'
        }
        encoded = liqpay.cnb_data(original)
        decoded = liqpay.decode_data_from_str(encoded)
        assert decoded['amount'] == original['amount']
        assert decoded['currency'] == original['currency']
        assert decoded['order_id'] == original['order_id']

    def test_decode_cyrillic(self, liqpay):
        """Тест декодирования кириллицы"""
        params = {'description': 'Тест'}
        encoded = liqpay.cnb_data(params)
        decoded = liqpay.decode_data_from_str(encoded)
        assert decoded['description'] == 'Тест'

    def test_decode_invalid_base64(self, liqpay):
        """Тест ошибки при некорректном base64"""
        with pytest.raises(Exception):
            liqpay.decode_data_from_str('not_valid_base64!!!')

    def test_decode_empty_string(self, liqpay):
        """Тест декодирования пустой строки"""
        with pytest.raises(Exception):
            liqpay.decode_data_from_str('')

    def test_decode_special_chars(self, liqpay):
        """Тест специальных символов"""
        params = {'text': 'Test <>&"\\ chars'}
        encoded = liqpay.cnb_data(params)
        decoded = liqpay.decode_data_from_str(encoded)
        assert decoded['text'] == 'Test <>&"\\ chars'


class TestLiqPaySignatureAlgorithm:
    """Тесты алгоритма подписи"""

    def test_signature_algorithm(self, liqpay):
        """Тест формулы: base64(sha1(private + data + private))"""
        private = 'test_key'
        data = 'test_data'
        expected = base64.b64encode(
            hashlib.sha1(f"{private}{data}{private}".encode()).digest()
        ).decode()
        lp = LiqPay('pub', private)
        result = lp.cnb_signature(data)
        assert result == expected

    def test_signature_matches_manual_calculation(self):
        """Тест соответствия ручному расчёту"""
        private = 'secret123'
        public = 'public456'
        lp = LiqPay(public, private)
        data = 'payment_data'
        
        expected_signature = base64.b64encode(
            hashlib.sha1(f"{private}{data}{private}".encode()).digest()
        ).decode()
        
        actual_signature = lp.cnb_signature(data)
        assert actual_signature == expected_signature


class TestLiqPayIntegration:
    """Интеграционные тесты LiqPay"""

    def test_full_payment_flow(self, liqpay):
        """Тест полного процесса создания платежа"""
        params = {
            'action': 'pay',
            'amount': '100.00',
            'currency': 'UAH',
            'description': 'Test order',
            'order_id': '123'
        }
        
        data = liqpay.cnb_data(params)
        signature = liqpay.cnb_signature(data)
        
        assert data is not None
        assert signature is not None
        assert len(signature) > 0

    def test_payment_data_structure(self, liqpay):
        """Тест структуры данных платежа"""
        params = {
            'action': 'pay',
            'amount': str(Decimal('250.50')),
            'currency': 'UAH',
            'description': f'Оплата заказа №{123}',
            'order_id': str(123),
            'version': '3',
            'sandbox': 1
        }
        
        data = liqpay.cnb_data(params)
        decoded = liqpay.decode_data_from_str(data)
        
        assert decoded['action'] == 'pay'
        assert decoded['amount'] == '250.50'
        assert decoded['currency'] == 'UAH'
        assert decoded['public_key'] == 'test_public_key'

    def test_multiple_payments_different_orders(self, liqpay):
        """Тест нескольких платежей для разных заказов"""
        orders = [
            {'order_id': '1', 'amount': '100'},
            {'order_id': '2', 'amount': '200'},
            {'order_id': '3', 'amount': '300'},
        ]
        
        signatures = []
        for order in orders:
            params = {'action': 'pay', 'amount': order['amount']}
            data = liqpay.cnb_data(params)
            sig = liqpay.cnb_signature(data)
            signatures.append(sig)
        
        assert len(set(signatures)) == 3

    def test_same_order_different_keys(self):
        """Тест разных подписей при разных ключах"""
        lp1 = LiqPay('pub1', 'priv1')
        lp2 = LiqPay('pub2', 'priv2')
        
        params = {'amount': '100'}
        data1 = lp1.cnb_data(params)
        data2 = lp2.cnb_data(params)
        
        sig1 = lp1.cnb_signature(data1)
        sig2 = lp2.cnb_signature(data2)
        
        assert sig1 != sig2
        assert data1 != data2


class TestLiqPayEdgeCases:
    """Граничные случаи"""

    def test_very_long_description(self, liqpay):
        """Тест очень длинного описания"""
        params = {
            'description': 'A' * 1000
        }
        data = liqpay.cnb_data(params)
        decoded = liqpay.decode_data_from_str(data)
        assert len(decoded['description']) == 1000

    def test_decimal_amount(self, liqpay):
        """Тест десятичных сумм"""
        params = {
            'amount': '99.99'
        }
        data = liqpay.cnb_data(params)
        decoded = liqpay.decode_data_from_str(data)
        assert decoded['amount'] == '99.99'

    def test_integer_amount(self, liqpay):
        """Тест целочисленных сумм"""
        params = {
            'amount': '100'
        }
        data = liqpay.cnb_data(params)
        decoded = liqpay.decode_data_from_str(data)
        assert decoded['amount'] == '100'

    def test_special_unicode_chars(self, liqpay):
        """Тест специальных unicode символов"""
        params = {
            'description': 'Emoji: 🍕 test & symbols: @#$%'
        }
        data = liqpay.cnb_data(params)
        decoded = liqpay.decode_data_from_str(data)
        assert '🍕' in decoded['description']

    def test_json_boolean_values(self, liqpay):
        """Тест JSON boolean значений"""
        params = {
            'sandbox': True,
            'auto': False
        }
        data = liqpay.cnb_data(params)
        decoded = liqpay.decode_data_from_str(data)
        assert decoded['sandbox'] is True
        assert decoded['auto'] is False

    def test_json_null_values(self, liqpay):
        """Тест JSON null значений"""
        params = {
            'description': None
        }
        data = liqpay.cnb_data(params)
        decoded = liqpay.decode_data_from_str(data)
        assert decoded['description'] is None

    def test_signature_with_very_long_data(self, liqpay):
        """Тест подписи очень длинных данных"""
        data = 'x' * 10000
        signature = liqpay.cnb_signature(data)
        assert len(signature) > 0

    def test_cyrillic_in_all_fields(self, liqpay):
        """Тест кириллицы во всех полях"""
        params = {
            'description': 'Описание товара',
            'order_id': '123',
            'amount': '100',
            'currency': 'UAH'
        }
        data = liqpay.cnb_data(params)
        decoded = liqpay.decode_data_from_str(data)
        assert decoded['description'] == 'Описание товара'


class TestLiqPaySecurity:
    """Тесты безопасности"""

    def test_different_private_keys_different_signatures(self):
        """Тест что разные ключи дают разные подписи"""
        base_data = 'test_payment_data'
        signatures = []
        for i in range(5):
            lp = LiqPay('pub', f'private_key_{i}')
            signatures.append(lp.cnb_signature(base_data))
        assert len(set(signatures)) == 5

    def test_signature_length_consistency(self, liqpay):
        """Тест постоянства длины подписи"""
        test_data = [
            'a', 'ab', 'abc', 'test', 
            'longer string here', 'x' * 1000
        ]
        lengths = [len(liqpay.cnb_signature(d)) for d in test_data]
        assert len(set(lengths)) == 1  # Все одной длины

    def test_cnb_data_contains_no_private_key(self, liqpay):
        """Тест что private_key не попадает в data"""
        params = {'amount': '100'}
        data = liqpay.cnb_data(params)
        decoded = base64.b64decode(data).decode('utf-8')
        assert 'private' not in decoded.lower()
        assert liqpay.private_key not in decoded
