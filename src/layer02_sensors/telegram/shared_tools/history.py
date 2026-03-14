from datetime import datetime
from telethon import TelegramClient
from telethon.tl.functions.messages import GetPeerDialogsRequest

from src.layer00_utils.logger import system_logger
from src.layer00_utils.watchdog.watchdog_decorator import watchdog_decorator
from src.layer00_utils.watchdog.watchdog import userbot_telethon_module
from src.layer02_sensors.telegram.shared_tools._helpers import clean_peer_id, _get_content
from telethon import utils

@watchdog_decorator(userbot_telethon_module)
async def tg_get_recent_messages(client: TelegramClient, chat_id: str | int, limit: int = 50, topic_id: int = None) -> str:
    """Получает историю сообщений чата (или конкретного топика)"""
    chat_id = clean_peer_id(chat_id)
    all_messages = []
    try:
        entity = await client.get_input_entity(chat_id)
        dialogs_res = await client(GetPeerDialogsRequest(peers=[entity]))
        
        read_outbox_max_id = 0
        read_inbox_max_id = 0
        if dialogs_res.dialogs:
            read_outbox_max_id = dialogs_res.dialogs[0].read_outbox_max_id
            read_inbox_max_id = dialogs_res.dialogs[0].read_inbox_max_id

        async for message in client.iter_messages(chat_id, limit=limit, reply_to=topic_id):
            local_tz = datetime.now().astimezone().tzinfo
            msg_time = message.date.astimezone(local_tz).strftime("%H:%M:%S")
            
            sender = await message.get_sender()
            if not sender:
                sender = await message.get_chat()
                
            first_name = utils.get_display_name(sender) if sender else "Unknown"
            username = f"@{sender.username}" if getattr(sender, 'username', None) else "No_Username"

            reply_info = ""
            if message.is_reply:
                reply_id = message.reply_to_msg_id
                reply_msg = await message.get_reply_message()
                
                if reply_msg:
                    orig_sender = await reply_msg.get_sender()
                    if not orig_sender:
                        orig_sender = await reply_msg.get_chat()
                        
                    orig_name = utils.get_display_name(orig_sender) if orig_sender else "Unknown"
                    orig_text = _get_content(reply_msg)
                    if len(orig_text) > 35:
                        orig_text = orig_text[:32] + "..."
                    reply_info = f" [В ответ на ID {reply_id} от {orig_name}: '{orig_text}']"
                else:
                    reply_info = f" [В ответ на недоступное сообщение ID {reply_id}]"

            text = _get_content(message)
            
            read_status = ""
            if message.out:
                read_status = " [Прочитано собеседником]" if message.id <= read_outbox_max_id else " [Не прочитано собеседником]"
            else:
                read_status = " [Прочитано]" if message.id <= read_inbox_max_id else " [Новое/Не прочитано]"

            all_messages.append(f"[{msg_time}] ID: {message.id}{read_status} | {first_name} ({username}){reply_info}: {text}")

        all_messages.reverse()
        return "\n".join(all_messages) if all_messages else "Чат пуст."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка чтения чата {chat_id}: {e}")
        return f"Ошибка чтения чата: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_get_dialogs(client: TelegramClient, limit: int = 30) -> str:
    """Получает список последних диалогов/групп со статусами прочтения"""
    all_dialogs = []
    try:
        async for dialog in client.iter_dialogs(limit=limit):
            entity = dialog.entity
            if dialog.is_user:
                chat_type = "Пользователь"
            elif dialog.is_channel:
                chat_type = "Канал" if getattr(entity, 'broadcast', False) else "Супергруппа"
            else:
                chat_type = "Группа"
                
            display_name = getattr(entity, 'first_name', getattr(entity, 'title', dialog.name))
            username = f"@{entity.username}" if getattr(entity, 'username', None) else "No_Link"
            
            unread = f" [Новых сообщений вам: {dialog.unread_count}]" if dialog.unread_count > 0 else ""
            
            outbox_status = ""
            last_msg = dialog.message
            read_outbox_max_id = getattr(dialog.dialog, 'read_outbox_max_id', 0)
            
            if last_msg and last_msg.out:
                outbox_status = " | Ваш последний ответ: прочитан" if last_msg.id <= read_outbox_max_id else " | Ваш последний ответ: не прочитан"
            
            all_dialogs.append(f"ID: {dialog.id} | [{chat_type}] {display_name} ({username}){unread}{outbox_status}")
            
        return "\n".join(all_dialogs)
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка получения диалогов: {e}")
        return f"Ошибка получения диалогов: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_get_channel_posts(client: TelegramClient, channel_name: str, limit: int = 10) -> str:
    """Получает последние посты из канала с количеством реакций и комментариев + ПОМЕЧАЕТ ПРОЧИТАННЫМ"""
    all_posts = []
    try:
        entity = await client.get_entity(channel_name)
        messages = []
        async for message in client.iter_messages(entity, limit=limit):
            messages.append(message)
            local_tz = datetime.now().astimezone().tzinfo
            post_time = message.date.astimezone(local_tz).strftime("%Y-%m-%d %H:%M")
            content = _get_content(message)
            views = f"Просмотры: {message.views}" if message.views is not None else ""
            
            replies_cnt = message.replies.replies if message.replies else 0
            comments_str = f"Комментарии: {replies_cnt}" if replies_cnt > 0 else ""

            reactions_str = ""
            if message.reactions and message.reactions.results:
                reacts = [f"{getattr(r.reaction, 'emoticon', '?')}{r.count}" for r in message.reactions.results]
                reactions_str = f" {' '.join(reacts)}"

            meta = " | ".join(filter(None, [views, comments_str, reactions_str]))
            all_posts.append(f"[{post_time}] ID: {message.id} | {content}\n   Метрики: {meta}")

        if messages:
            await client.send_read_acknowledge(entity, message=messages[0], clear_mentions=True)

        all_posts.reverse()
        return "\n\n".join(all_posts)
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка чтения постов из {channel_name}: {e}")
        return f"Ошибка чтения канала: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_get_post_comments(client: TelegramClient, channel_name: str, message_id: int, limit: int = 20) -> str:
    """Читает комментарии к конкретному посту"""
    comments = []
    try:
        entity = await client.get_entity(channel_name)
        async for message in client.iter_messages(entity, reply_to=message_id, limit=limit):
            sender = await message.get_sender()
            if not sender:
                sender = await message.get_chat()
                
            name = utils.get_display_name(sender) if sender else "Unknown"
            username = f"@{sender.username}" if getattr(sender, 'username', None) else ""
            text = _get_content(message)
            comments.append(f"Chat ID: {message.chat_id} | Msg ID: {message.id} | {name} ({username}): {text}")
        
        comments.reverse()
        return "\n".join(comments) if comments else "Комментариев пока нет."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка чтения комментариев поста {message_id} в {channel_name}: {e}")
        return f"Ошибка чтения комментариев: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_get_unread_chats_summary(client: TelegramClient, limit: int = 50) -> str:
    """Получает сводку чатов ТОЛЬКО с непрочитанными входящими сообщениями"""
    unread_chats = []
    try:
        async for dialog in client.iter_dialogs(limit=limit):
            if dialog.unread_count > 0:
                entity = dialog.entity
                if dialog.is_user:
                    chat_type = "Пользователь"
                elif dialog.is_channel:
                    chat_type = "Канал" if getattr(entity, 'broadcast', False) else "Супергруппа"
                else:
                    chat_type = "Группа"
                    
                display_name = getattr(entity, 'first_name', getattr(entity, 'title', dialog.name))
                username = f"@{entity.username}" if getattr(entity, 'username', None) else "без_юзернейма"
                status_str = f"Новых: {dialog.unread_count}"
                
                unread_chats.append(f"- [{chat_type}] {display_name} ({username}) | ID: {dialog.id} | {status_str}")
                
        return "\n".join(unread_chats) if unread_chats else "Нет непрочитанных сообщений."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка получения непрочитанных чатов: {e}")
        return f"Ошибка получения непрочитанных: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_search_chat_messages(client: TelegramClient, chat_id: str | int, query: str = None, from_user: str | int = None, limit: int = 20) -> str:
    """Ищет сообщения в чате по тексту или от конкретного пользователя"""
    chat_id = clean_peer_id(chat_id)
    from_user = clean_peer_id(from_user)
    try:
        all_messages = []
        async for message in client.iter_messages(chat_id, search=query, from_user=from_user, limit=limit):
            local_tz = datetime.now().astimezone().tzinfo
            msg_time = message.date.astimezone(local_tz).strftime("%Y-%m-%d %H:%M:%S")
            
            sender = await message.get_sender()
            if not sender:
                sender = await message.get_chat()
                
            first_name = utils.get_display_name(sender) if sender else "Unknown"
            username = f"@{sender.username}" if getattr(sender, 'username', None) else "No_Username"
            text = _get_content(message)
            
            all_messages.append(f"[{msg_time}] ID: {message.id} | {first_name} ({username}): {text}")
            
        all_messages.reverse()
        return "Найденные сообщения:\n" + "\n".join(all_messages) if all_messages else "По вашему запросу ничего не найдено."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка поиска сообщений в {chat_id}: {e}")
        return f"Ошибка поиска сообщений: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_mark_as_read(client: TelegramClient, chat_id: str | int) -> str:
    """Принудительно помечает чат как прочитанный"""
    chat_id = clean_peer_id(chat_id)
    try:
        await client.send_read_acknowledge(chat_id)
        await client.send_read_acknowledge(chat_id, clear_mentions=True)
        return "Чат успешно помечен как прочитанный."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка пометки прочитанным {chat_id}: {e}")
        return f"Ошибка при пометке прочитанным: {e}"