Cinema Kingdom v4 Final

Railway Variables Required:
BOT_TOKEN
BOT_USERNAME (without @)
SUPER_ADMIN_ID
ADMIN_IDS (comma separated)
GROUP_ID
CHANNEL_ID
STORAGE_CHANNEL
GROUP_USERNAME (without @)
CHANNEL_USERNAME (without @)
STORAGE_USERNAME (without @)
SHORTENER_BASE_URL=https://adsfly.in/api
SHORTENER_API_KEY=your AdsFly API key
SHORTENER_ALIAS optional
GOOGLE_SHEET_URL optional
GOOGLE_CREDENTIALS_JSON optional but recommended

Important:
1. Only one bot instance can run. Stop Termux/other Railway deployments.
2. /delete MovieID works only inside MyStorage channel.
3. Super admin commands:
   /addadmin USER_ID
   /removeadmin USER_ID
   /admins
4. Admins bypass 1 minute group cooldown.
5. User cooldown message shows a progress bar; Telegram cannot change the actual send button text.
6. Google Sheet creates two worksheets automatically: Movie Requests and Storage Uploads.
7. Shortener supports AdsFly API format: BASE?api=KEY&url=DESTINATION&alias=ALIAS
