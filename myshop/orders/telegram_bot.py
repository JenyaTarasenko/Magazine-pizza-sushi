# """
# Telegram Bot уведомления для заказов.
# """

# import logging
# import requests
# from django.conf import settings

# logger = logging.getLogger(__name__)


# def send_telegram_message(text):
#     """Отправляет сообщение в Telegram.
    
#     Args:
#         text: Текст сообщения (поддерживает HTML)
        
#     Returns:
#         bool: True если сообщение отправлено успешно, False иначе
#     """
#     bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
#     chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', None)
    
#     if not bot_token or not chat_id:
#         logger.warning("Telegram bot not configured: missing TOKEN or CHAT_ID")
#         return False
    
#     url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
#     payload = {
#         "chat_id": chat_id,
#         "text": text,
#         "parse_mode": "HTML"
#     }
    
#     try:
#         response = requests.post(url, data=payload, timeout=10)
#         response.raise_for_status()
        
#         result = response.json()
#         if result.get('ok'):
#             logger.info("Telegram message sent successfully")
#             return True
#         else:
#             logger.error(f"Telegram API error: {result}")
#             return False
            
#     except requests.exceptions.Timeout:
#         logger.error("Telegram request timeout")
#         return False
#     except requests.exceptions.ConnectionError as e:
#         logger.error(f"Telegram connection error: {e}")
#         return False
#     except requests.exceptions.HTTPError as e:
#         logger.error(f"Telegram HTTP error: {e}")
#         return False
#     except Exception as e:
#         logger.exception(f"Unexpected Telegram error: {e}")
#         return False

import requests
from django.conf import settings


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }

    requests.post(url, data=payload)
