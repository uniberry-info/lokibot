import logging
import telethon.sync
import sqlalchemy.orm

from lokiunimore.config import config, TELEGRAM_APP_ID, TELEGRAM_APP_HASH, TELEGRAM_BOT_TOKEN, SQLALCHEMY_DATABASE_URL
from lokiunimore.utils.logs import install_log_handler
from lokiunimore.sql.tables import TelegramUser
from lokiunimore.web.app import app
from .templates import messages

log = logging.getLogger(__name__)


def main():
    install_log_handler()
    client: telethon.sync.TelegramClient = telethon.sync.TelegramClient(
        session="bot",
        api_id=TELEGRAM_APP_ID.__wrapped__,
        api_hash=TELEGRAM_APP_HASH.__wrapped__,
    ).start(
        bot_token=TELEGRAM_BOT_TOKEN.__wrapped__,
    )

    sqla_engine = sqlalchemy.create_engine(SQLALCHEMY_DATABASE_URL.__wrapped__)

    def sqla_session():
        return sqlalchemy.orm.Session(bind=sqla_engine)

    @client.on(telethon.events.NewMessage(pattern="^[/]start"))
    async def on_start(event: telethon.events.NewMessage.Event):
        if not event.is_private:
            await client.send_message(
                entity=event.chat_id,
                reply_to=event.message.id,
                message=messages.START_ONLY_PRIVATE_CHAT
            )
            return

        user_id = event.chat_id
        with sqla_session() as session:
            telegram_user: TelegramUser = TelegramUser.create(session=session, id=user_id)
            session.commit()

            with app.app_context():
                user = await client.get_me()
                formatting = dict(
                    username=user.username,
                    profile_url=telegram_user.profile_url(),
                )

        await client.send_message(
            entity=event.chat_id,
            reply_to=event.message.id,
            message=messages.START_SUCCESSFUL.format(**formatting)
        )

    @client.on(telethon.events.ChatAction())
    async def on_join(event: telethon.events.ChatAction.Event):
        breakpoint()

    client.run_until_disconnected()


if __name__ == "__main__":
    config.proxies.resolve()
    main()
