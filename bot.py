from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = "8867608436:AAGRMJj26VODPBnE0Vte4dAXQ6zVArc73iE"

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

app = Application.builder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
message = event.raw_text.lower()
 if "привет" in message:
        await event.reply("Привет 😈")
        await event.reply("_ЭТО АВТООТВЕТЧИК_")
app.run_polling()
