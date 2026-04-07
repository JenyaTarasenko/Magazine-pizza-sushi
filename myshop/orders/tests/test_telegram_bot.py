import pytest
from unittest.mock import patch, MagicMock
import requests


@pytest.fixture
def mock_settings():
    """Мок настроек для Telegram"""
    with patch('orders.telegram_bot.settings') as mock:
        mock.TELEGRAM_BOT_TOKEN = 'test_token_123'
        mock.TELEGRAM_CHAT_ID = 'test_chat_456'
        yield mock


class TestSendTelegramMessage:
    """Тесты для функции send_telegram_message"""

    def test_send_message_success(self, mock_settings):
        """Тест успешной отправки сообщения"""
        from orders.telegram_bot import send_telegram_message
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        
        with patch('orders.telegram_bot.requests.post') as mock_post:
            mock_post.return_value = mock_response

            result = send_telegram_message("Test message")

            assert result is True
            mock_post.assert_called_once()

    def test_send_message_payload_format(self, mock_settings):
        """Тест формата payload"""
        from orders.telegram_bot import send_telegram_message
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        
        with patch('orders.telegram_bot.requests.post') as mock_post:
            mock_post.return_value = mock_response

            test_message = "Test notification"
            send_telegram_message(test_message)

            call_args = mock_post.call_args
            payload = call_args[1]['data']
            assert 'text' in payload
            assert payload['text'] == test_message
            assert 'parse_mode' in payload
            assert payload['parse_mode'] == 'HTML'

    def test_send_message_empty_string(self, mock_settings):
        """Тест отправки пустой строки"""
        from orders.telegram_bot import send_telegram_message
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        
        with patch('orders.telegram_bot.requests.post') as mock_post:
            mock_post.return_value = mock_response

            result = send_telegram_message("")

            assert result is True

    def test_send_message_with_html_tags(self, mock_settings):
        """Тест сообщения с HTML тегами"""
        from orders.telegram_bot import send_telegram_message
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        
        with patch('orders.telegram_bot.requests.post') as mock_post:
            mock_post.return_value = mock_response

            html_message = "<b>Жирный</b> и <i>курсив</i>"
            result = send_telegram_message(html_message)

            assert result is True

    def test_send_message_with_emoji(self, mock_settings):
        """Тест сообщения с эмодзи"""
        from orders.telegram_bot import send_telegram_message
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        
        with patch('orders.telegram_bot.requests.post') as mock_post:
            mock_post.return_value = mock_response

            emoji_message = "✅ Новый заказ!"
            result = send_telegram_message(emoji_message)

            assert result is True

    def test_send_message_with_unicode(self, mock_settings):
        """Тест сообщения с unicode символами"""
        from orders.telegram_bot import send_telegram_message
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        
        with patch('orders.telegram_bot.requests.post') as mock_post:
            mock_post.return_value = mock_response

            unicode_message = "Заказ №123 - Оплачен"
            result = send_telegram_message(unicode_message)

            assert result is True

    def test_send_message_long_text(self, mock_settings):
        """Тест длинного сообщения"""
        from orders.telegram_bot import send_telegram_message
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        
        with patch('orders.telegram_bot.requests.post') as mock_post:
            mock_post.return_value = mock_response

            long_message = "A" * 1000
            result = send_telegram_message(long_message)

            assert result is True


class TestSendTelegramMessageErrors:
    """Тесты обработки ошибок"""

    def test_send_message_connection_error(self, mock_settings):
        """Тест ошибки соединения"""
        from orders.telegram_bot import send_telegram_message
        
        with patch('orders.telegram_bot.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

            result = send_telegram_message("Test message")

            assert result is False

    def test_send_message_timeout(self, mock_settings):
        """Тест таймаута"""
        from orders.telegram_bot import send_telegram_message
        
        with patch('orders.telegram_bot.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

            result = send_telegram_message("Test message")

            assert result is False

    def test_send_message_http_error(self, mock_settings):
        """Тест HTTP ошибки"""
        from orders.telegram_bot import send_telegram_message
        
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Bad Request")
        
        with patch('orders.telegram_bot.requests.post') as mock_post:
            mock_post.return_value = mock_response

            result = send_telegram_message("Test message")

            assert result is False

    def test_send_message_api_error(self, mock_settings):
        """Тест ошибки API Telegram"""
        from orders.telegram_bot import send_telegram_message
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': False, 'error': 'Bot was blocked by the user'}
        
        with patch('orders.telegram_bot.requests.post') as mock_post:
            mock_post.return_value = mock_response

            result = send_telegram_message("Test message")

            assert result is False

    def test_send_message_multiple_calls(self, mock_settings):
        """Тест нескольких последовательных вызовов"""
        from orders.telegram_bot import send_telegram_message
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        
        with patch('orders.telegram_bot.requests.post') as mock_post:
            mock_post.return_value = mock_response

            for i in range(5):
                result = send_telegram_message(f"Message {i}")
                assert result is True

            assert mock_post.call_count == 5


class TestSendTelegramMessageConfiguration:
    """Тесты конфигурации"""

    def test_missing_token_returns_false(self):
        """Тест что отсутствие токена возвращает False"""
        from orders.telegram_bot import send_telegram_message
        
        with patch('orders.telegram_bot.settings') as mock_settings:
            mock_settings.TELEGRAM_BOT_TOKEN = None
            mock_settings.TELEGRAM_CHAT_ID = '123456'

            result = send_telegram_message("Test")

            assert result is False

    def test_missing_chat_id_returns_false(self):
        """Тест что отсутствие chat_id возвращает False"""
        from orders.telegram_bot import send_telegram_message
        
        with patch('orders.telegram_bot.settings') as mock_settings:
            mock_settings.TELEGRAM_BOT_TOKEN = 'token'
            mock_settings.TELEGRAM_CHAT_ID = None

            result = send_telegram_message("Test")

            assert result is False

    def test_empty_credentials_returns_false(self):
        """Тест что пустые credentials возвращают False"""
        from orders.telegram_bot import send_telegram_message
        
        with patch('orders.telegram_bot.settings') as mock_settings:
            mock_settings.TELEGRAM_BOT_TOKEN = ''
            mock_settings.TELEGRAM_CHAT_ID = ''

            result = send_telegram_message("Test")

            assert result is False

    def test_uses_correct_api_url(self, mock_settings):
        """Тест использования правильного API URL"""
        from orders.telegram_bot import send_telegram_message
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        
        with patch('orders.telegram_bot.requests.post') as mock_post:
            mock_post.return_value = mock_response

            send_telegram_message("Test")

            call_args = mock_post.call_args
            url = call_args[0][0]
            assert 'api.telegram.org' in url
            assert 'test_token_123' in url
            assert 'sendMessage' in url


class TestSendTelegramMessageIntegration:
    """Интеграционные тесты"""

    def test_order_notification_format(self, mock_settings):
        """Тест формата уведомления о заказе"""
        from orders.telegram_bot import send_telegram_message
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        
        with patch('orders.telegram_bot.requests.post') as mock_post:
            mock_post.return_value = mock_response

            order_message = """✅ <b>Новый оплаченный заказ!</b>

📦 Заказ №123
👤 Имя: Иван Иванов
📧 Email: test@example.com
💰 Сумма: 500 UAH"""

            result = send_telegram_message(order_message)

            assert result is True
            call_args = mock_post.call_args
            payload = call_args[1]['data']
            assert 'Заказ №123' in payload['text']
            assert 'Иван Иванов' in payload['text']
