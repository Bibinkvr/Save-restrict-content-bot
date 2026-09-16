import os
import asyncio
import random
import time
import shutil
from pyrogram import Client, filters, enums
from pyrogram.errors import (
    FloodWait,
    RPCError,
    UserNotParticipant,
    ChatAdminRequired,
    ChannelPrivate,
    PeerIdInvalid
)
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    CallbackQuery,
    InputMediaPhoto
)
from config import API_ID, API_HASH, ADMINS, FSUB_CHANNEL
from database.db import db
from plugins.strings import HELP_TXT, COMMANDS_TXT
from logger import LOGGER

logger = LOGGER(__name__)

ADMIN_URL = "https://t.me/H4CK3R_OO7"
DEFAULT_BANNER = "https://i.postimg.cc/5tB8b7DN/Chat-GPT-Image-Sep-16-2026-08-25-15-PM.png"

REACTIONS = [
    "👍", "❤️", "🔥", "🥰", "👏", "😁", "🎉", "🤩", "⚡", "💯"
]

class script:
    FSUB_TXT = """<b>📢 Channel Subscription Required</b>
<b>👋 Hello {},</b>

<blockquote>To access <b>ContentSaver Bot</b> and download restricted content, you must join our official updates channel.

<i>Join the channel below, then click <b>'🔄 Try Again'</b> to continue!</i></blockquote>
"""

    START_TXT = """<b>👋 Hello {},</b>
<b>🤖 I am <a href=https://t.me/{}>{}</a> (ContentSaver)</b>
<i>Your Fast & Secure Content Saver Bot.</i>
<blockquote><b>🚀 System Status: 🟢 Online</b>
<b>⚡ Performance: High-Speed Async Engine</b>
<b>🔐 Security: End-to-End Encrypted</b>
<b>📊 Uptime: 99.9% Guaranteed</b></blockquote>
<b>👇 Select an Option Below to Get Started:</b>
"""

    HELP_TXT = HELP_TXT

    ABOUT_TXT = """<b>ℹ️ About ContentSaver</b>
<blockquote><b>╭────[ 🧩 Technical Stack ]────⍟</b>
<b>├⍟ 🤖 Bot : ContentSaver Bot</b>
<b>├⍟ 👑 Admin : <a href='https://t.me/H4CK3R_OO7'>@H4CK3R_OO7</a></b>
<b>├⍟ 📚 Library : <a href='https://docs.pyrogram.org/'>Pyrogram Async</a></b>
<b>├⍟ 🐍 Language : <a href='https://www.python.org/'>Python 3</a></b>
<b>├⍟ 🗄 Database : <a href='https://www.mongodb.com/'>MongoDB Atlas</a></b>
<b>├⍟ 📡 Hosting : Dedicated High-Speed VPS</b>
<b>╰───────────────⍟</b></blockquote>
"""

    PREMIUM_TEXT = """<b>💎 Premium Membership Plans</b>
<b>Unlock Unlimited Access & Advanced Features!</b>
<blockquote><b>✨ Key Benefits:</b>
<b>♾️ Unlimited Daily Downloads</b>
<b>📂 Support for 4GB+ File Sizes</b>
<b>⚡ Instant Processing (Zero Delay)</b>
<b>🖼 Customizable Thumbnails</b>
<b>📝 Personalized Captions</b>
<b>🛂 24/7 Priority Support</b></blockquote>
<blockquote><b>💳 Pricing Options:</b></blockquote>
• <b>1 Month Plan:</b> ₹50 / $1
• <b>3 Months Plan:</b> ₹120 / $2.5

<i>👉 Click below to contact Admin for activation:</i>
"""

    PROGRESS_BAR = """\
<b>⚡ {action} Task...</b>
<blockquote>
<b>Progress: {bar} {percentage:.1f}%</b>
<b>🚀 Speed:</b> <code>{speed}/s</code>
<b>💾 Size:</b> <code>{current} of {total}</code>
<b>⏱ Elapsed:</b> <code>{elapsed}</code>
<b>⏳ ETA:</b> <code>{eta}</code>
</blockquote>
"""

    LIMIT_REACHED = """<b>🚫 Daily Limit Exceeded</b>
<b>Your 10 free saves for today have been used.</b>
<i>Quota resets automatically after 24 hours from first download.</i>
<blockquote><b>🔓 Upgrade to Premium for Unlimited Access!</b></blockquote>
"""

    SIZE_LIMIT = """<b>⚠️ File Size Exceeded</b>
<b>Free tier is limited to 2GB per file.</b>
<blockquote><b>🔓 Upgrade to Premium for 4GB+ files!</b></blockquote>
"""

def humanbytes(size: int | float) -> str:
    if not size:
        return "0 B"
    power = 2**10
    n = 0
    dic_power_n = {0: "", 1: "K", 2: "M", 3: "G", 4: "T"}
    while size >= power and n < 4:
        size /= power
        n += 1
    unit = dic_power_n.get(n, "")
    return f"{round(size, 2)} {unit}B" if unit else f"{round(size, 2)} B"

def time_formatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + "d, ") if days else "") +
        ((str(hours) + "h, ") if hours else "") +
        ((str(minutes) + "m, ") if minutes else "") +
        ((str(seconds) + "s, ") if seconds else "")
    )
    return tmp[:-2] if tmp else "0s"

def apply_word_filters(text: str | None, delete_words: list[str], replace_words: dict[str, str]) -> str:
    """Applies word deletion and word replacement filters to captions/names."""
    if not text:
        return ""
    for word in delete_words:
        if word:
            text = text.replace(word, "")
    for target, replacement in replace_words.items():
        if target:
            text = text.replace(target, replacement)
    return text.strip()

class BatchState:
    IS_BATCH = {}

class ProgressTracker:
    """In-memory throttled progress handler to prevent Telegram rate limits and file locks."""
    def __init__(self, bot: Client, status_msg: Message, action: str, user_id: int):
        self.bot = bot
        self.status_msg = status_msg
        self.action = action
        self.user_id = user_id
        self.last_update = 0.0
        self.start_time = time.time()

    async def __call__(self, current: int, total: int):
        if BatchState.IS_BATCH.get(self.user_id, False):
            raise asyncio.CancelledError("Batch task cancelled by user.")

        now = time.time()
        if (now - self.last_update) < 4.0 and current < total:
            return
        self.last_update = now

        percentage = (current * 100 / total) if total > 0 else 0
        elapsed_sec = max(0.1, now - self.start_time)
        speed = current / elapsed_sec
        eta = (total - current) / speed if speed > 0 else 0

        filled_length = int(percentage / 5)
        bar = "█" * filled_length + " " * (20 - filled_length)

        status_text = script.PROGRESS_BAR.format(
            action=self.action,
            bar=bar,
            percentage=percentage,
            current=humanbytes(current),
            total=humanbytes(total),
            speed=humanbytes(speed),
            elapsed=time_formatter(int(elapsed_sec * 1000)),
            eta=time_formatter(int(eta * 1000))
        )

        try:
            await self.status_msg.edit_text(status_text, parse_mode=enums.ParseMode.HTML)
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            pass

def get_message_type(msg: Message) -> str | None:
    if getattr(msg, "document", None): return "Document"
    if getattr(msg, "video", None): return "Video"
    if getattr(msg, "photo", None): return "Photo"
    if getattr(msg, "audio", None): return "Audio"
    if getattr(msg, "text", None): return "Text"
    return None

@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    user_id = message.from_user.id
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)
    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except Exception:
        pass

    buttons = [
        [
            InlineKeyboardButton("💎 Buy Premium", callback_data="buy_premium"),
            InlineKeyboardButton("🆘 Help & Guide", callback_data="help_btn")
        ],
        [
            InlineKeyboardButton("⚙️ Settings Panel", callback_data="settings_btn"),
            InlineKeyboardButton("ℹ️ About Bot", callback_data="about_btn")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    bot = await client.get_me()
    await client.send_photo(
        chat_id=message.chat.id,
        photo=DEFAULT_BANNER,
        caption=script.START_TXT.format(message.from_user.mention, bot.username, bot.first_name),
        reply_markup=reply_markup,
        reply_to_message_id=message.id,
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    buttons = [[InlineKeyboardButton("❌ Close Menu", callback_data="close_btn")]]
    await client.send_message(
        chat_id=message.chat.id,
        text=script.HELP_TXT,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML
    )


@Client.on_message(filters.command(["cancel"]))
async def send_cancel(client: Client, message: Message):
    BatchState.IS_BATCH[message.from_user.id] = True
    await message.reply_text("❌ <b>Task Cancelled Successfully.</b>", parse_mode=enums.ParseMode.HTML)

async def settings_panel(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    is_premium = await db.check_premium(user_id)
    badge = "💎 Premium Member" if is_premium else "👤 Standard User"

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 Command List", callback_data="cmd_list_btn")],
        [InlineKeyboardButton("📊 Usage Stats", callback_data="user_stats_btn")],
        [InlineKeyboardButton("🗑 Dump Chat Settings", callback_data="dump_chat_btn")],
        [InlineKeyboardButton("🖼 Manage Thumbnail", callback_data="thumb_btn")],
        [InlineKeyboardButton("📝 Edit Caption", callback_data="caption_btn")],
        [InlineKeyboardButton("⬅️ Return to Home", callback_data="start_btn")]
    ])

    text = (
        f"<b>⚙️ Settings Dashboard</b>\n\n"
        f"<b>Account Status:</b> {badge}\n"
        f"<b>User ID:</b> <code>{user_id}</code>\n\n"
        f"<i>Customize and manage your bot preferences below:</i>"
    )

    await callback_query.edit_message_caption(
        caption=text,
        reply_markup=buttons,
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_message(filters.text & filters.private & ~filters.regex("^/"))
async def save(client: Client, message: Message):
    if "https://t.me/" not in message.text:
        return

    user_id = message.from_user.id

    if await db.is_banned(user_id):
        return await message.reply_text("<b>🚫 You are banned from using this bot.</b>", parse_mode=enums.ParseMode.HTML)

    if await db.check_limit(user_id):
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("💎 Upgrade to Premium", callback_data="buy_premium")]])
        return await message.reply_photo(
            photo=DEFAULT_BANNER,
            caption=script.LIMIT_REACHED,
            reply_markup=btn,
            parse_mode=enums.ParseMode.HTML
        )

    if BatchState.IS_BATCH.get(user_id) is False:
        return await message.reply_text(
            "<b>⚠️ A Task is Currently Processing.</b>\n<i>Please wait for completion or use /cancel to stop.</i>",
            parse_mode=enums.ParseMode.HTML
        )

    datas = message.text.split("/")
    temp = datas[-1].replace("?single", "").split("-")
    try:
        from_id = int(temp[0].strip())
        to_id = int(temp[1].strip()) if len(temp) > 1 else from_id
    except ValueError:
        return await message.reply_text("❌ <b>Invalid Telegram link format.</b>", parse_mode=enums.ParseMode.HTML)

    is_private_link = "https://t.me/c/" in message.text
    is_batch = "https://t.me/b/" in message.text
    is_public_link = not is_private_link and not is_batch

    BatchState.IS_BATCH[user_id] = False

    # 1. Public direct copy (No user session required)
    if is_public_link:
        username = datas[3]
        for msgid in range(from_id, to_id + 1):
            if BatchState.IS_BATCH.get(user_id, False):
                break
            try:
                copied_msg = await client.copy_message(
                    chat_id=message.chat.id,
                    from_chat_id=username,
                    message_id=msgid,
                    reply_to_message_id=message.id
                )
                await db.add_traffic(user_id)
                # Forward to Dump Chat if configured
                dump_chat = await db.get_dump_chat(user_id)
                if dump_chat:
                    try:
                        await copied_msg.copy(chat_id=dump_chat)
                    except Exception as e:
                        logger.warning(f"Could not forward public message to dump chat {dump_chat}: {e}")
                await asyncio.sleep(1.5)
            except Exception as e:
                logger.debug(f"Copy message failed: {e}")
        BatchState.IS_BATCH[user_id] = True
        return

    # 2. Private/Restricted link (User session required)
    user_data = await db.get_session(user_id)
    if user_data is None:
        BatchState.IS_BATCH[user_id] = True
        return await message.reply(
            "<b>🔒 Authentication Required</b>\n\n"
            "<i>Access to this content requires login.</i>\n"
            "<i>Use /login to securely connect your account.</i>",
            parse_mode=enums.ParseMode.HTML
        )

    acc = Client(
        f"session_user_{user_id}",
        session_string=user_data,
        api_hash=API_HASH,
        api_id=API_ID,
        in_memory=True,
        max_concurrent_transmissions=10
    )

    try:
        await acc.connect()
    except Exception as e:
        BatchState.IS_BATCH[user_id] = True
        return await message.reply(
            f"<b>❌ Authentication Failed</b>\n\n<i>Your session may have expired. Please /logout and /login again.</i>\n<code>{e}</code>",
            parse_mode=enums.ParseMode.HTML
        )

    try:
        for msgid in range(from_id, to_id + 1):
            if BatchState.IS_BATCH.get(user_id, False):
                break

            if is_private_link:
                chat_target = int("-100" + datas[4])
            elif is_batch:
                chat_target = datas[4]
            else:
                chat_target = datas[3]

            await handle_restricted_content(client, acc, message, chat_target, msgid)
            await asyncio.sleep(2)
    finally:
        # Guarantee client disconnection to prevent socket & memory leaks
        BatchState.IS_BATCH[user_id] = True
        try:
            if acc.is_connected:
                await acc.disconnect()
        except Exception as e:
            logger.debug(f"Error disconnecting client: {e}")

async def handle_restricted_content(client: Client, acc: Client, message: Message, chat_target, msgid: int):
    user_id = message.from_user.id
    try:
        msg: Message = await acc.get_messages(chat_target, msgid)
    except Exception as e:
        logger.error(f"Error fetching message {msgid}: {e}")
        return

    if not msg or msg.empty:
        return

    msg_type = get_message_type(msg)
    if not msg_type:
        return

    file_size = 0
    if msg_type == "Document" and msg.document: file_size = msg.document.file_size
    elif msg_type == "Video" and msg.video: file_size = msg.video.file_size
    elif msg_type == "Audio" and msg.audio: file_size = msg.audio.file_size

    if file_size > FREE_LIMIT_SIZE:
        if not await db.check_premium(user_id):
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("💎 Upgrade to Premium", callback_data="buy_premium")]])
            return await client.send_message(
                message.chat.id,
                script.SIZE_LIMIT,
                reply_markup=btn,
                parse_mode=enums.ParseMode.HTML
            )

    # Simple Text Message
    if msg_type == "Text":
        try:
            sent_text = await client.send_message(
                message.chat.id,
                msg.text,
                entities=msg.entities,
                parse_mode=enums.ParseMode.HTML
            )
            await db.add_traffic(user_id)
            dump_chat = await db.get_dump_chat(user_id)
            if dump_chat:
                try:
                    await sent_text.copy(chat_id=dump_chat)
                except Exception:
                    pass
            return
        except Exception as e:
            logger.error(f"Error forwarding text: {e}")
            return

    await db.add_traffic(user_id)
    smsg = await client.send_message(
        message.chat.id,
        "<b>⬇️ Starting Download...</b>",
        reply_to_message_id=message.id,
        parse_mode=enums.ParseMode.HTML
    )

    temp_dir = f"downloads/{message.id}_{msgid}"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir, exist_ok=True)

    try:
        down_progress = ProgressTracker(client, smsg, "Downloading", user_id)
        file_path = await acc.download_media(
            msg,
            file_name=f"{temp_dir}/",
            progress=down_progress
        )

        if not file_path or not os.path.exists(file_path):
            return await smsg.edit_text("❌ <b>Download Failed: File not found.</b>", parse_mode=enums.ParseMode.HTML)

        # Thumbnail handling
        ph_path = None
        thumb_id = await db.get_thumbnail(user_id)
        if thumb_id:
            try:
                ph_path = await client.download_media(thumb_id, file_name=f"{temp_dir}/custom_thumb.jpg")
            except Exception as e:
                logger.error(f"Failed to download custom thumb: {e}")

        if not ph_path:
            try:
                if msg_type == "Video" and msg.video and msg.video.thumbs:
                    ph_path = await acc.download_media(msg.video.thumbs[0].file_id, file_name=f"{temp_dir}/thumb.jpg")
                elif msg_type == "Document" and msg.document and msg.document.thumbs:
                    ph_path = await acc.download_media(msg.document.thumbs[0].file_id, file_name=f"{temp_dir}/thumb.jpg")
            except Exception:
                pass

        # Caption & Word Filters
        filename = os.path.basename(file_path)
        delete_words = await db.get_delete_words(user_id)
        replace_words = await db.get_replace_words(user_id)

        custom_caption = await db.get_caption(user_id)
        if custom_caption:
            base_caption = custom_caption.format(filename=filename, size=humanbytes(file_size))
        else:
            base_caption = msg.caption if msg.caption else ""

        final_caption = apply_word_filters(base_caption, delete_words, replace_words)

        # Upload phase
        up_progress = ProgressTracker(client, smsg, "Uploading", user_id)
        sent_media = None

        if msg_type == "Document":
            sent_media = await client.send_document(
                message.chat.id,
                file_path,
                thumb=ph_path,
                caption=final_caption,
                progress=up_progress
            )
        elif msg_type == "Video":
            duration = msg.video.duration if msg.video else 0
            width = msg.video.width if msg.video else 0
            height = msg.video.height if msg.video else 0
            sent_media = await client.send_video(
                message.chat.id,
                file_path,
                duration=duration,
                width=width,
                height=height,
                thumb=ph_path,
                caption=final_caption,
                supports_streaming=True,
                progress=up_progress
            )
        elif msg_type == "Audio":
            sent_media = await client.send_audio(
                message.chat.id,
                file_path,
                thumb=ph_path,
                caption=final_caption,
                progress=up_progress
            )
        elif msg_type == "Photo":
            sent_media = await client.send_photo(
                message.chat.id,
                file_path,
                caption=final_caption
            )

        # Dump Chat Forwarding
        if sent_media:
            dump_chat = await db.get_dump_chat(user_id)
            if dump_chat:
                try:
                    await sent_media.copy(chat_id=dump_chat)
                except Exception as e:
                    logger.warning(f"Failed to forward uploaded media to dump chat {dump_chat}: {e}")

        await smsg.delete()

    except asyncio.CancelledError:
        await smsg.edit_text("❌ <b>Task Cancelled.</b>", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        logger.error(f"Upload process failed: {e}")
        await smsg.edit_text(f"❌ <b>Process Failed:</b> <code>{e}</code>", parse_mode=enums.ParseMode.HTML)
    finally:
        # Guarantee disk cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

@Client.on_callback_query()
async def button_callbacks(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    message = callback_query.message
    if not message:
        return

    if data == "settings_btn":
        await settings_panel(client, callback_query)
    elif data == "buy_premium":
        buttons = [
            [InlineKeyboardButton("💬 Contact Admin (@H4CK3R_OO7)", url="https://t.me/H4CK3R_OO7")],
            [InlineKeyboardButton("⬅️ Back to Home", callback_data="start_btn")]
        ]
        await client.edit_message_media(
            chat_id=message.chat.id,
            message_id=message.id,
            media=InputMediaPhoto(
                media=DEFAULT_BANNER,
                caption=script.PREMIUM_TEXT
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif data == "help_btn":
        buttons = [[InlineKeyboardButton("⬅️ Back to Home", callback_data="start_btn")]]
        await client.edit_message_caption(
            chat_id=message.chat.id,
            message_id=message.id,
            caption=script.HELP_TXT,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )
    elif data == "about_btn":
        buttons = [[InlineKeyboardButton("⬅️ Back to Home", callback_data="start_btn")]]
        await client.edit_message_caption(
            chat_id=message.chat.id,
            message_id=message.id,
            caption=script.ABOUT_TXT,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )
    elif data == "start_btn":
        bot = await client.get_me()
        buttons = [
            [
                InlineKeyboardButton("💎 Buy Premium", callback_data="buy_premium"),
                InlineKeyboardButton("🆘 Help & Guide", callback_data="help_btn")
            ],
            [
                InlineKeyboardButton("⚙️ Settings Panel", callback_data="settings_btn"),
                InlineKeyboardButton("ℹ️ About Bot", callback_data="about_btn")
            ]
        ]
        await client.edit_message_media(
            chat_id=message.chat.id,
            message_id=message.id,
            media=InputMediaPhoto(
                media=DEFAULT_BANNER,
                caption=script.START_TXT.format(callback_query.from_user.mention, bot.username, bot.first_name)
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif data == "close_btn":
        await message.delete()
    elif data in ["cmd_list_btn", "user_stats_btn", "dump_chat_btn", "thumb_btn", "caption_btn"]:
        pass

    await callback_query.answer()
