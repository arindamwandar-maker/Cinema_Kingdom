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
