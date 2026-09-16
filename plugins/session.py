import asyncio
import time
from pyrogram import Client, filters, enums
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from pyrogram.errors import (
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)
from config import API_ID, API_HASH
from database.db import db
from logger import LOGGER

logger = LOGGER(__name__)

LOGIN_STATE = {}
LOGIN_TIMEOUT_SECONDS = 300  # 5 minutes TTL

cancel_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton("❌ Cancel")]],
    resize_keyboard=True
)
remove_keyboard = ReplyKeyboardRemove()

PROGRESS_STEPS = {
    "WAITING_PHONE": "🟢 Phone Number → 🔵 Code → 🔵 Password",
    "WAITING_CODE": "✅ Phone Number → 🟢 Code → 🔵 Password",
    "WAITING_PASSWORD": "✅ Phone Number → ✅ Code → 🟢 Password"
}

LOADING_FRAMES = [
    "🔄 Connecting •••",
    "🔄 Connecting ••○",
    "🔄 Connecting •○○",
    "🔄 Connecting ○○○",
    "🔄 Connecting ○○•",
    "🔄 Connecting ○••",
    "🔄 Connecting •••"
]

async def cleanup_login(user_id: int):
    """Safely terminates temporary client connections and clears user state."""
    state = LOGIN_STATE.pop(user_id, None)
    if state and "data" in state and "client" in state["data"]:
        client: Client = state["data"]["client"]
        try:
            if client.is_connected:
                await client.disconnect()
        except Exception as e:
            logger.debug(f"Error disconnecting temporary login client for {user_id}: {e}")

async def animate_loading(message: Message, duration: int = 5):
    for _ in range(duration):
        for frame in LOADING_FRAMES:
            try:
                await message.edit_text(f"<b>{frame}</b>", parse_mode=enums.ParseMode.HTML)
                await asyncio.sleep(0.5)
            except Exception:
                return

@Client.on_message(filters.private & filters.command("login"))
async def login_start(client: Client, message: Message):
    user_id = message.from_user.id
   
    user_data = await db.get_session(user_id)
    if user_data:
        return await message.reply(
            "<b>✅ You're already logged in! 🎉</b>\n\n"
            "To switch accounts, first use /logout.",
            parse_mode=enums.ParseMode.HTML
        )
   
    await cleanup_login(user_id)
    LOGIN_STATE[user_id] = {
        "step": "WAITING_PHONE",
        "timestamp": time.time(),
        "data": {}
    }
   
    progress = PROGRESS_STEPS["WAITING_PHONE"]
    await message.reply(
        f"<b>👋 Let's log in to your Telegram account 🌟</b>\n\n"
        f"<i>Progress: {progress}</i>\n\n"
        "📞 Please send your <b>Telegram Phone Number</b> with country code.\n\n"
        "<blockquote>Example: +919876543210</blockquote>\n\n"
        "<i>💡 Your number is used only for verification and is kept secure. 🔒</i>\n\n"
        "❌ Tap the <b>Cancel</b> button or send /cancel to stop.",
        parse_mode=enums.ParseMode.HTML,
        reply_markup=cancel_keyboard
    )

@Client.on_message(filters.private & filters.command("logout"))
async def logout(client: Client, message: Message):
    user_id = message.from_user.id
    await cleanup_login(user_id)
    await db.set_session(user_id, session=None)
    await message.reply(
        "<b>🚪 Logout Successful! 👋</b>\n\n"
        "<i>Your session has been cleared. You can log in again anytime! 🔄</i>",
        parse_mode=enums.ParseMode.HTML,
        reply_markup=remove_keyboard
    )

@Client.on_message(filters.private & filters.command(["cancel", "cancellogin"]))
async def cancel_login(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in LOGIN_STATE:
        await cleanup_login(user_id)
        await message.reply(
            "<b>❌ Login process cancelled.</b>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=remove_keyboard
        )

async def check_login_state(_, __, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if not user_id or user_id not in LOGIN_STATE:
        return False
    # Check TTL timeout
    if time.time() - LOGIN_STATE[user_id].get("timestamp", 0) > LOGIN_TIMEOUT_SECONDS:
        asyncio.create_task(cleanup_login(user_id))
        return False
    return True

login_state_filter = filters.create(check_login_state)

@Client.on_message(filters.private & filters.text & login_state_filter & ~filters.command(["cancel", "cancellogin"]))
async def login_handler(bot: Client, message: Message):
    user_id = message.from_user.id
    text = message.text
    state = LOGIN_STATE.get(user_id)
    if not state:
        return

    state["timestamp"] = time.time()  # Refresh activity
    step = state["step"]
    progress = PROGRESS_STEPS.get(step, "")
   
    if text.strip().lower() in ["❌ cancel", "/cancel"]:
        await cleanup_login(user_id)
        return await message.reply(
            "<b>❌ Login process cancelled.</b>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=remove_keyboard
        )
   
    if step == "WAITING_PHONE":
        phone_number = text.replace(" ", "").strip()
       
        temp_client = Client(
            name=f"session_{user_id}",
            api_id=API_ID,
            api_hash=API_HASH,
            in_memory=True
        )
       
        status_msg = await message.reply(
            f"<b>🔄 Connecting to Telegram... 🌐</b>\n\n<i>Progress: {progress}</i>",
            parse_mode=enums.ParseMode.HTML
        )
       
        animation_task = asyncio.create_task(animate_loading(status_msg))
       
        try:
            await temp_client.connect()
        except Exception as e:
            animation_task.cancel()
            await cleanup_login(user_id)
            return await status_msg.edit(
                f"<b>❌ Connection Failed:</b> <code>{e}</code>\n<i>Please try /login again.</i>",
                parse_mode=enums.ParseMode.HTML
            )

        animation_task.cancel()
       
        try:
            code = await temp_client.send_code(phone_number)
            state["data"]["client"] = temp_client
            state["data"]["phone"] = phone_number
            state["data"]["hash"] = code.phone_code_hash
            state["step"] = "WAITING_CODE"
            progress = PROGRESS_STEPS["WAITING_CODE"]
           
            await status_msg.edit(
                f"<b>📩 OTP Sent to your Telegram app! 📲</b>\n\n"
                f"<i>Progress: {progress}</i>\n\n"
                "Please check your Telegram app and send the verification code.\n\n"
                "<b>Send with spaces:</b> <code>1 2 3 4 5</code>\n\n"
                "<blockquote>Adding spaces prevents Telegram from auto-deleting the code. 💡</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
        except PhoneNumberInvalid:
            await cleanup_login(user_id)
            await status_msg.edit(
                "<b>❌ Invalid phone number format.</b>\n\n"
                "Please try again (e.g., +919876543210) using /login.",
                parse_mode=enums.ParseMode.HTML
            )
        except Exception as e:
            await cleanup_login(user_id)
            await status_msg.edit(
                f"<b>❌ Error:</b> <code>{e}</code>\n\nPlease start again with /login.",
                parse_mode=enums.ParseMode.HTML
            )
   
    elif step == "WAITING_CODE":
        phone_code = text.replace(" ", "").strip()
        temp_client: Client = state["data"]["client"]
        phone_number = state["data"]["phone"]
        phone_hash = state["data"]["hash"]
       
        status_msg = await message.reply(
            f"<b>🔍 Verifying code... 🔍</b>\n\n<i>Progress: {progress}</i>",
            parse_mode=enums.ParseMode.HTML
        )
       
        animation_task = asyncio.create_task(animate_loading(status_msg, duration=3))
       
        try:
            await temp_client.sign_in(phone_number, phone_hash, phone_code)
            animation_task.cancel()
            await finalize_login(status_msg, temp_client, user_id)
        except PhoneCodeInvalid:
            animation_task.cancel()
            await status_msg.edit(
                "<b>❌ Invalid verification code.</b>\n\n"
                f"<i>Progress: {progress}</i>\n\nPlease double check and enter the code again.",
                parse_mode=enums.ParseMode.HTML
            )
        except PhoneCodeExpired:
            animation_task.cancel()
            await cleanup_login(user_id)
            await status_msg.edit(
                "<b>⏰ Code expired.</b>\n\nPlease restart with /login.",
                parse_mode=enums.ParseMode.HTML
            )
        except SessionPasswordNeeded:
            animation_task.cancel()
            state["step"] = "WAITING_PASSWORD"
            progress = PROGRESS_STEPS["WAITING_PASSWORD"]
            await status_msg.edit(
                f"<b>🔐 Two-Step Verification Detected 🔒</b>\n\n"
                f"<i>Progress: {progress}</i>\n\n"
                "Please enter your Two-Step Verification <b>Password</b>.",
                parse_mode=enums.ParseMode.HTML
            )
        except Exception as e:
            animation_task.cancel()
            await cleanup_login(user_id)
            await status_msg.edit(
                f"<b>❌ Verification Failed:</b> <code>{e}</code>\n\nPlease try /login again.",
                parse_mode=enums.ParseMode.HTML
            )
   
    elif step == "WAITING_PASSWORD":
        password = text.strip()
        temp_client: Client = state["data"]["client"]
       
        status_msg = await message.reply(
            f"<b>🔑 Checking password... 🔑</b>\n\n<i>Progress: {progress}</i>",
            parse_mode=enums.ParseMode.HTML
        )
       
        animation_task = asyncio.create_task(animate_loading(status_msg, duration=3))
       
        try:
            await temp_client.check_password(password=password)
            animation_task.cancel()
            await finalize_login(status_msg, temp_client, user_id)
        except PasswordHashInvalid:
            animation_task.cancel()
            await status_msg.edit(
                "<b>❌ Incorrect password.</b>\n\n"
                f"<i>Progress: {progress}</i>\n\nPlease enter the correct password.",
                parse_mode=enums.ParseMode.HTML
            )
        except Exception as e:
            animation_task.cancel()
            await cleanup_login(user_id)
            await status_msg.edit(
                f"<b>❌ Authentication Error:</b> <code>{e}</code>\n\nPlease try /login again.",
                parse_mode=enums.ParseMode.HTML
            )

async def finalize_login(status_msg: Message, temp_client: Client, user_id: int):
    try:
        session_string = await temp_client.export_session_string()
        await cleanup_login(user_id)
        await db.set_session(user_id, session=session_string)
       
        await status_msg.edit(
            "<b>🎉 Login Successful! 🌟</b>\n\n"
            "<i>Your account session is authenticated and saved securely.</i>\n\n"
            "You can now send any restricted post link! 🚀",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=remove_keyboard
        )
    except Exception as e:
        await cleanup_login(user_id)
        await status_msg.edit(
            f"<b>❌ Failed to save session:</b> <code>{e}</code>\n\nPlease try /login again.",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=remove_keyboard
        )