# Файл: src/layer02_sensors/telegram/shared_tools/account.py

import os
from telethon import TelegramClient
from telethon.tl.functions.account import UpdateProfileRequest, UpdateUsernameRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest
from telethon.tl.functions.contacts import AddContactRequest

from src.layer00_utils.logger import system_logger
from src.layer00_utils.watchdog.watchdog_decorator import watchdog_decorator
from src.layer00_utils.watchdog.watchdog import userbot_telethon_module
from src.layer02_sensors.telegram.shared_tools._helpers import clean_peer_id

@watchdog_decorator(userbot_telethon_module)
async def tg_change_bio(client: TelegramClient, new_bio: str) -> str:
    """Меняет раздел 'О себе' в профиле"""
    try:
        if len(new_bio) > 70:
            return f"Ошибка: Bio слишком длинное ({len(new_bio)} символов). Максимум 70."
        await client(UpdateProfileRequest(about=new_bio))
        return f"Статус (Bio) успешно изменен на: '{new_bio}'"
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка смены Bio: {e}")
        return f"Ошибка смены Bio: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_change_avatar(client: TelegramClient, image_path: str) -> str:
    """Меняет аватарку профиля"""
    try:
        if not os.path.exists(image_path):
            return f"Ошибка: Файл '{image_path}' не найден."
        file = await client.upload_file(image_path)
        await client(UploadProfilePhotoRequest(file=file))
        return "Аватарка профиля успешно обновлена."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка смены аватарки профиля: {e}")
        return f"Ошибка при обновлении аватарки: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_change_account_name(client: TelegramClient, first_name: str, last_name: str = "") -> str:
    """Меняет имя и фамилию профиля"""
    try:
        await client(UpdateProfileRequest(first_name=first_name, last_name=last_name))
        return f"Имя профиля успешно изменено на: {first_name} {last_name}"
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка смены имени: {e}")
        return f"Ошибка при смене имени: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_change_account_username(client: TelegramClient, username: str) -> str:
    """Меняет @username профиля"""
    try:
        clean_username = username.replace("@", "")
        await client(UpdateUsernameRequest(username=clean_username))
        return f"Юзернейм успешно изменен на: @{clean_username}"
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка смены юзернейма: {e}")
        return f"Ошибка при смене юзернейма: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_add_to_contacts(client: TelegramClient, user_id: str | int, first_name: str, last_name: str = "") -> str:
    """Добавляет пользователя в контакты аккаунта"""
    user_id = clean_peer_id(user_id)
    try:
        user_entity = await client.get_input_entity(user_id)
        
        await client(AddContactRequest(
            id=user_entity, first_name=first_name, last_name=last_name,
            phone="", add_phone_privacy_exception=False
        ))
        
        return f"Пользователь {user_id} добавлен в контакты как '{first_name} {last_name}'."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка добавления в контакты {user_id}: {e}")
        return f"Ошибка при добавлении в контакты: {e}"