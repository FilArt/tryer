import asyncio
import tempfile
from pathlib import Path

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from .config import load_config
from .database import Database
from .downloader import Downloader
from .llm import Planner
from .organizer import Organizer


class App:
    def __init__(self):
        self.config = load_config()
        self.db = Database(self.config.database_path)
        self.downloader = Downloader(
            self.config.qbittorrent_host,
            self.config.qbittorrent_username,
            self.config.qbittorrent_password,
            self.config.download_dir,
        )
        self.planner = Planner(
            self.config.openai_model,
            self.config.movies_dir,
            self.config.series_dir,
            self.config.openai_api_key,
            self.config.openai_base_url,
        )
        self.organizer = Organizer(self.planner)
        self.pending: dict[str, tuple[int, str, dict]] = {}

    def commands_text(self) -> str:
        return "\n".join(
            [
                "/start - начать",
                "/status - статус загрузок",
                "/list - список торрентов",
                "/ask - спросить модель",
                "/help - помощь",
            ]
        )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Отправьте magnet-ссылку или .torrent файл.")

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(self.commands_text())

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        rows = self.db.list_recent()
        if not rows:
            await update.message.reply_text("Загрузок нет.")
            return
        await update.message.reply_text("\n".join(f"#{row['id']} {row['name']} - {row['status']}" for row in rows))

    async def list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        torrents = self.downloader.torrents()
        if not torrents:
            await update.message.reply_text("Торрентов нет.")
            return
        await update.message.reply_text("\n".join(f"{torrent.name}: {float(torrent.progress) * 100:.0f}%" for torrent in torrents))

    async def ask(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        prompt = " ".join(context.args)
        if not prompt:
            await update.message.reply_text("Использование: /ask вопрос")
            return
        message = await update.message.reply_text("...")
        answer = ""
        last_sent = ""
        for delta in self.planner.ask_stream(prompt):
            answer += delta
            if len(answer) - len(last_sent) >= 120:
                text = answer[:4000] or "..."
                await message.edit_text(text)
                last_sent = answer
        await message.edit_text(answer[:4000] or "Пустой ответ.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text or ""
        if text == "/":
            await update.message.reply_text(self.commands_text())
            return
        if text.startswith("magnet:"):
            self.downloader.add_magnet(text)
            name = text[:120]
            torrent_id = self.db.create_torrent(update.effective_chat.id, None, name)
            self.db.create_job(torrent_id)
            await update.message.reply_text("Торрент добавлен.")
            return
        await update.message.reply_text("Пришлите magnet-ссылку или .torrent файл.")

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        document = update.message.document
        if not document.file_name.endswith(".torrent"):
            await update.message.reply_text("Нужен .torrent файл.")
            return
        file = await document.get_file()
        path = Path(tempfile.gettempdir()) / document.file_name
        await file.download_to_drive(str(path))
        self.downloader.add_torrent_file(str(path))
        torrent_id = self.db.create_torrent(update.effective_chat.id, None, document.file_name)
        self.db.create_job(torrent_id)
        await update.message.reply_text("Торрент добавлен.")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        action, key = query.data.split(":", 1)
        if key not in self.pending:
            await query.edit_message_text("План уже не актуален.")
            return
        torrent_id, chat_id, root, plan = self.pending.pop(key)
        if action == "cancel":
            await query.edit_message_text("Отменено.")
            return
        moved = self.organizer.apply(root, plan)
        self.db.update_job(torrent_id, "done")
        await query.edit_message_text(self.organizer.summary(plan, moved))
        await context.bot.send_message(chat_id=chat_id, text="Готово.")

    async def poll(self, application: Application):
        while True:
            for torrent in self.downloader.completed():
                row = self.db.find_torrent_by_name(torrent.name)
                if row is None:
                    continue
                if self.db.has_done_job(row["id"]):
                    continue
                root = self.downloader.content_path(torrent)
                plan = self.organizer.make_plan(torrent.name, root)
                key = torrent.hash
                if float(plan.get("confidence", 0)) < 0.8:
                    self.pending[key] = (row["id"], row["telegram_user_id"], root, plan)
                    self.db.update_torrent(row["id"], "completed", root)
                    self.db.update_job(row["id"], "needs_confirmation", self.organizer.summary(plan))
                    keyboard = InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("Подтвердить", callback_data=f"confirm:{key}"),
                                InlineKeyboardButton("Отменить", callback_data=f"cancel:{key}"),
                            ]
                        ]
                    )
                    await application.bot.send_message(
                        chat_id=row["telegram_user_id"],
                        text=self.organizer.summary(plan),
                        reply_markup=keyboard,
                    )
                    continue
                moved = self.organizer.apply(root, plan)
                self.db.update_torrent(row["id"], "completed", root)
                self.db.update_job(row["id"], "done", self.organizer.summary(plan, moved))
                await application.bot.send_message(chat_id=row["telegram_user_id"], text=self.organizer.summary(plan, moved))
            await asyncio.sleep(60)

    def build(self):
        application = Application.builder().token(self.config.telegram_token).post_init(self.on_start).build()
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help))
        application.add_handler(CommandHandler("status", self.status))
        application.add_handler(CommandHandler("list", self.list))
        application.add_handler(CommandHandler("ask", self.ask))
        application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        return application

    async def on_start(self, application: Application):
        await application.bot.set_my_commands(
            [
                BotCommand("start", "начать"),
                BotCommand("status", "статус загрузок"),
                BotCommand("list", "список торрентов"),
                BotCommand("ask", "спросить модель"),
                BotCommand("help", "помощь"),
            ]
        )
        asyncio.create_task(self.poll(application))


def main():
    App().build().run_polling()


if __name__ == "__main__":
    main()
