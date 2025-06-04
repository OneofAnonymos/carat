
# ✅ نسخه ساده اولیه ربات انیمه‌گیر
# ویژگی‌ها: ارسال کاراکتر + گرفتن با /catch + محدودیت 15 بار + چندگروهی + عکس + رنک

import logging
import random
import json
import asyncio
from telegram import Update, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

import os
TOKEN = os.getenv("TOKEN")

logging.basicConfig(level=logging.INFO)

# دادهٔ شخصیت‌ها از فایل
with open("characters.json", "r", encoding="utf-8") as f:
    CHARACTERS = json.load(f)

# وضعیت فعلی هر گروه
active_characters = {}

# وضعیت کاربران و شخصیت‌های گرفته‌شده
try:
    with open("user_data.json", "r") as f:
        user_data = json.load(f)
except:
    user_data = {}

# ذخیره وضعیت
async def save_data():
    with open("user_data.json", "w") as f:
        json.dump(user_data, f)

# ارسال شخصیت تصادفی به گروه
def select_random_character():
    return random.choice(CHARACTERS)

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ ربات Anime Catcher فعال شد! منتظر ظاهر شدن شخصیت‌ها باش 🧚‍♀️")

    chat_id = update.effective_chat.id
    context.job_queue.run_repeating(send_character, interval=300, first=5, chat_id=chat_id)

async def catch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or user_id

    if chat_id not in active_characters:
        await update.message.reply_text("❌ هیچ کاراکتری فعال نیست الان!")
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
        await update.message.reply_text(f"🎉 آفرین @{username}! تو شخصیت {character['name']} رو گرفتی!")
        del active_characters[chat_id]
        await save_data()
    else:
        remaining = character["max_tries"] - character["tries"]
        await update.message.reply_text(f"❌ اشتباهه! تلاش باقی‌مانده: {remaining}")

        if remaining == 0:
            await update.message.reply_text(f"🔥 کاراکتر {character['name']} از بین رفت. هیچ‌کس درست حدس نزد.")
            del active_characters[chat_id]

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

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("catch", catch))
    app.add_handler(CommandHandler("mycollection", mycollection))

    app.run_polling()
