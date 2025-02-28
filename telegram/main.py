import os
import logging
import random
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from openai import OpenAI
from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    raise ValueError("Missing API key: Set OPENROUTER_API_KEY in .env file")

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# OpenRouter AI Client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

# Logging
logging.basicConfig(level=logging.INFO)

# Roast levels
ROAST_LEVELS = {
    "mild": "Give a playful, funny roast in Nigerian Pidgin. Make it teasing but not too harsh.",
    "medium": "Roast the user HARD in Nigerian Pidgin. Be brutal, no pity, but still funny.",
    "savage": "Forget jokes. Drag this person mercilessly in Nigerian Pidgin. Be heartless, ruthless, and disrespectful. No mercy, no limits. Make them feel completely worthless."
}

# Gender-based roast variations
MALE_ROASTS = [
    "E be like say your barber na blind man, which kind haircut be this? 😂",
    "You dey form big man but you still dey borrow data. Guy, rest abeg! 😭",
    "Your WhatsApp deep quotes no fit help your life. Abeg, go hustle! 🤡",
]
FEMALE_ROASTS = [
    "Without Snapchat filter, you be like expired bread. E sweet you? 🤣",
    "You dey dress like upcoming TikTok influencer wey no get sponsor. 😭",
    "You dey shout ‘men are trash’ but na one broke guy still dey make you cry. 😂",
]

# Store user data
user_data = {}


@dp.message(CommandStart())
async def start_command(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👨 Male", callback_data="gender_male")],
            [InlineKeyboardButton(text="👩 Female", callback_data="gender_female")],
        ]
    )
    await message.answer("Oya Welcome! 🔥 Pick ya gender make we start wahala:", reply_markup=keyboard)


@dp.callback_query()
async def handle_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data

    # Handle gender selection
    if data in ["gender_male", "gender_female"]:
        user_data[user_id] = {"gender": "male" if data == "gender_male" else "female"}

        # Show roast level selection
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔥 Mild", callback_data="level_mild")],
                [InlineKeyboardButton(text="😈 Medium", callback_data="level_medium")],
                [InlineKeyboardButton(text="💀 Savage", callback_data="level_savage")],
            ]
        )
        await callback_query.message.edit_text("Oya! Pick your roast level, make wahala start:", reply_markup=keyboard)

    # Handle roast level selection
    elif data.startswith("level_"):
        roast_level = data.split("_")[1]
        if user_id not in user_data:
            await callback_query.message.answer("Abeg, start with /start first!")
            return

        user_data[user_id]["level"] = roast_level

        # Move forward and tell the user to send a message
        await callback_query.message.edit_text("Oya send your message. Make I disgrace you small. 😂🔥")


@dp.message()
async def handle_message(message: Message):
    try:
        user_id = message.from_user.id

        if user_id not in user_data or "gender" not in user_data[user_id] or "level" not in user_data[user_id]:
            await message.reply("Abeg, start with /start first, no dey jump step.")
            return

        gender = user_data[user_id]["gender"]
        level = user_data[user_id]["level"]
        user_message = message.text.strip()

        roast_instruction = ROAST_LEVELS[level]
        gender_instruction = random.choice(MALE_ROASTS if gender == "male" else FEMALE_ROASTS)

        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://yourwebsite.com",
                "X-Title": "WahalaBot",
            },
            extra_body={},
            model="google/gemini-2.0-flash-lite-preview-02-05:free",
            messages=[
                {"role": "system", "content": [{"type": "text", "text": f"Imagine say you be Nigerian street guy wey no get filter. You dey for roast battle, and your only mission na to **disgrace** your opponent. Drag dem like NEPA pole, finish dem life. Be **petty, disrespectful, and brutal**, but use sarcasm so e go sound like 'joke'. Forget kindness, na wahala zone we dey! {roast_instruction} {gender_instruction}"}]},
                {"role": "user", "content": [{"type": "text", "text": user_message}]},
            ]
        )

        # ✅ FIX: Properly extract the AI's response without using indexing
        roast_response = response.choices[0].message.content

        await message.reply(roast_response)

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        await message.reply("Something don go wrong o! Try again later.")


# FastAPI with bot startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(dp.start_polling(bot))
    yield
    await bot.session.close()


app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "Bot is running"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
