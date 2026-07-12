import logging

from telegram.constants import ParseMode

from config import Config
from keyboards import Keyboards


class PromotionService:

    def __init__(self, config: Config):
        self.config = config

    async def send_promotion(self, context):

        text = (
            "📹 <b>Welcome to Cinema Kingdom</b> 📹\n\n"

            "🎬 Welcome to our movie community! Search and download your favorite movies for free.\n"
            "🍿 Enjoy Hollywood, Bollywood, and regional movies anytime.\n"
            "🔍 Simply search for the movie you want and get instant access.\n"
            "📢 Stay connected for the latest movie updates and releases.\n"
            "❤️ Enjoy unlimited entertainment with us!\n\n"

            "🎬 আমাদের মুভি কমিউনিটিতে আপনাকে স্বাগতম! আপনার পছন্দের সিনেমা বিনামূল্যে খুঁজুন এবং ডাউনলোড করুন।\n"
            "🍿 হলিউড, বলিউড এবং আঞ্চলিক সিনেমা উপভোগ করুন।\n"
            "🔍 পছন্দের সিনেমা সার্চ করুন এবং সঙ্গে সঙ্গে অ্যাক্সেস পান।\n"
            "📢 নতুন সিনেমা ও আপডেট পেতে আমাদের সঙ্গে যুক্ত থাকুন।\n"
            "❤️ আমাদের সঙ্গে সীমাহীন বিনোদন উপভোগ করুন!\n\n"

            "🎬 हमारे मूवी कम्युनिटी में आपका स्वागत है! अपनी पसंदीदा फिल्में मुफ्त में खोजें और डाउनलोड करें।\n"
            "🍿 हॉलीवुड, बॉलीवुड और क्षेत्रीय फिल्मों का आनंद लें।\n"
            "🔍 अपनी पसंद की फिल्म खोजें और तुरंत एक्सेस पाएं।\n"
            "📢 नई फिल्मों और अपडेट्स के लिए हमारे साथ जुड़े रहें।\n"
            "❤️ हमारे साथ अनलिमिटेड मनोरंजन का आनंद लें!"
        )

        previous = context.bot_data.setdefault(
            "promo_messages",
            {}
        )

        for chat_id in (
            self.config.GROUP_ID,
            self.config.CHANNEL_ID
        ):
            old_message_id = previous.get(chat_id)

            if old_message_id:
                try:
                    await context.bot.delete_message(
                        chat_id=chat_id,
                        message_id=old_message_id
                    )
                except Exception:
                    pass

            try:
                sent = await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=Keyboards.promo_buttons(
                        self.config.CHANNEL_USERNAME,
                        self.config.GROUP_USERNAME
                    ),
                    disable_web_page_preview=True
                )

                previous[chat_id] = sent.message_id

            except Exception as exc:
                logging.warning(
                    "Promotion message failed for %s: %s",
                    chat_id,
                    exc
                )