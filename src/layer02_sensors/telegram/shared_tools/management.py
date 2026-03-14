import os
from telethon import TelegramClient, types, functions
from telethon.tl.functions.channels import EditBannedRequest, CreateChannelRequest, EditTitleRequest, EditAdminRequest, UpdateUsernameRequest, EditPhotoRequest
from telethon.tl.functions.contacts import BlockRequest, UnblockRequest, GetBlockedRequest
from telethon.tl.functions.messages import EditChatAboutRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantsKicked, ChannelParticipantsRecent, ChannelParticipantsSearch, ChatAdminRights, ChannelParticipantsAdmins

from src.layer00_utils.logger import system_logger
from src.layer00_utils.watchdog.watchdog_decorator import watchdog_decorator
from src.layer00_utils.watchdog.watchdog import userbot_telethon_module
from src.layer02_sensors.telegram.shared_tools._helpers import clean_peer_id

@watchdog_decorator(userbot_telethon_module)
async def tg_get_chat_info(client: TelegramClient, chat_id: str | int) -> str:
    """Получает полную информацию (Bio, участники) о чате/юзере"""
    chat_id = clean_peer_id(chat_id)
    try:
        entity = await client.get_entity(chat_id)
        if isinstance(entity, types.Channel) or isinstance(entity, types.Chat):
            return f"Название: {entity.title}, Тип: Группа/Канал, ID: {entity.id}"
        elif isinstance(entity, types.User):
            full_user = await client(functions.users.GetFullUserRequest(id=entity))
            bio = full_user.full_user.about or "Bio отсутствует"
            username = f"@{entity.username}" if entity.username else "No Username"
            return f"Имя: {entity.first_name}, Username: {username}, Bio: {bio}"
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка получения инфо о {chat_id}: {e}")
        return f"Ошибка получения инфо: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_search_channels(client: TelegramClient, query: str, limit: int = 5) -> str:
    """Ищет публичные каналы и группы в глобальном поиске Telegram"""
    try:
        result = await client(functions.contacts.SearchRequest(q=query, limit=limit))
        chats = []
        for chat in result.chats:
            chat_type = "Канал" if getattr(chat, 'broadcast', False) else "Группа"
            username = f"@{chat.username}" if getattr(chat, 'username', None) else "Без_юзернейма"
            title = getattr(chat, 'title', 'Без названия')
            about = "Нет описания"
            participants_count = "Неизвестно"
            
            try:
                full_chat = await client(functions.channels.GetFullChannelRequest(channel=chat))
                about = full_chat.full_chat.about or "Нет описания"
                participants_count = full_chat.full_chat.participants_count or "Неизвестно"
            except Exception:
                pass
            
            if len(about) > 150:
                about = about[:147] + "..."
                
            chats.append(f"[{chat_type}] {title} ({username}) | ID: {chat.id}\n   Подписчиков: {participants_count} | Описание: {about}")
            
        return "\n\n".join(chats) if chats else f"По запросу '{query}' ничего не найдено."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка поиска каналов: {e}")
        return f"Ошибка при поиске: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_join_channel(client: TelegramClient, link_or_username: str) -> str:
    """Вступает в канал или группу"""
    try:
        target = link_or_username.strip()
        if "t.me/+" in target or "t.me/joinchat/" in target:
            if "t.me/+" in target:
                invite_hash = target.split("t.me/+")[1].split("/")[0].split("?")[0]
            else:
                invite_hash = target.split("t.me/joinchat/")[1].split("/")[0].split("?")[0]
            await client(functions.messages.ImportChatInviteRequest(invite_hash))
            return "Успешное присоединение по приватной ссылке."
        else:
            await client(functions.channels.JoinChannelRequest(channel=target))
            return f"Успешное присоединение к {target}."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка вступления в {link_or_username}: {e}")
        return f"Ошибка при вступлении в канал: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_ban_user(client: TelegramClient, chat_id: str | int, user_id: str | int, reason: str = "Ban") -> str:
    """Банит пользователя в группе/канале ИЛИ глобально"""
    user_id = clean_peer_id(user_id)
    try:
        try:
            user = await client.get_entity(user_id)
        except ValueError:
            return f"Ошибка Telethon: Невозможно найти пользователя '{user_id}'. Передайте @username."
        
        if str(chat_id).lower() in ["global", "me", "личные", "pm"] or str(chat_id) == str(user_id):
            await client(BlockRequest(id=user))
            return f"Пользователь {user.id} успешно добавлен в глобальный ЧС."

        chat_id = clean_peer_id(chat_id)
        rights = ChatBannedRights(
            until_date=None, view_messages=True, send_messages=True, 
            send_media=True, send_stickers=True, send_gifs=True, 
            send_games=True, send_inline=True, embed_links=True
        )
        await client(EditBannedRequest(channel=chat_id, participant=user, banned_rights=rights))
        return f"Пользователь {user.id} забанен в чате {chat_id}. Причина: {reason}"
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка бана {user_id} в {chat_id}: {e}")
        return f"Ошибка при бане пользователя: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_unban_user(client: TelegramClient, chat_id: str | int, user_id: str | int) -> str:
    """Разбанивает пользователя"""
    user_id = clean_peer_id(user_id)
    try:
        user = await client.get_entity(user_id)
        if str(chat_id).lower() in ["global", "me", "личные", "pm"] or str(chat_id) == str(user_id):
            await client(UnblockRequest(id=user))
            return f"Пользователь {user.id} удален из глобального ЧС."

        chat_id = clean_peer_id(chat_id)
        rights = ChatBannedRights(until_date=None)
        await client(EditBannedRequest(channel=chat_id, participant=user, banned_rights=rights))
        return f"Пользователь {user.id} разбанен в чате {chat_id}."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка разбана {user_id} в {chat_id}: {e}")
        return f"Ошибка при разбане пользователя: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_get_banned_users(client: TelegramClient, chat_id: str | int, limit: int = 50) -> str:
    """Возвращает список забаненных пользователей"""
    try:
        banned_list = []
        if str(chat_id).lower() in ["global", "me", "личные", "pm"]:
            result = await client(GetBlockedRequest(offset=0, limit=limit))
            for user in result.users:
                name = getattr(user, 'first_name', 'Unknown')
                username = f"@{user.username}" if getattr(user, 'username', None) else "No_username"
                banned_list.append(f"- ID: {user.id} | {name} ({username})")
            return "Глобальный ЧС:\n" + "\n".join(banned_list) if banned_list else "Глобальный ЧС пуст."

        chat_id = clean_peer_id(chat_id)
        async for user in client.iter_participants(chat_id, filter=ChannelParticipantsKicked, limit=limit):
            name = getattr(user, 'first_name', 'Unknown')
            username = f"@{user.username}" if getattr(user, 'username', None) else "No_username"
            banned_list.append(f"- ID: {user.id} | {name} ({username})")
            
        return f"Забаненные в чате {chat_id}:\n" + "\n".join(banned_list) if banned_list else "Список забаненных пуст."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка получения бан-листа {chat_id}: {e}")
        return f"Ошибка при получении списка забаненных: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_create_channel_post(client: TelegramClient, channel_id: str | int, text: str) -> str:
    """Отправляет новый пост в Telegram-канал"""
    channel_id = clean_peer_id(channel_id)
    try:
        msg = await client.send_message(channel_id, text)
        return f"Пост успешно опубликован в канале. ID поста: {msg.id}"
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка публикации в канал {channel_id}: {e}")
        return f"Ошибка публикации поста: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_get_channel_subscribers(client: TelegramClient, chat_id: str | int, limit: int = 50) -> str:
    """Получает список подписчиков канала или группы"""
    chat_id = clean_peer_id(chat_id)
    try:
        subscribers = []
        async for user in client.iter_participants(chat_id, limit=limit, filter=ChannelParticipantsRecent):
            name = getattr(user, 'first_name', 'Unknown')
            username = f"@{user.username}" if getattr(user, 'username', None) else "без_юзернейма"
            subscribers.append(f"- ID: {user.id} | {name} ({username})")
        return "Список подписчиков:\n" + "\n".join(subscribers) if subscribers else "Список пуст или нет прав."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка получения подписчиков {chat_id}: {e}")
        return f"Ошибка при получении подписчиков: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_check_user_in_chat(client: TelegramClient, chat_id: str | int, query: str) -> str:
    """Проверяет, есть ли конкретный пользователь в канале/группе"""
    chat_id = clean_peer_id(chat_id)
    try:
        found_users = []
        async for user in client.iter_participants(chat_id, search=query, filter=ChannelParticipantsSearch):
            name = getattr(user, 'first_name', 'Unknown')
            username = f"@{user.username}" if getattr(user, 'username', None) else "без_юзернейма"
            found_users.append(f"ID: {user.id} | {name} ({username})")
        return "Найдены совпадения:\n" + "\n".join(found_users) if found_users else f"Пользователь '{query}' не найден."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка поиска юзера в {chat_id}: {e}")
        return f"Ошибка при поиске пользователя: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_create_channel(client: TelegramClient, title: str, about: str = "") -> str:
    """Создает новый Telegram-канал"""
    try:
        result = await client(CreateChannelRequest(title=title, about=about, megagroup=False))
        channel_id = result.chats[0].id
        return f"Канал '{title}' успешно создан. ID: {channel_id}."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка создания канала: {e}")
        return f"Ошибка при создании канала: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_update_channel_info(client: TelegramClient, channel_id: str | int, new_title: str = None, new_about: str = None) -> str:
    """Изменяет название и/или описание канала"""
    channel_id = clean_peer_id(channel_id)
    try:
        entity = await client.get_input_entity(channel_id)
        res_msg = []
        if new_title:
            await client(EditTitleRequest(channel=entity, title=new_title))
            res_msg.append("Название обновлено.")
        if new_about:
            await client(EditChatAboutRequest(peer=entity, about=new_about))
            res_msg.append("Описание обновлено.")
        return " ".join(res_msg) if res_msg else "Нет данных для обновления."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка обновления канала {channel_id}: {e}")
        return f"Ошибка при обновлении информации канала: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_set_channel_username(client: TelegramClient, channel_id: str | int, username: str) -> str:
    """Делает канал публичным"""
    channel_id = clean_peer_id(channel_id)
    try:
        entity = await client.get_input_entity(channel_id)
        clean_username = username.replace("@", "")
        await client(UpdateUsernameRequest(channel=entity, username=clean_username))
        return f"Канал стал публичным. Ссылка: t.me/{clean_username}"
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка установки юзернейма {channel_id}: {e}")
        return f"Ошибка установки юзернейма: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_promote_to_admin(client: TelegramClient, channel_id: str | int, user_id: str | int) -> str:
    """Выдает полные права администратора"""
    channel_id = clean_peer_id(channel_id)
    user_id = clean_peer_id(user_id)
    try:
        channel_entity = await client.get_input_entity(channel_id)
        user_entity = await client.get_input_entity(user_id)
        rights = ChatAdminRights(
            change_info=True, post_messages=True, edit_messages=True,
            delete_messages=True, ban_users=True, invite_users=True,
            pin_messages=True, add_admins=True, anonymous=False, manage_call=True
        )
        await client(EditAdminRequest(channel=channel_entity, user_id=user_entity, admin_rights=rights, rank="Creator's Proxy"))
        return f"Пользователь {user_id} назначен администратором."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка выдачи админки в {channel_id}: {e}")
        return f"Ошибка выдачи прав: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_create_discussion_group(client: TelegramClient, channel_id: str | int, group_title: str) -> str:
    """Создает супергруппу и привязывает её к каналу"""
    channel_id = clean_peer_id(channel_id)
    try:
        channel_entity = await client.get_input_entity(channel_id)
        created_group = await client(functions.channels.CreateChannelRequest(title=group_title, about="Обсуждения", megagroup=True))
        group_id = created_group.chats[0].id
        group_entity = await client.get_input_entity(group_id)
        await client(functions.channels.SetDiscussionGroupRequest(broadcast=channel_entity, group=group_entity))
        return f"Группа '{group_title}' привязана к каналу. ID: {group_id}"
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка привязки группы к {channel_id}: {e}")
        return f"Ошибка создания группы обсуждений: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_leave_chat(client: TelegramClient, chat_id: str | int) -> str:
    """Выходит из канала или группы"""
    chat_id = clean_peer_id(chat_id)
    try:
        entity = await client.get_input_entity(chat_id)
        await client(functions.channels.LeaveChannelRequest(channel=entity))
        return "Успешно покинули чат/канал."
    except Exception as e:
        try:
            await client(functions.messages.DeleteChatUserRequest(chat_id=chat_id, user_id='me'))
            return "Успешно покинули базовую группу."
        except Exception as e2:
            system_logger.error(f"[Telegram Tools] Ошибка выхода из {chat_id}: {e} | {e2}")
            return f"Ошибка при выходе из чата: {e} | {e2}"

@watchdog_decorator(userbot_telethon_module)
async def tg_archive_chat(client: TelegramClient, chat_id: str | int) -> str:
    """Отправляет чат в архив"""
    chat_id = clean_peer_id(chat_id)
    try:
        entity = await client.get_input_entity(chat_id)
        await client(functions.folders.EditPeerFoldersRequest(folder_peers=[types.InputFolderPeer(peer=entity, folder_id=1)]))
        return "Чат успешно отправлен в архив."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка архивации {chat_id}: {e}")
        return f"Ошибка при архивации чата: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_unarchive_chat(client: TelegramClient, chat_id: str | int) -> str:
    """Возвращает чат из архива"""
    chat_id = clean_peer_id(chat_id)
    try:
        entity = await client.get_input_entity(chat_id)
        await client(functions.folders.EditPeerFoldersRequest(folder_peers=[types.InputFolderPeer(peer=entity, folder_id=0)]))
        return "Чат успешно возвращен из архива."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка разархивации {chat_id}: {e}")
        return f"Ошибка при возврате чата из архива: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_create_supergroup(client: TelegramClient, title: str, about: str = "") -> str:
    """Создает новую супергруппу"""
    try:
        result = await client(functions.channels.CreateChannelRequest(title=title, about=about, megagroup=True))
        return f"Группа '{title}' успешно создана. ID: {result.chats[0].id}"
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка создания группы: {e}")
        return f"Ошибка при создании группы: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_invite_to_chat(client: TelegramClient, chat_id: str | int, user_id: str | int) -> str:
    """Приглашает пользователя в группу/канал"""
    chat_id = clean_peer_id(chat_id)
    user_id = clean_peer_id(user_id)
    try:
        chat_entity = await client.get_input_entity(chat_id)
        user_entity = await client.get_input_entity(user_id)
        await client(functions.channels.InviteToChannelRequest(channel=chat_entity, users=[user_entity]))
        return f"Пользователь {user_id} приглашен в чат {chat_id}."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка инвайта {user_id} в {chat_id}: {e}")
        return f"Ошибка при приглашении: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_get_chat_admins(client: TelegramClient, chat_id: str | int) -> str:
    """Получает список администраторов чата/канала"""
    chat_id = clean_peer_id(chat_id)
    try:
        admins = []
        async for admin in client.iter_participants(chat_id, filter=ChannelParticipantsAdmins):
            name = getattr(admin, 'first_name', 'Unknown')
            username = f"@{admin.username}" if getattr(admin, 'username', None) else "без_юзернейма"
            admins.append(f"- ID: {admin.id} | {name} ({username})")
        return f"Администраторы чата {chat_id}:\n" + "\n".join(admins) if admins else "Не удалось найти администраторов."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка получения админов {chat_id}: {e}")
        return f"Ошибка при получении списка администраторов: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_change_channel_avatar(client: TelegramClient, channel_id: str | int, image_path: str) -> str:
    """Меняет аватарку канала"""
    channel_id = clean_peer_id(channel_id)
    try:
        if not os.path.exists(image_path):
            return f"Ошибка: Файл '{image_path}' не найден."
        entity = await client.get_input_entity(channel_id)
        uploaded_photo = await client.upload_file(image_path)
        await client(EditPhotoRequest(channel=entity, photo=uploaded_photo))
        return "Аватарка канала успешно обновлена."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка смены аватарки канала {channel_id}: {e}")
        return f"Ошибка при обновлении аватарки: {e}"