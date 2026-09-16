HELP_TXT = """<b>📚 ContentSaver - Complete Guide & Command Index</b>

<b>👋 How to Save Content:</b>
<blockquote>
<b>1. Public Channels:</b>
• Send any public post link (e.g. <code>https://t.me/channel/123</code>).

<b>2. Private/Restricted Channels:</b>
• Use <code>/login</code> to connect your account securely.
• Send private post link (e.g. <code>https://t.me/c/1234567890/456</code>).

<b>3. Batch Range Saving:</b>
• Send a range link: <code>https://t.me/channel/100-110</code>
• Send <code>/cancel</code> anytime to stop batch operations.
</blockquote>

<b>📱 Main Commands:</b>
<blockquote>
• <b>/start</b> — Restart bot & view home dashboard
• <b>/help</b> — Open this complete user guide
• <b>/settings</b> — Interactive settings panel
• <b>/commands</b> — Complete commands index
• <b>/login</b> — Connect account for restricted channels
• <b>/logout</b> — Disconnect & clear session
• <b>/cancel</b> — Stop active download or batch task
</blockquote>

<b>💎 Plan & Quota:</b>
<blockquote>
• <b>/myplan</b> (or <b>/plan</b>) — Check plan, daily tokens & expiry
• <b>/premium</b> — View premium benefits & upgrade options
</blockquote>

<b>✍️ Custom Caption:</b>
<blockquote>
• <b>/set_caption &lt;text&gt;</b> — Set custom caption (supports <code>{filename}</code> & <code>{size}</code>)
• <b>/see_caption</b> — Preview current custom caption
• <b>/del_caption</b> — Remove custom caption
</blockquote>

<b>🖼 Custom Thumbnail:</b>
<blockquote>
• <b>/set_thumb</b> — Reply to photo to set custom thumbnail
• <b>/view_thumb</b> — Preview current custom thumbnail
• <b>/del_thumb</b> — Remove custom thumbnail
• <b>/thumb_mode</b> — Check thumbnail mode status
</blockquote>

<b>✂️ Word Filters:</b>
<blockquote>
• <b>/set_del_word &lt;w1&gt; &lt;w2&gt;</b> — Remove unwanted words from captions
• <b>/rem_del_word &lt;w1&gt; &lt;w2&gt;</b> — Remove words from deletion list
• <b>/set_repl_word &lt;old&gt; &lt;new&gt;</b> — Replace words/links in captions
• <b>/rem_repl_word &lt;old&gt;</b> — Remove replacement rule
</blockquote>

<b>📤 Dump Chat:</b>
<blockquote>
• <b>/setchat &lt;chat_id&gt;</b> — Auto-forward saved media to channel/group
• <b>/setchat clear</b> — Remove forward destination
</blockquote>

<b>👑 Admin Commands (Owner Only):</b>
<blockquote>
• <b>/add_premium &lt;user_id&gt; &lt;days&gt;</b> — Grant premium (0 for permanent)
• <b>/remove_premium &lt;user_id&gt;</b> — Revoke user premium
• <b>/broadcast</b> (reply to message) — Broadcast to all users
• <b>/users</b> — View total registered users count
• <b>/ban &lt;user_id&gt;</b> / <b>/unban &lt;user_id&gt;</b> — Ban or unban user
• <b>/set_dump &lt;user_id&gt; &lt;chat_id&gt;</b> — Admin set user dump chat
• <b>/add_fsub &lt;channel&gt; [link]</b> — Add channel to Multi-FSub
• <b>/del_fsub &lt;channel&gt;</b> (or <code>all</code>) — Remove FSub channel(s)
• <b>/fsub</b> — View active FSub channels status
• <b>/auto_approve &lt;on/off&gt;</b> — Toggle Join-Request auto-approval
</blockquote>
"""

COMMANDS_TXT = """<b>📜 All Available Commands</b>

<b>👤 Main & System</b>
<blockquote>
/start  — Home & quota
/help  — Detailed guide
/settings — Customize bot
/commands — This list
/login  — Connect account
/logout — Disconnect account
/cancel — Stop current task
</blockquote>

<b>💎 Plan & Quota</b>
<blockquote>
/myplan — Your plan & quota
/premium — Upgrade options
</blockquote>

<b>✍️ Custom Caption</b>
<blockquote>
/set_caption &lt;text&gt; — Set caption
/see_caption — Preview caption
/del_caption — Remove caption
</blockquote>

<b>🖼 Custom Thumbnail</b>
<blockquote>
/set_thumb — Reply to photo
/view_thumb — Preview thumbnail
/del_thumb — Remove thumbnail
/thumb_mode — Status
</blockquote>

<b>✂️ Word Filters</b>
<blockquote>
/set_del_word — Delete words
/rem_del_word — Remove del words
/set_repl_word — Replace words
/rem_repl_word — Remove repl words
</blockquote>

<b>📤 Dump Chat</b>
<blockquote>
/setchat &lt;chat_id&gt; — Set forward chat
/setchat clear — Remove dump chat
</blockquote>

<b>👑 Admin Management</b>
<blockquote>
/add_premium — Add premium
/remove_premium — Remove premium
/broadcast — Broadcast message
/users — User count
/ban / /unban — Ban management
/add_fsub / /del_fsub — FSub channels
/fsub — FSub status
/auto_approve &lt;on/off&gt; — Auto-approval
</blockquote>
"""
