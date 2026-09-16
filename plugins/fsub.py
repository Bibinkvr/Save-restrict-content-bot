import asyncio
import os
from pyrogram import Client, filters, enums
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChatJoinRequest,
    InputMediaPhoto
)
from pyrogram.errors import (
    UserNotParticipant,
    ChatAdminRequired,
    ChannelPrivate,
    PeerIdInvalid,
    FloodWait
)
from config import ADMINS, FSUB_CHANNELS, FSUB_AUTO_APPROVE
from database.db import db
from logger import LOGGER

logger = LOGGER(__name__)

DEFAULT_BANNER = "https://i.postimg.cc/5tB8b7DN/Chat-GPT-Image-Sep-16-2026-08-25-15-PM.png"

# In-memory invite link cache to prevent FloodWait
INVITE_CACHE = {}

# ======================================================
# 1. MODERN JOIN REQUEST AUTO-APPROVER
# ======================================================

@Client.on_chat_join_request()
async def auto_approve_join_request(client: Client, join_req: ChatJoinRequest):
    """
    Modern Telegram Join Request Handler:
    Automatically approves incoming join requests and immediately sends the
    verified start dashboard to the user without requiring them to click verify!
    """
    user_id = join_req.from_user.id
    chat_id = join_req.chat.id
    
    # 1. Record join request in database (Auto-Verified)
    await db.record_join_request(user_id, chat_id)
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, join_req.from_user.first_name)
    
    # 2. Approve join request if auto-approve is enabled
    auto_approve = await db.get_auto_approve()
    if auto_approve:
        try:
            await client.approve_chat_join_request(chat_id, user_id)
            logger.info(f"Auto-approved join request for user {user_id} in chat {chat_id}")
        except Exception as e:
            logger.debug(f"Could not auto-approve join request: {e}")

    # 3. Automatically send verified start dashboard in PM (Zero manual clicks needed)
    try:
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
        
        auto_verified_text = (
            f"<b>👋 Hello {join_req.from_user.mention},</b>\n"
            f"<b>🤖 I am <a href=https://t.me/{bot.username}>{bot.first_name}</a> (ContentSaver)</b>\n"
            f"<i>Your Fast & Secure Content Saver Bot.</i>\n\n"
            f"<b>✅ Subscription Verified Automatically! 🎉</b>\n"
            f"<blockquote><b>🚀 System Status: 🟢 Online</b>\n"
            f"<b>⚡ Instant Access: Unlocked</b>\n"
            f"<b>📥 Ready: Send any post link directly to start downloading!</b></blockquote>\n\n"
            f"<b>👇 Select an Option Below:</b>\n"
        )

        await client.send_photo(
            chat_id=user_id,
            photo=DEFAULT_BANNER,
            caption=auto_verified_text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        logger.debug(f"Could not send auto-verified PM to {user_id}: {e}")

# ======================================================
# 2. CORE SUBSCRIPTION VERIFICATION ENGINE
# ======================================================

async def get_fsub_invite_link(client: Client, chat_target: int | str, is_join_request: bool = True) -> str:
    """Creates and caches a Join Request or direct invite link for the channel."""
    cache_key = str(chat_target)
    if cache_key in INVITE_CACHE:
        return INVITE_CACHE[cache_key]

    try:
        chat = await client.get_chat(chat_target)
        if is_join_request:
            try:
                # Modern Request-to-Join Link (creates_join_request=True)
                invite = await client.create_chat_invite_link(
                    chat_id=chat_target,
                    name="ContentSaver FSub Gate",
                    creates_join_request=True
                )
                INVITE_CACHE[cache_key] = invite.invite_link
                return invite.invite_link
            except Exception:
                pass

        if chat.username:
            link = f"https://t.me/{chat.username}"
        elif chat.invite_link:
            link = chat.invite_link
        else:
            try:
                link = await client.export_chat_invite_link(chat_target)
            except Exception:
                link = f"https://t.me/{str(chat_target).lstrip('@')}"
        
        INVITE_CACHE[cache_key] = link
        return link
    except Exception as e:
        logger.warning(f"Failed to generate invite link for {chat_target}: {e}")
        return f"https://t.me/{str(chat_target).lstrip('@')}"

async def get_unsubscribed_channels(client: Client, user_id: int) -> list[dict]:
    """
    Checks all configured FSub channels and returns a list of missing channels.
    Admins are always exempt.
    """
    if int(user_id) in ADMINS:
        return []

    # 1. Fetch channels from DB
    configured_channels = await db.get_fsub_channels()
    
    # Fallback to config.FSUB_CHANNELS if DB is empty
    if not configured_channels and FSUB_CHANNELS:
        configured_channels = [
            {"channel": ch, "title": f"Updates Channel {idx+1}", "invite_link": None, "is_join_request": True}
            for idx, ch in enumerate(FSUB_CHANNELS)
        ]

    if not configured_channels:
        return []

    unsubscribed = []

    for item in configured_channels:
        target = item.get("channel")
        if not target:
            continue

        try:
            if str(target).startswith("-100") or str(target).lstrip("-").isdigit():
                chat_target = int(target)
            else:
                chat_target = str(target)
        except Exception:
            chat_target = target

        # Check membership
        try:
            member = await client.get_chat_member(chat_target, int(user_id))
            if member.status in [
                enums.ChatMemberStatus.MEMBER,
                enums.ChatMemberStatus.ADMINISTRATOR,
                enums.ChatMemberStatus.OWNER
            ]:
                continue
            
            # If kicked/banned from update channel
            if member.status in [enums.ChatMemberStatus.BANNED, enums.ChatMemberStatus.RESTRICTED]:
                unsubscribed.append({
                    "channel": target,
                    "title": item.get("title") or "Required Channel",
                    "invite_link": item.get("invite_link") or await get_fsub_invite_link(client, chat_target),
                    "banned": True
                })
                continue

        except UserNotParticipant:
            # Check if modern Join Request is already submitted
            if await db.is_join_requested(user_id, chat_target):
                continue

            link = item.get("invite_link") or await get_fsub_invite_link(client, chat_target, item.get("is_join_request", True))
            unsubscribed.append({
                "channel": target,
                "title": item.get("title") or "Required Channel",
                "invite_link": link,
                "banned": False
            })
        except (ChatAdminRequired, ChannelPrivate, PeerIdInvalid) as e:
            logger.warning(f"FSub channel {chat_target} bypassed due to permission/access issue: {e}")
            continue
        except Exception as e:
            logger.error(f"Error checking channel {chat_target} for {user_id}: {e}")
            continue

    return unsubscribed

def build_fsub_keyboard(unsubscribed: list[dict]) -> InlineKeyboardMarkup:
    """Builds interactive Multi-Channel Join Keyboard."""
    buttons = []
    for idx, ch in enumerate(unsubscribed, start=1):
        title = ch.get("title") or f"Channel {idx}"
        link = ch.get("invite_link") or "https://t.me/"
        buttons.append([InlineKeyboardButton(f"📢 Join {title}", url=link)])
    
    buttons.append([InlineKeyboardButton("🔄 Verify & Try Again", callback_data="fsub_refresh")])
    return InlineKeyboardMarkup(buttons)

# ======================================================
# 3. GLOBAL MIDDLEWARE INTERCEPTOR (group = -1)
# ======================================================

@Client.on_message(filters.private & ~filters.user(ADMINS), group=-1)
async def fsub_message_interceptor(client: Client, message: Message):
    """
    Global Interceptor:
    Catches all incoming messages in group -1.
    If the user has not subscribed to all required channels, halts execution.
    """
    user_id = message.from_user.id
    unsubscribed = await get_unsubscribed_channels(client, user_id)
    
    if unsubscribed:
        # User is not subscribed: stop propagation immediately
        keyboard = build_fsub_keyboard(unsubscribed)
        
        caption = (
            f"<b>📢 Channel Subscription Required</b>\n\n"
            f"<b>👋 Hello {message.from_user.mention},</b>\n\n"
            f"<blockquote>To access <b>ContentSaver Bot</b>, you must join our updates channel(s) below. "
            f"If using request-to-join links, simply tap <b>Request to Join</b>, then click <b>Verify & Try Again</b>!</blockquote>"
        )
        
        await message.reply_photo(
            photo=DEFAULT_BANNER,
            caption=caption,
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
        message.stop_propagation()

# ======================================================
# 4. CALLBACK REFRESH HANDLER
# ======================================================

@Client.on_callback_query(filters.regex("^fsub_refresh$"))
async def fsub_refresh_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    unsubscribed = await get_unsubscribed_channels(client, user_id)
    
    if unsubscribed:
        await callback_query.answer("⚠️ You haven't joined all required channels yet! Please join and try again.", show_alert=True)
        return

    await callback_query.answer("✅ Subscription Verified! Welcome to ContentSaver 🎉", show_alert=False)
    
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
    
    start_text = (
        f"<b>👋 Hello {callback_query.from_user.mention},</b>\n"
        f"<b>🤖 I am <a href=https://t.me/{bot.username}>{bot.first_name}</a> (ContentSaver)</b>\n"
        f"<i>Your Fast & Secure Content Saver Bot.</i>\n"
        f"<blockquote><b>🚀 System Status: 🟢 Online</b>\n"
        f"<b>⚡ Performance: High-Speed Async Engine</b>\n"
        f"<b>🔐 Security: End-to-End Encrypted</b>\n"
        f"<b>📊 Uptime: 99.9% Guaranteed</b></blockquote>\n"
        f"<b>👇 Select an Option Below to Get Started:</b>\n"
    )

    try:
        await client.edit_message_media(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.id,
            media=InputMediaPhoto(
                media=DEFAULT_BANNER,
                caption=start_text
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception:
        await callback_query.message.reply_photo(
            photo=DEFAULT_BANNER,
            caption=start_text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )
