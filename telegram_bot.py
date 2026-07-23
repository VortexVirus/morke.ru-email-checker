import asyncio

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from config import BOT_TOKEN, CHAT_ID


class TelegramInterface:

    def __init__(self):

        self.application = (
            Application.builder()
            .token(BOT_TOKEN)
            .build()
        )

        self.status = "Starting..."

        self.captcha_future = None
        self.check_callback = None
        self.check_event = asyncio.Event()
        self.restart_event = asyncio.Event()

        self.application.add_handler(
            CommandHandler("status", self.status_command)
        )

        self.application.add_handler(
            CommandHandler("check", self.check_command)
        )

        self.application.add_handler(
            CommandHandler("restart", self.restart_command)
        )

        self.application.add_handler(
            CommandHandler("captcha", self.captcha_command)
        )

    async def start(self):

        await self.application.initialize()
        await self.application.start()

        await self.application.bot.set_my_commands([
            BotCommand("status", "Show monitor status"),
            BotCommand("check", "Check mailbox now"),
            BotCommand("restart", "Restart login"),
            BotCommand("captcha", "Submit captcha"),
        ])

        await self.application.updater.start_polling()

    async def stop(self):

        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()

    async def send_message(self, text):

        await self.application.bot.send_message(
            chat_id=CHAT_ID,
            text=text,
        )

    async def send_photo(self, filename, caption=""):

        with open(filename, "rb") as photo:

            await self.application.bot.send_photo(
                chat_id=CHAT_ID,
                photo=photo,
                caption=caption,
            )

    def set_status(self, text):

        self.status = text

    async def request_captcha(self, filename):

        self.captcha_future = asyncio.get_running_loop().create_future()

        await self.send_photo(
            filename,
            "Reply using:\n/captcha CODE"
        )

        return await self.captcha_future

    async def status_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):

        if str(update.effective_chat.id) != str(CHAT_ID):
            return

        await update.message.reply_text(self.status)

    async def check_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):

        if str(update.effective_chat.id) != str(CHAT_ID):
            return

        if self.check_callback is None:
            await update.message.reply_text("Monitor not running.")
            return

        await self.check_callback()

    async def restart_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):

        if str(update.effective_chat.id) != str(CHAT_ID):
            return

        self.restart_event.set()

        await update.message.reply_text(
            "Restart requested."
        )

    async def captcha_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):

        if str(update.effective_chat.id) != str(CHAT_ID):
            return

        if len(context.args) != 1:

            await update.message.reply_text(
                "Usage:\n/captcha CODE"
            )

            return

        if self.captcha_future is None:

            await update.message.reply_text(
                "No captcha is currently pending."
            )

            return

        if self.captcha_future.done():

            await update.message.reply_text(
                "Captcha already received."
            )

            return

        self.captcha_future.set_result(
            context.args[0]


        )

        await update.message.reply_text(
            "Captcha received."
        )


telegram = TelegramInterface()


async def main():

    await telegram.start()

    telegram.set_status("Running")

    await telegram.send_message(
        "Bot started."
    )

    while True:

        await asyncio.sleep(60)


if __name__ == "__main__":

    asyncio.run(main())
