from datetime import datetime
from telethon import TelegramClient
from telethon.tl.functions.messages import SetTypingRequest
from telethon.tl.types import SendMessageTypingAction, SendMessageRecordAudioAction

from src.layer00_utils.logger import system_logger
from src.layer00_utils.watchdog.watchdog_decorator import watchdog_decorator
from src.layer00_utils.watchdog.watchdog import userbot_telethon_module
from src.layer02_sensors.telegram.shared_tools._helpers import clean_peer_id

@watchdog_decorator(userbot_telethon_module)
async def tg_send_message(client: TelegramClient, chat_id: str | int, text: str, topic_id: int = None, silent: bool = False, schedule_date: datetime = None) -> str:
    """Отправляет сообщение и помечает чат прочитанным"""
    chat_id = clean_peer_id(chat_id)
    try:
        msg = await client.send_message(chat_id, text, reply_to=topic_id, silent=silent, schedule=schedule_date)
        
        # Если сообщение отложенное, не помечаем чат прочитанным
        if not schedule_date:
            await client.send_read_acknowledge(chat_id)
            await client.send_read_acknowledge(chat_id, clear_mentions=True)
            return f"Сообщение успешно отправлено. ID: {msg.id}"
        else:
            return "Сообщение успешно добавлено в отложенные."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка отправки сообщения в {chat_id}: {e}")
        return f"Ошибка отправки: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_reply_to_message(client: TelegramClient, chat_id: str | int, message_id: int, text: str) -> str:
    """Отвечает на конкретное сообщение и помечает чат прочитанным"""
    chat_id = clean_peer_id(chat_id)
    try:
        await client.send_message(chat_id, text, reply_to=message_id)
        await client.send_read_acknowledge(chat_id) 
        await client.send_read_acknowledge(chat_id, clear_mentions=True)
        return "Ответ успешно отправлен."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка ответа на сообщение {message_id} в {chat_id}: {e}")
        return f"Ошибка ответа: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_delete_message(client: TelegramClient, chat_id: str | int, message_id: int) -> str:
    """Удаляет сообщение"""
    chat_id = clean_peer_id(chat_id)
    try:
        await client.delete_messages(chat_id, [message_id])
        return f"Сообщение ID {message_id} успешно удалено."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка удаления сообщения {message_id}: {e}")
        return f"Ошибка при удалении сообщения: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_forward_message(client: TelegramClient, from_chat: str | int, message_id: int, to_chat: str | int) -> str:
    """Пересылает сообщение из одного чата в другой"""
    from_chat = clean_peer_id(from_chat)
    to_chat = clean_peer_id(to_chat)
    try:
        msg = await client.forward_messages(to_chat, messages=message_id, from_peer=from_chat)
        return f"Сообщение успешно переслано. Новый ID в целевом чате: {msg.id}"
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка пересылки сообщения {message_id}: {e}")
        return f"Ошибка при пересылке: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_edit_message(client: TelegramClient, chat_id: str | int, message_id: int, new_text: str) -> str:
    """Редактирует сообщение/пост"""
    chat_id = clean_peer_id(chat_id)
    try:
        await client.edit_message(chat_id, message_id, new_text)
        return f"Сообщение ID {message_id} успешно отредактировано."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка редактирования сообщения {message_id}: {e}")
        return f"Ошибка редактирования: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_pin_message(client: TelegramClient, chat_id: str | int, message_id: int) -> str:
    """Закрепляет сообщение в чате/канале"""
    chat_id = clean_peer_id(chat_id)
    try:
        await client.pin_message(chat_id, message_id, notify=True)
        return f"Сообщение ID {message_id} успешно закреплено."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка закрепления сообщения {message_id}: {e}")
        return f"Ошибка закрепления: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_set_typing_status(client: TelegramClient, chat_id: str | int, action: str = "typing") -> str:
    """Отправляет статус 'Печатает...' или 'Записывает аудио...' (длится ~5 секунд)"""
    chat_id = clean_peer_id(chat_id)
    try:
        peer = await client.get_input_entity(chat_id)
        typing_action = SendMessageRecordAudioAction() if action == "record-audio" else SendMessageTypingAction()
        await client(SetTypingRequest(peer=peer, action=typing_action))
        return f"Статус '{action}' успешно отправлен в чат."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка статуса печатает в {chat_id}: {e}")
        return f"Ошибка отправки статуса: {e}"