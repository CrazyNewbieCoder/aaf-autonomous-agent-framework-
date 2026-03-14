# Файл: src/layer02_sensors/telegram/shared_tools/interact.py

import random
from telethon import TelegramClient
from telethon.tl.functions.messages import SendReactionRequest, SendVoteRequest
from telethon.tl.types import ReactionEmoji, InputMediaPoll, Poll, PollAnswer, TextWithEntities

from src.layer00_utils.logger import system_logger
from src.layer00_utils.watchdog.watchdog_decorator import watchdog_decorator
from src.layer00_utils.watchdog.watchdog import userbot_telethon_module
from src.layer02_sensors.telegram.shared_tools._helpers import clean_peer_id

@watchdog_decorator(userbot_telethon_module)
async def tg_set_reaction(client: TelegramClient, chat_id: str | int, message_id: int, emoticon: str) -> str:
    """Ставит реакцию на сообщение"""
    chat_id = clean_peer_id(chat_id)
    try:
        await client(SendReactionRequest(
            peer=chat_id, msg_id=message_id, reaction=[ReactionEmoji(emoticon=emoticon)]
        ))
        return f"Реакция '{emoticon}' успешно поставлена."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка реакции на {message_id} в {chat_id}: {e}")
        return f"Ошибка установки реакции: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_comment_on_post(client: TelegramClient, channel_id: str | int, message_id: int, text: str) -> str:
    """Оставляет комментарий под постом в канале"""
    channel_id = clean_peer_id(channel_id)
    try:
        msg = await client.send_message(channel_id, text, comment_to=message_id)
        return f"Комментарий успешно оставлен. ID: {msg.id}"
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка комментария к {message_id} в {channel_id}: {e}")
        return f"Ошибка при отправке комментария: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_create_poll(client: TelegramClient, chat_id: str | int, question: str, options: list) -> str:
    """Создает опрос в чате/канале"""
    chat_id = clean_peer_id(chat_id)
    try:
        answers = [
            PollAnswer(text=TextWithEntities(text=str(opt), entities=[]), option=str(i).encode('utf-8'))
            for i, opt in enumerate(options)
        ]
        poll_media = InputMediaPoll(
            poll=Poll(
                id=random.getrandbits(62), question=TextWithEntities(text=question, entities=[]),
                answers=answers, closed=False, multiple_choice=False, quiz=False
            )
        )
        msg = await client.send_message(chat_id, file=poll_media)
        return f"Опрос '{question}' успешно создан. ID: {msg.id}"
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка создания опроса в {chat_id}: {e}")
        return f"Ошибка при создании опроса: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_get_poll_results(client: TelegramClient, chat_id: str | int, message_id: int) -> str:
    """Получает результаты опроса"""
    chat_id = clean_peer_id(chat_id)
    try:
        messages = await client.get_messages(chat_id, ids=[message_id])
        if not messages or not getattr(messages[0], 'poll', None):
            return "Сообщение не найдено или это не опрос."

        message = messages[0]
        msg_time = message.date.astimezone().strftime("%Y-%m-%d %H:%M:%S")
        poll = message.poll.poll
        results = message.poll.results
        question_text = getattr(poll.question, 'text', str(poll.question))
        total_voters = getattr(results, 'total_voters', 0)
        
        if total_voters == 0:
            return f"[{msg_time}] Опрос '{question_text}'. Голосов пока нет."

        summary = [f"[{msg_time}] Опрос: {question_text}\nВсего голосов: {total_voters}\nРезультаты:"]
        votes_map = {r.option: r.voters for r in results.results} if getattr(results, 'results', None) else {}
        
        for answer in poll.answers:
            answer_text = getattr(answer.text, 'text', str(answer.text))
            count = votes_map.get(answer.option, 0)
            percent = round((count / total_voters) * 100, 1) if total_voters > 0 else 0
            summary.append(f"- {answer_text}: {count} ({percent}%)")
            
        return "\n".join(summary)
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка результатов опроса {message_id} в {chat_id}: {e}")
        return f"Ошибка получения результатов опроса: {e}"

@watchdog_decorator(userbot_telethon_module)
async def tg_vote_in_poll(client: TelegramClient, chat_id: str | int, message_id: int, options: list) -> str:
    """Голосует в опросе"""
    chat_id = clean_peer_id(chat_id)
    try:
        messages = await client.get_messages(chat_id, ids=[message_id])
        if not messages or not messages[0].poll:
            return "Ошибка: Сообщение не найдено или это не опрос."
            
        poll_answers = messages[0].poll.poll.answers
        options_to_send = []
        
        for opt in options:
            opt_str = str(opt)
            for answer in poll_answers:
                if opt_str.lower() in getattr(answer.text, 'text', str(answer.text)).lower():
                    options_to_send.append(answer.option)
                    break
            else:
                if opt_str.isdigit() and int(opt_str) < len(poll_answers):
                    options_to_send.append(poll_answers[int(opt_str)].option)

        if not options_to_send:
            return f"Ошибка: Не удалось найти вариант ответа '{options}' в опросе."

        await client(SendVoteRequest(peer=chat_id, msg_id=message_id, options=options_to_send))
        return f"Голос за вариант(ы) '{options}' успешно отправлен."
    except Exception as e:
        system_logger.error(f"[Telegram Tools] Ошибка голосования {message_id} в {chat_id}: {e}")
        return f"Ошибка при голосовании: {e}"