import logging
import random
import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("❌ متغیر محیطی TOKEN تعریف نشده!")

logging.basicConfig(level=logging.INFO)

# خواندن کاراکترها از فایل
with open("characters.json", "r", encoding="utf-8") as f:
    CHARACTERS = json.load(f)

# وضعیت شخصیت فعال برای هر گروه
active_characters = {}

# وضعیت کاربران
try:
    with open("user_data.json", "r") as f:
        user_data = json.load(f)
except:
    user_data = {}

# ذخیره وضعیت کاربران
async def save_data():
    with open("user_data.json", "w") as f:
        json.dump(user_data, f)

# انتخاب کاراکتر تصادفی
def select_random_character():
    return random.choice(CHARACTERS)

# ارسال کاراکتر جدید به گروه
async def send_character(context: ContextTypes.DEFAULT_TYPE):
    group_id = context.job.chat_id
    character = select_random_character()
    active_characters[str(group_id)] = {
        "name": character["name"].lower(),
        "image": character["image"],
        "rank": character["rank"],
        "tries": 0,
        "max_tries": 15
    }
    await context.bot.send_photo(
        chat_id=group_id,
        photo=character["image"],
        caption=f"✨ یه کاراکتر جدید ظاهر شد!\n👤 نام: ???\n🏆 رنک: {character['rank']}\n⏳ با /catch [نام] امتحان کن! (تا 15 بار)"
    )

# اجرای اولیه: استارت گروه
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text("✅ ربات Anime Catcher فعال شد! الان کاراکتر می‌فرستم...")

    # همون لحظه یک کاراکتر بفرسته
    await send_character(context)

    # و هر 7 دقیقه تکرار شه (فقط یک بار ست می‌شه)
    context.job_queue.run_repeating(send_character, interval=420, first=420, chat_id=chat_id)

# گرفتن شخصیت با /catch
async def catch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or user_id

    if chat_id not in active_characters:
        await update.message.reply_text("❌ الان هیچ کاراکتری فعال نیست!")
        return

    if len(context.args) == 0:
        await update.message.reply_text("❗️ استفاده صحیح: /catch [نام شخصیت]")
        return

    guess = " ".join(context.args).strip().lower()
    character = active_characters[chat_id]

    if character["tries"] >= character["max_tries"]:
        await update.message.reply_text("🔥 این شخصیت از بین رفت. کسی نتونست بگیره!")
        del active_characters[chat_id]
        return

    character["tries"] += 1
    if guess == character["name"]:
        user_data.setdefault(user_id, {"username": username, "characters": []})
        user_data[user_id]["characters"].append({"name": character["name"], "rank": character["rank"]})
        await update.message.reply_text(f"🎉 آفرین @{username}! شخصیت {character['name']} رو گرفتی!")
        del active_characters[chat_id]
        await save_data()
    else:
        remaining = character["max_tries"] - character["tries"]
        await update.message.reply_text(f"❌ اشتباهه! تلاش باقی‌مانده: {remaining}")

        if remaining == 0:
            await update.message.reply_text(f"🔥 کاراکتر {character['name']} از بین رفت. هیچ‌کس درست حدس نزد.")
            del active_characters[chat_id]

# کلکسیون من
async def mycollection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in user_data:
        await update.message.reply_text("📦 هنوز هیچ کاراکتری نگرفتی!")
        return
    chars = user_data[user_id]["characters"]
    msg = f"📚 کلکسیون تو ({len(chars)} شخصیت):\n"
    for c in chars:
        msg += f"- {c['name']} ({c['rank']})\n"
    await update.message.reply_text(msg)

# اجرا
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("catch", catch))
    app.add_handler(CommandHandler("mycollection", mycollection))
 from telegram.error import TelegramError

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(msg="⚠️ خطا هنگام اجرای ربات:", exc_info=context.error)

app.add_error_handler(error_handler)
    app.run_polling()
