import logging import random import json import os from telegram import Update from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


RARITY_WEIGHTS = { "Common": 60, "Rare": 25, "Epic": 10, "Supreme": 5 }



TOKEN = os.getenv("TOKEN") if not TOKEN: raise ValueError("❌ متغیر محیطی TOKEN تعریف نشده!")

logging.basicConfig(level=logging.INFO)



with open("characters.json", "r", encoding="utf-8") as f: CHARACTERS = json.load(f)


active_characters = {}



try: with open("user_data.json", "r") as f: user_data = json.load(f) except: user_data = {}



async def save_data(): with open("user_data.json", "w") as f: json.dump(user_data, f)



def select_random_character(): ranked_characters = {} for char in CHARACTERS: rank = char["rank"] ranked_characters.setdefault(rank, []).append(char)

selected_rank = random.choices(
    population=list(RARITY_WEIGHTS.keys()),
    weights=RARITY_WEIGHTS.values(),
    k=1
)[0]

return random.choice(ranked_characters[selected_rank])



async def send_character(context: ContextTypes.DEFAULT_TYPE, chat_id=None): if not chat_id: chat_id = context.job.chat_id

character = select_random_character()
active_characters[str(chat_id)] = {
    "name": character["name"].lower(),
    "image": character["image"],
    "rank": character["rank"],
    "tries": 0,
    "max_tries": 15
}
await context.bot.send_photo(
    chat_id=chat_id,
    photo=character["image"],
    caption=f"✨ یه کاراکتر جدید ظاهر شد!\n👤 نام: ???\n🏆 رنک: {character['rank']}\n⏳ با /catch [نام] امتحان کن! (تا 15 بار)"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): chat_id = update.effective_chat.id await update.message.reply_text("✅ ربات Anime Catcher فعال شد! الان کاراکتر می‌فرستم...") await send_character(context, chat_id=chat_id) context.job_queue.run_repeating(send_character, interval=420, first=420, chat_id=chat_id)


async def catch(update: Update, context: ContextTypes.DEFAULT_TYPE): chat_id = str(update.effective_chat.id) user_id = str(update.effective_user.id) username = update.effective_user.username or user_id

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



async def mycollection(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) if user_id not in user_data or not user_data[user_id]["characters"]: await update.message.reply_text("📦 هنوز هیچ کاراکتری نگرفتی!") return chars = user_data[user_id]["characters"] msg = f"📚 کلکسیون تو ({len(chars)} شخصیت):\n" for c in chars: msg += f"- {c['name']} ({c['rank']})\n" await update.message.reply_text(msg)


async def gift(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) if len(context.args) < 2: await update.message.reply_text("❗️ استفاده صحیح: /gift [username] [نام شخصیت]") return

target_username = context.args[0].lstrip("@")
char_name = " ".join(context.args[1:]).lower()

sender_chars = user_data.get(user_id, {}).get("characters", [])
for c in sender_chars:
    if c["name"].lower() == char_name:
        for target_id, data in user_data.items():
            if data["username"] == target_username:
                sender_chars.remove(c)
                data.setdefault("characters", []).append(c)
                await save_data()
                await update.message.reply_text(f"🎁 شخصیت {c['name']} با موفقیت به @{target_username} گیفت شد!")
                return
        await update.message.reply_text("❌ کاربری با این یوزرنیم پیدا نشد!")
        return

await update.message.reply_text("❌ شما این شخصیت رو ندارید!")



from telegram.error import TelegramError async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None: logging.error(msg="⚠️ خطا هنگام اجرای ربات:", exc_info=context.error)



if name == "main": app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("catch", catch))
app.add_handler(CommandHandler("mycollection", mycollection))
app.add_handler(CommandHandler("gift", gift))
app.add_error_handler(error_handler)

app.run_polling()

