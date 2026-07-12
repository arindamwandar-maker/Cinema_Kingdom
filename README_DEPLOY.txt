CINEMA KINGDOM - CK_V!

IMPORTANT
1. Run only one bot instance. Multiple Railway/Termux instances cause Telegram getUpdates Conflict.
2. Add the bot as admin in the main group, community channel and MyStorage channel.
3. In the main group enable Delete Messages permission.
4. For old movies to survive redeploys, attach a Railway volume at /data and set DB_PATH=/data/bot.db.
   Without persistent storage, Railway can remove bot.db during redeploy.

GOOGLE SHEET
- Create one spreadsheet and share it as Editor with the service account client_email.
- Set GOOGLE_SHEET_URL.
- Recommended: Base64 encode the entire credentials JSON file and set GOOGLE_CREDENTIALS_BASE64.
- The bot creates/uses worksheets named Movie Requests and Storage Uploads.
- Test with /sheettest as an admin.

SEARCH FLOW
- Users search only in GROUP_ID.
- Private DM search is disabled.
- Search result movie button opens the private bot.
- Generate Download Link creates a 5-minute token.
- If no shortener is configured or the provider blocks Railway, the bot uses the direct Telegram token link.

DELETE / RESTORE
- In MyStorage use /delete MovieID, for example /delete 12.
- Delete is soft delete: record remains in SQLite, disappears from search, and Google Sheet Status becomes Movie Deleted.
- Use /restore MovieID to restore a soft-deleted record.

ADMIN
- Super admin can use /addadmin ID and /removeadmin ID.
- /admins lists admins.
- Admins bypass group cooldown.

GOOGLE SHEET MOVIE NAME SYNC
- Edit Movie Name in the Storage Uploads worksheet.
- The bot checks for changes every 60 seconds.
- It updates the database title and the original MyStorage post caption.
- Telegram does not allow renaming the actual uploaded filename; only the caption/title changes.
- Optional Railway variable: SHEET_SYNC_INTERVAL=60

NEW FEATURES
- Google Sheet movie-name sync runs every SHEET_SYNC_INTERVAL seconds.
- Bot needs Edit Messages permission in MyStorage to change the original file caption.
- Promotional join message runs every PROMO_INTERVAL seconds (minimum 120).
- Bot needs Ban Users/Delete Messages permissions in the main group for link moderation.
- Duplicate uploads require admin confirmation through inline buttons.
- 18+ searches require age confirmation.


ADMIN SEND COMMANDS
- /sendgroup Your message -> sends to the main group with Join buttons.
- /sendchannel Your message -> sends to the community channel with Join buttons.
- /sendboth Your message -> sends to both.
- You can also reply to an existing text message with one of these commands.

GPLINKS SHORTENER
- Set SHORTENER_BASE_URL=https://api.gplinks.com/api
- Set SHORTENER_API_KEY in Railway Variables.
- SHORTENER_ALIAS is optional; the bot adds a unique suffix to prevent duplicate-alias errors.
- SHORTENER_RESPONSE_FORMAT can be json or text.

LINK TRACKING
- Link Generated is recorded when a user presses Generate Download Link.
- File Delivered is recorded when the user returns through the token and receives the file.
- Google Sheet worksheet: Link Clicks.
- LOCAL_TIMEZONE defaults to Asia/Kolkata.
- GPLinks external page clicks cannot be known exactly without a GPLinks webhook/reporting API; the bot records generation and successful delivery events.
