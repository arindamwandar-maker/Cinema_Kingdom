import logging

from telegram.constants import ParseMode

from config import Config
from keyboards import Keyboards


class PromotionService:
    def __init__(self, config: Config):
        self.config = config

    async def send_promotion(self, context):
        text = (
            '🎬 <b>Welcome to Cinema Kingdom</b>\n\n'
            'Search for available movies in our community group.\n'
            'Use the official update channel to receive new upload announcements.\n'
            'Movie links and temporary results are removed automatically for a cleaner experience.\n'
            'Please avoid spam, outside links, and promotional usernames in the group.\n'
            'Join both places below and enjoy Cinema Kingdom responsibly.'
        )

        previous = context.bot_data.setdefault('promo_messages', {})

        for chat_id in (self.config.GROUP_ID, self.config.CHANNEL_ID):
            old_message_id = previous.get(chat_id)
            if old_message_id:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=old_message_id)
                except Exception:
                    pass

            try:
                sent = await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=Keyboards.promo_buttons(
                        self.config.CHANNEL_USERNAME,
                        self.config.GROUP_USERNAME,
                    ),
                    disable_web_page_preview=True,
                )
                previous[chat_id] = sent.message_id
            except Exception as exc:
                logging.warning('Promotion message failed for %s: %s', chat_id, exc)
