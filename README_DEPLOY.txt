Cinema Kingdom Final Rectified Build

Railway setup:
1. Upload all files to GitHub and connect the repository to Railway.
2. Add all values from .env.example to Railway Variables.
3. Add a Railway Volume mounted at /data.
4. Set DB_PATH=/data/bot.db so uploaded movies survive redeploys.
5. Bot must be admin in the Group, Community Channel, and MyStorage channel.
6. Run only one bot instance. Stop old Railway services and Termux copies.

Google Sheet:
- Set GOOGLE_SHEET_URL.
- Recommended: put the full one-line service-account JSON in GOOGLE_CREDENTIALS_JSON.
- Alternative: base64-encode credentials.json and place it in GOOGLE_CREDENTIALS_BASE64.
- Share the Google Sheet with the service account client_email as Editor.
- Admin command /sheettest writes a test row and reports connection status.
- Worksheets Movie Requests and Storage Uploads are created automatically.

Storage and deletion:
- Upload a document/video/audio/animation in MyStorage.
- Caption first line becomes movie title; filename is fallback.
- Bot replies with Movie ID and /delete ID.
- /delete MovieID works only in MyStorage. In channel-post mode Telegram does not expose the individual admin identity; therefore storage-channel posting permission is the security gate.

Cooldown:
- Normal users can search every 60 seconds.
- Admins bypass cooldown.
- Telegram does not allow bots to replace the user's Send button with a timer. The bot displays a progress/timer message instead.

Auto-delete:
- Group search query and bot result are tracked and removed after AUTO_DELETE_TIME.
- Cleanup sends only one short-lived graphic status per affected chat, preventing repeated cleanup spam.

Shortener:
- API is fully controlled by SHORTENER_BASE_URL and SHORTENER_API_KEY.
- AdsFly default: https://adsfly.in/api
- Keep SHORTENER_ALIAS blank unless needed; configured aliases get a unique suffix.
- If the API fails, the bot safely falls back to the direct Telegram deep link.
