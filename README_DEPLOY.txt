Cinema Kingdom Final Deploy Notes

Railway Variables Required:
BOT_TOKEN
BOT_USERNAME  -> without @, exact bot username from BotFather
ADMIN_IDS     -> comma separated Telegram numeric IDs
GROUP_ID
CHANNEL_ID
STORAGE_CHANNEL
GROUP_USERNAME -> without @
CHANNEL_USERNAME -> without @
STORAGE_USERNAME -> without @
SHORTENER_API_KEY
SHORTENER_BASE_URL=https://shrinkearn.com/api
GOOGLE_SHEET_URL
GOOGLE_CREDENTIALS_JSON -> paste full credentials.json content here for Railway

Optional:
SHORTENER_ALIAS -> keep empty unless you really need custom alias. Duplicate alias can break short links.

Google Sheet setup:
1. Create Google Sheet.
2. Share it with service account client_email as Editor.
3. Paste the full credentials.json into Railway variable GOOGLE_CREDENTIALS_JSON.
4. Bot will auto-create two worksheets:
   - Movie Requests
   - Storage Uploads

Storage upload:
- Add bot as admin in @mystoragecinema.
- Bot must be able to read channel posts and send messages.
- Upload video/document/audio with caption or filename.
- Bot replies with Movie Name, Movie ID, Upload By, Date & Time, File Size.

Movie delete:
- Admin can use /delete MovieID
- Admin also sees Delete Movie button in private movie detail.

Common Railway issue:
Conflict getUpdates means same bot is running in two places. Stop Termux/other Railway deployments and keep only one instance.
