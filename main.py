import asyncio

from config import (
    CAPTCHA_FILE,
    CHECK_INTERVAL,
)

from squirrelmail import SquirrelMail
from telegram_bot import telegram


mail = SquirrelMail()


# ---------------------------------------------------------

async def ensure_login():

    #
    # Already authenticated
    #

    if mail.logged_in():
        return True

    telegram.set_status(
        "Waiting for CAPTCHA..."
    )

    await telegram.send_message(
        "🔐 Session expired."
    )

    mail.download_captcha(CAPTCHA_FILE)

    code = await telegram.request_captcha(
        CAPTCHA_FILE
    )

    ok = mail.login(code)

    if ok:

        telegram.set_status(
            "Logged in"
        )

        await telegram.send_message(
            "✅ Login successful."
        )

        return True

    telegram.set_status(
        "Login failed"
    )

    await telegram.send_message(
        "❌ Login failed.\n"
        "A new CAPTCHA will be requested."
    )

    return False


# ---------------------------------------------------------

async def mailbox_check(manual=False):

    ok = await ensure_login()

    if not ok:
        return

    try:

        new_mail, message = mail.has_new_mail()

        telegram.set_status(
            f"Running\n"
            f"Newest ID: {message.id}"
        )

        if new_mail:

            await telegram.send_message(
                f"""📬 New Mail

From: {message.sender}
Subject: {message.subject}
Date: {message.date}
ID: {message.id}
"""
            )

        elif manual:

            await telegram.send_message(
                f"""✅ No new mail.

Newest message:

From: {message.sender}
Subject: {message.subject}
Date: {message.date}
ID: {message.id}
"""
            )

    except Exception as e:

        telegram.set_status("Mailbox error")

        await telegram.send_message(
            f"⚠️ Mailbox error\n\n{e}"
        )


# ---------------------------------------------------------

async def scheduler():

    while True:

        try:

            #
            # Manual restart
            #

            if telegram.restart_event.is_set():

                telegram.restart_event.clear()

                mail.clear_cookies()

                await telegram.send_message(
                    "Session cleared."
                )

            #
            # Manual mailbox check
            #

            async def manual_check():
                await mailbox_check(manual=True)

            telegram.check_callback = manual_check

        except Exception as e:

            await telegram.send_message(
                f"Fatal error:\n{e}"
            )

        await asyncio.sleep(
            CHECK_INTERVAL
        )


# ---------------------------------------------------------

async def main():
    print("MAIN STARTED")
    await telegram.start()

    telegram.set_status(
        "Starting..."
    )

    await telegram.send_message(
        "📨 Mail monitor started."
    )

    #
    # Initialize last message ID
    #

    try:

        if mail.logged_in():

            mail.initialize()

    except Exception:
        pass

    await scheduler()
    print("SCHEDULER STARTED")

    while True:
          print("scheduler loop")


# ---------------------------------------------------------

if __name__ == "__main__":

    asyncio.run(main())
