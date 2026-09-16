from pyrogram import Client, filters
from pyrogram.types import Message
from database.db import db
from config import ADMINS

@Client.on_message(filters.command("ban") & filters.user(ADMINS))
async def ban(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("**Usage:** `/ban user_id`")
    try:
        user_id = int(message.command[1])
        await db.ban_user(user_id)
        await message.reply_text(f"**User {user_id} Banned Successfully 🚫**")
    except:
        await message.reply_text("Error banning user.")

@Client.on_message(filters.command("unban") & filters.user(ADMINS))
async def unban(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("**Usage:** `/unban user_id`")
    try:
        user_id = int(message.command[1])
        await db.unban_user(user_id)
        await message.reply_text(f"**User {user_id} Unbanned Successfully ✅**")
    except:
        await message.reply_text("Error unbanning user.")

@Client.on_message(filters.command("set_dump") & filters.user(ADMINS))
async def set_dump(client: Client, message: Message):
    if len(message.command) < 3:
        return await message.reply_text("**Usage:** `/set_dump user_id chat_id`")
    try:
        user_id = int(message.command[1])
        chat_id = int(message.command[2])
        await db.set_dump_chat(user_id, chat_id)
        await message.reply_text(f"**Dump chat set for user {user_id}.**")
    except:
        await message.reply_text("Error setting dump chat.")

@Client.on_message(filters.command(["add_fsub", "set_fsub"]) & filters.user(ADMINS))
async def add_fsub_admin(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>⚠️ Force Subscribe 2.0 Usage:</b>\n\n"
            "<code>/add_fsub &lt;channel_id_or_username&gt; [custom_invite_link]</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/add_fsub @MyChannel</code>\n"
            "• <code>/add_fsub -1001234567890</code>\n"
            "• <code>/add_fsub -1001234567890 https://t.me/+AbCdEfGh</code>\n\n"
            "<i>💡 Supports Multi-Channel FSub with automatic Join-Request approval!</i>"
        )
    
    target = message.command[1].strip()
    invite_link = message.command[2].strip() if len(message.command) > 2 else None

    # Parse int chat_id if provided
    try:
        if target.startswith("-100") or target.lstrip("-").isdigit():
            chat_target = int(target)
        else:
            chat_target = target
    except Exception:
        chat_target = target

    # Validate bot access and generate Join Request invite link
    try:
        chat = await client.get_chat(chat_target)
        chat_title = chat.title or str(chat_target)
        
        if not invite_link:
            try:
                # Create modern Request-to-Join link
                req_invite = await client.create_chat_invite_link(
                    chat_id=chat_target,
                    name="ContentSaver FSub Gate",
                    creates_join_request=True
                )
                invite_link = req_invite.invite_link
            except Exception:
                if chat.username:
                    invite_link = f"https://t.me/{chat.username}"
                elif chat.invite_link:
                    invite_link = chat.invite_link

        await db.add_fsub_channel(
            channel=chat_target,
            title=chat_title,
            invite_link=invite_link,
            is_join_request=True
        )

        await message.reply_text(
            f"<b>✅ FSub Channel Added Successfully!</b>\n\n"
            f"<b>📢 Title:</b> {chat_title}\n"
            f"<b>🆔 ID:</b> <code>{chat_target}</code>\n"
            f"<b>🔗 Invite Link:</b> {invite_link or 'Auto-created'}\n"
            f"<b>⚡ Join-Request Auto-Approval:</b> 🟢 Active\n\n"
            f"<i>Users will now be required to join this channel.</i>"
        )
    except Exception as e:
        # Save anyway if admin insists, but display warning
        await db.add_fsub_channel(
            channel=chat_target,
            title=str(chat_target),
            invite_link=invite_link,
            is_join_request=True
        )
        await message.reply_text(
            f"<b>⚠️ Channel Saved (Access Warning):</b>\n"
            f"<code>{e}</code>\n\n"
            f"<b>Target:</b> <code>{chat_target}</code>\n"
            f"<i>Ensure the bot is added as an Admin with 'Invite Users via Link' permission.</i>"
        )

@Client.on_message(filters.command(["del_fsub", "rem_fsub"]) & filters.user(ADMINS))
async def del_fsub_admin(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>⚠️ Usage:</b>\n"
            "• <code>/del_fsub &lt;channel_id_or_username&gt;</code> → Remove specific channel\n"
            "• <code>/del_fsub all</code> → Remove all FSub channels"
        )
    
    arg = message.command[1].strip()
    if arg.lower() == "all":
        await db.clear_fsub_channels()
        return await message.reply_text("<b>✅ All FSub channels have been cleared & disabled.</b>")
    
    removed = await db.remove_fsub_channel(arg)
    if removed:
        await message.reply_text(f"<b>✅ Removed FSub channel:</b> <code>{arg}</code>")
    else:
        await message.reply_text(f"❌ Channel <code>{arg}</code> was not found in active FSub list.")

@Client.on_message(filters.command(["fsub", "fsub_status", "fsubs"]) & filters.user(ADMINS))
async def fsub_status_admin(client: Client, message: Message):
    channels = await db.get_fsub_channels()
    if not channels and FSUB_CHANNELS:
        channels = [
            {"channel": ch, "title": f"Updates Channel {idx+1}", "invite_link": None, "is_join_request": True}
            for idx, ch in enumerate(FSUB_CHANNELS)
        ]

    if not channels:
        return await message.reply_text(
            "<b>ℹ️ Force Subscribe Status: DISABLED ⚪</b>\n\n"
            "<i>Use /add_fsub &lt;channel_id&gt; to add one or more channels.</i>"
        )

    text = f"<b>📢 Active FSub Channels ({len(channels)} Channels Configured):</b>\n\n"
    for idx, item in enumerate(channels, start=1):
        ch = item.get("channel")
        title = item.get("title", "Channel")
        link = item.get("invite_link") or "Auto-generated"
        text += (
            f"<b>{idx}. {title}</b>\n"
            f"• <b>ID:</b> <code>{ch}</code>\n"
            f"• <b>Link:</b> {link}\n\n"
        )

    text += "<i>Use /add_fsub to add more, or /del_fsub &lt;id&gt; to remove.</i>"
    await message.reply_text(text, disable_web_page_preview=True)

@Client.on_message(filters.command(["auto_approve", "autoapprove", "set_auto_approve"]) & filters.user(ADMINS))
async def toggle_auto_approve_admin(client: Client, message: Message):
    if len(message.command) < 2:
        current = await db.get_auto_approve()
        status_badge = "🟢 ENABLED (ON)" if current else "🔴 DISABLED (OFF)"
        return await message.reply_text(
            f"<b>⚡ Join-Request Auto-Approve Status:</b> {status_badge}\n\n"
            "<b>Usage:</b>\n"
            "• <code>/auto_approve on</code> → Turn Auto-Approval ON\n"
            "• <code>/auto_approve off</code> → Turn Auto-Approval OFF"
        )
    
    arg = message.command[1].strip().lower()
    if arg in ["on", "true", "enable", "yes", "1"]:
        await db.set_auto_approve(True)
        await message.reply_text("<b>✅ Join-Request Auto-Approval is now ENABLED 🟢</b>\n<i>New join requests will be approved automatically.</i>")
    elif arg in ["off", "false", "disable", "no", "0"]:
        await db.set_auto_approve(False)
        await message.reply_text("<b>✅ Join-Request Auto-Approval is now DISABLED 🔴</b>\n<i>Admins must approve join requests manually.</i>")
    else:
        await message.reply_text("❌ <b>Invalid Option.</b> Use <code>/auto_approve on</code> or <code>/auto_approve off</code>.")
