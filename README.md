# 🚀 ContentSaver Bot (Save Restricted Content)

<p align="center">
  <img src="banner.png" alt="ContentSaver Bot Banner" width="700">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white&style=for-the-badge">
  <img src="https://img.shields.io/badge/Pyrogram-v2.0-26A5E4?logo=telegram&logoColor=white&style=for-the-badge">
  <img src="https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white&style=for-the-badge">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white&style=for-the-badge">
  <img src="https://img.shields.io/badge/License-MIT-red?style=for-the-badge">
</p>

<p align="center">
  <b>High-performance, async Telegram bot to save media, files, and messages from public and private restricted channels. Packed with Multi-Channel ForceSub 2.0, Join-Request Auto-Approval, Video Fast-Streaming, Custom Captions, Thumbnails, Word Filters, and Dump Chat Forwarding.</b>
</p>

---

## 🌟 Key Highlights

- ⚡ **High-Speed Async Engine:** Powered by Pyrogram Async with concurrent upload/download pipelines.
- 🔓 **Restricted Channel Support:** Download protected media and documents seamlessly using authenticated session login.
- 📦 **Batch Range Mode:** Save entire series of posts at once (e.g. `https://t.me/channel/100-150`).
- 🎬 **Video Fast-Streaming:** All uploaded videos support instant streaming without waiting for complete downloads.
- 📢 **Force Subscribe (FSub 2.0):** Multi-channel gate support with Request-to-Join links and automatic background approval.
- ✍️ **Dynamic Captions & Thumbnails:** Custom placeholders (`{filename}`, `{size}`) and persistent custom thumbnail support.
- ✂️ **Word Filters:** Automatic removal and replacement of unwanted spam words and channel links.
- 📤 **Dump Chat Forwarding:** Automatically route saved media to your private backup channel or supergroup.
- 💎 **Tiered Quota & Monetization:** Configurable Free tier (10 saves/day, 2GB cap) vs Premium tier (unlimited, 4GB+ support) with expiry tracking. Admins enjoy permanent exemption.

---

## ⚙️ Configuration & Environment Variables

| Variable | Required | Description | Default |
| :--- | :---: | :--- | :--- |
| `BOT_TOKEN` | **Yes** | Telegram Bot Token from [@BotFather](https://t.me/BotFather) | — |
| `API_ID` | **Yes** | Telegram App API ID from [my.telegram.org](https://my.telegram.org) | — |
| `API_HASH` | **Yes** | Telegram App API Hash from [my.telegram.org](https://my.telegram.org) | — |
| `ADMINS` | **Yes** | Comma-separated Telegram User IDs of Bot Owners/Admins | — |
| `DB_URI` | **Yes** | MongoDB Atlas Connection URI | — |
| `DB_NAME` | No | MongoDB Database Name | `SaveRestricted2` |
| `LOG_CHANNEL` | **Yes** | Channel ID for logging user signups and system events | — |
| `FSUB_CHANNELS` | No | Comma-separated Channel IDs/Usernames for Force Subscribe | `""` |
| `FSUB_AUTO_APPROVE`| No | Automatically approve incoming channel join requests | `True` |
| `ERROR_MESSAGE` | No | Display user-facing error messages | `True` |

---

## 🚀 Deployment Guide

### 1. Local / VPS Setup

```bash
# Clone the repository
git clone https://github.com/Bibinkvr/Save-restrict-content-bot.git
cd Save-restrict-content-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Configure environment
cp .env.example .env  # Fill in your credentials

# Start the bot
python bot.py
```

### 2. Docker Deployment

```bash
docker build -t contentsaver-bot .
docker run -d --name contentsaver --env-file .env contentsaver-bot
```

---

## 📜 All Available Commands

### 👤 User Commands

| Command | Action |
| :--- | :--- |
| `/start` | Start/Restart the bot & view quota status |
| `/help` | Detailed interactive guide & command list |
| `/settings` | Open interactive settings dashboard |
| `/commands` | Quick command index |
| `/login` | Interactive phone + OTP login for restricted access |
| `/logout` | Log out and disconnect active user session |
| `/cancel` | Instantly abort current task or batch save |
| `/myplan` / `/plan` | View plan details, daily tokens, and expiry |
| `/premium` | View premium membership pricing and benefits |

### ⚙️ Customization & Filters

| Command | Action |
| :--- | :--- |
| `/set_caption <text>` | Set custom caption (supports `{filename}` and `{size}`) |
| `/see_caption` | Preview current custom caption |
| `/del_caption` | Reset custom caption to default |
| `/set_thumb` | Reply to any photo to set upload thumbnail |
| `/view_thumb` | View current custom thumbnail |
| `/del_thumb` | Delete custom thumbnail |
| `/thumb_mode` | Check thumbnail mode status |
| `/set_del_word <w1> <w2>` | Add words to automatic delete list |
| `/rem_del_word <w1> <w2>` | Remove words from delete list |
| `/set_repl_word <old> <new>` | Set word replacement rule |
| `/rem_repl_word <old>` | Delete word replacement rule |
| `/setchat <chat_id>` | Set dump chat for auto-forwarding |
| `/setchat clear` | Remove dump chat forward destination |

### 👑 Admin Commands (Owner Only)

| Command | Action |
| :--- | :--- |
| `/add_premium <id> <days>` | Grant premium subscription (`0` for permanent) |
| `/remove_premium <id>` | Revoke premium subscription from user |
| `/broadcast` | Reply to any message/media to broadcast to all users |
| `/users` | View registered user analytics and export JSON |
| `/ban <user_id>` | Ban a user from bot access |
| `/unban <user_id>` | Unban a user |
| `/set_dump <user_id> <chat_id>`| Configure dump chat for a user |
| `/add_fsub <channel> [link]` | Add a channel to Multi-FSub gate |
| `/del_fsub <channel>` / `all` | Remove specific or all FSub channels |
| `/fsub` | View status of all active FSub channels |
| `/auto_approve on/off` | Toggle Join-Request auto-approval |

---

## 📞 Support & Admin Contact

<p align="center">
  <a href="https://t.me/H4CK3R_OO7">
    <img src="https://img.shields.io/badge/Admin%20Support-@H4CK3R__OO7-0088cc?style=for-the-badge&logo=telegram&logoColor=white">
  </a>
</p>

---

<p align="center">
  ⭐ <b>If you find this bot helpful, please star the repository!</b>
</p>
