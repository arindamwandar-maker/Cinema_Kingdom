CINEMA KINGDOM - DEPLOYING ON A FREE 24/7 HOST

The bot now has two entry points:

  web.py       Telegram pushes updates to it. Runs as a web app. (free 24/7)
  bot.py       Old polling mode, for a host that keeps one process running
               (Railway, Termux). Registers the timed jobs itself.

services/jobs.py holds the timed jobs (auto-delete, Google Sheet sync,
promotion) so web.py and bot.py share one implementation.


WHY THE POLLING MODE WAS DROPPED

app.run_polling() plus the JobQueue needs one process that never exits.
No free host gives that away any more: Render and Koyeb put free workers to
sleep, and PythonAnywhere free has no always-on process and no scheduled
tasks at all. A web app, in contrast, is online 24/7 on the free tier, so the
bot answers as a webhook instead.


FREE SETUP ON PYTHONANYWHERE (no credit card)

1. Register
   Go to pythonanywhere.com -> Sign up. Pick the free/Beginner account.
   No card is asked for. Choose a username you like, it becomes part of your
   site address: https://YOURUSERNAME.pythonanywhere.com

2. Get the code
   Click "Bash" (a console). Type these lines, pressing Enter after each:

     git clone https://github.com/arindamwandar-maker/Cinema_Kingdom.git
     cd Cinema_Kingdom
     pip3 install --user -r requirements.txt

3. Put your secrets in a .env file
   Still in the console:

     cp .env.example .env
     nano .env

   Fill at least BOT_TOKEN and GOOGLE_CREDENTIALS_BASE64, exactly the values
   you had in Railway Variables. Save with Ctrl+O, Enter, then exit with
   Ctrl+X.

4. Create the webhook secret
     python3 setup_hook.py --make-secret

   Copy the printed WEBHOOK_SECRET_TOKEN line into .env (step 3 style editing).

5. Set the webhook address
   Also in .env:

     WEBHOOK_BASE_URL=https://YOURUSERNAME.pythonanywhere.com

6. Tell Telegram to use the webhook
     cd ~/Cinema_Kingdom
     python3 setup_hook.py

   It should print "Webhook registered" and then the webhook info from
   Telegram. Keep that output, it proves the switch happened.

7. Point the web app at web.py
   Web tab -> "Configure" -> choose Flask -> in "Source code" and "Working
   directory" write /home/YOURUSERNAME/Cinema_Kingdom -> Continue.
   Then on the same Web tab click the "WSGI configuration file" link,
   select all of its contents, delete them, and paste the contents of
   pythonanywhere_wsgi.py from the repo (change PROJECT_DIR only if your
   folder is named differently). Click Reload.

8. Check it is alive
   Open https://YOURUSERNAME.pythonanywhere.com/healthz in a browser.
   "ready": true means the bot is running. If it says false, "boot_error"
   tells you what went wrong. Send /start to the bot as the real test.

9. Keep the timed jobs running while the chat is quiet
   GitHub -> Cinema_Kingdom -> Settings -> Secrets and variables -> Actions
   -> "New repository secret":
       Name  KEEP_ALIVE_TOKEN
       Value the same WEBHOOK_SECRET_TOKEN string from step 4
   Then edit .github/workflows/keep-alive.yml and replace yourusername in
   TICK_URL with your real PythonAnywhere username. Commit the change.
   That workflow calls /tick every 10 minutes, which is what fires the
   promotion message and the cleanup when nobody is posting.

10. Stop the Railway service
    Do this last, and do it for real. Only one delivery method may be active:
    while the Railway bot is still polling, Telegram reports 409 Conflict.
    Railway -> your project -> Service -> Settings -> Stop (or delete it).


MOVING YOUR OLD DATABASE

Your movies live in bot.db. Download it from Railway (or take it from a
backup) and upload it into /home/YOURUSERNAME/Cinema_Kingdom, then from the
console:

     cd ~/Cinema_Kingdom
     chmod ug+rw bot.db

DB_PATH is just "bot.db", so the file stays inside the project folder, which
is persistent - redeploying does not wipe it, unlike Railway without a volume.


THINGS THAT BEHAVE DIFFERENTLY FROM RAILWAY

* Expired download messages are removed within 30 seconds while the group is
  active. In a completely quiet chat the next removal waits for the next
  /tick, so up to about 10 minutes.
* The promotion message fires on the tick, so it can be a few minutes off.
* PythonAnywhere free only allows outbound calls to its allowlist.
  api.telegram.org and *.googleapis.com are already allowed, so Telegram and
  Google Sheets work. api.gplinks.com is not: until it is added, the bot
  falls back to the direct Telegram link, which still works. Ask for the
  domain in the PythonAnywhere "Code for business" forum to enable GPLinks.
* Free tier gives about 512 MB of disk and a daily CPU cap. The bot stores
  Telegram file ids, not the files, so the database stays small.


KEEPING THE FREE ACCOUNT ALIVE

PythonAnywhere pauses free accounts that are not looked at. Once every three
months, log in and click the "Extend free account" button on the dashboard,
otherwise the site stops answering and Telegram will drop the webhook.
Nothing else needs restarting: the web app is always on, and the GitHub
workflow is always scheduled.


BACKUPS

bot.db is the whole catalogue. Once a month, in the Files tab, right-click
bot.db and download it. Losing the database means re-uploading every movie.


ORIGINAL FUNCTIONAL NOTES (unchanged)

IMPORTANT
1. Run only one bot instance. Multiple Railway/Termux instances cause
   Telegram getUpdates Conflict.
2. Add the bot as admin in the main group, community channel and MyStorage
   channel.
3. In the main group enable Delete Messages permission.
4. For old movies to survive redeploys, keep DB_PATH inside the project
   folder (it is persistent on PythonAnywhere). On Railway a volume was
   needed at /data with DB_PATH=/data/bot.db.

GOOGLE SHEET
- Create one spreadsheet and share it as Editor with the service account
  client_email.
- Set GOOGLE_SHEET_URL.
- Recommended: base64 encode the whole credentials JSON and set
  GOOGLE_CREDENTIALS_BASE64.
- The bot creates/uses worksheets named Movie Requests, Storage Uploads,
  Link Clicks, movie download status and Group Members.
- Test with /sheettest as an admin.
- See GOOGLE SHEET MOVIE NAME SYNC below for renaming movies from the sheet.

SEARCH FLOW
- Users search only in GROUP_ID. Private DM search is disabled.
- Search result movie button opens the private bot.
- Generate Download Link creates a 5-minute token.
- If no shortener is configured or the provider is blocked, the bot uses the
  direct Telegram token link.

DELETE / RESTORE
- In MyStorage use /del MovieID (or the full /delete 12).
- Delete is soft delete: record remains in SQLite, disappears from search,
  and Google Sheet Status becomes Movie Deleted.
- Use /rst MovieID (or /restore 12) to restore a soft-deleted record.

ADMIN
- Super admin can use /addadmin ID and /removeadmin ID.
- /admins lists admins. Admins bypass group cooldown.

GOOGLE SHEET MOVIE NAME SYNC
- Edit Movie Name in the Storage Uploads worksheet.
- The bot checks for changes on every job run.
- It updates the database title and the original MyStorage post caption.
- Telegram does not allow renaming the actual uploaded filename; only the
  caption/title changes.
- /syncnames runs that check immediately and reports each rename.

RENAME AND STORAGE COMMAND KEYS
- Type / in MyStorage and Telegram suggests these; they only work there:
  /rn MovieID New Name     rename (alias /rename)
  /del MovieID             delete (alias /delete)
  /rst MovieID             restore (alias /restore)
  /syncnames               apply names edited in the sheet
- /rn updates the database, search, download pages, the MyStorage caption and
  the Movie Name cell of the sheet. The previous names stay searchable.
- /stats also works in MyStorage: post it there and the bot replies with a new
  post (Telegram does not allow replying inside a broadcast channel).

ADMIN / COMMAND MENU
- Type / as an admin and Telegram lists every admin command, in the group, in
  MyStorage and in the private chat with the bot.
- Normal users only see /start, /help and /request.
- The menus are refreshed on every bot start, so edit core.py
  (ADMIN_COMMANDS / STORAGE_COMMANDS) to add a key.

SEARCH RESULTS DISPLAY
- The group message shows the search query, the number of matches and the page
  (Pages — 1/3); the movie names only appear on the buttons below, labelled
  "{File Size} - {Movie Name}".
- SEARCH_RESULTS_PER_PAGE (default 5) is the number of buttons per page,
  MAX_MOVIES_PER_SEARCH (default 15) is the maximum number of matches.
- Very long queries cannot fit in a page button, so those searches show one
  page only.

GROUP MESSAGE TIMER
- GROUP_MESSAGE_INTERVAL (default 60) is the number of seconds a member must
  wait between messages in the group. It applies to everyone, admins included.
  Messages starting with / are exempt so an admin can always run a command.
  0 turns the timer off.
- The bot deletes the too-early message and posts a notice naming the user with
  the seconds left; the notice deletes itself.
- Telegram gives bots no way to draw a countdown inside the member's typing
  box, so the wait is shown as that self-deleting notice instead.

GROUP RULES (Cinema Kingdom 3.0)
- Attachments: with GROUP_BLOCK_ATTACHMENTS=true (default) any file, video,
  music, voice note, photo, animation or sticker a member sends is deleted.
  Admins are exempt so they can post posters.
- The same setting is also written into Telegram itself on every bot start
  (core.py apply_group_privacy): members keep text only, lose polls, inline
  bots, web page previews, invites, pins and topic management. For this to
  take effect the bot must be a group admin with "Manage Group".
- Links: http(s)://, www., t.me/ and telegram.me/ are removed, and so is a
  @username that belongs to a real channel or group. Plain @name talk is fine.
- Repeat offenders: every violation adds a strike valid for
  GROUP_OFFENCE_WINDOW seconds (default 1 day). The first GROUP_BAN_STRIKES-1
  violations (default 1) remove the member, who may rejoin; at GROUP_BAN_STRIKES
  the ban stays and the member is listed in Banned until /unban.
- GROUP_BAN_STRIKES=1 bans on the first violation.
- /unban UserID lifts the ban and clears that user's strikes. Telegram does not
  let a bot re-add a member, so the user must join again with your invite link.
- Admins are not affected by the attachment or link rules, only by the timer.

WHAT TELEGRAM DOES NOT ALLOW
- Hiding a group's member list from members. Only "Restrict New Members" in
  the group's own Permissions screen stops a *newly joined* user from reading
  history and members until an admin approves them — do that in Telegram:
  group -> Edit -> Permissions.
- Removing the group's public invite link without breaking the
  https://t.me/cinema_kingdom_vault1 buttons the bot shows on Join prompts and
  promotions. The bot deletes any group link a member posts instead.
- Making the group Private would take it off the search page and stop users
  reaching it from the bot, so it stays Public with the rules above.
- Reading a member's phone number. The only number a bot ever gets is one the
  member hands over with the Share My Number button, so a Country or Mobile cell
  stays empty until that member taps it - nobody can fill in the old members.

FEATURES
- Promotional join message runs every PROMO_INTERVAL seconds (minimum 120).
- Bot needs Ban Users/Delete Messages permissions in the main group for link
  moderation, and Edit Messages in MyStorage to change file captions.
- Duplicate uploads require admin confirmation through inline buttons.
- 18+ searches require age confirmation.

ADMIN SEND COMMANDS
- /sendgroup Your message -> sends to the main group with Join buttons.
- /sendchannel Your message -> sends to the community channel with buttons.
- /sendboth Your message -> sends to both.
- You can also reply to an existing text message with one of these commands.

GPLINKS SHORTENER
- Set SHORTENER_BASE_URL=https://api.gplinks.com/api and SHORTENER_API_KEY.
- SHORTENER_ALIAS is optional; the bot adds a unique suffix to prevent
  duplicate-alias errors. SHORTENER_RESPONSE_FORMAT can be json or text.

LINK TRACKING
- "Link Generated" is recorded when a user presses Generate Download Link.
- "File Delivered" is recorded when the user returns through the token and
  receives the file. Worksheet: Link Clicks. LOCAL_TIMEZONE defaults to
  Asia/Kolkata.
- GPLinks external page clicks cannot be known exactly without a GPLinks
  webhook/reporting API; the bot records generation and delivery events.

MOVIE REQUEST REMINDERS
- Every REQUEST_REMINDER_INTERVAL seconds (default 3600 = 1 hour) the bot
  private-messages every bot admin the list of pending movie requests. That is
  ADMIN_IDS, SUPER_ADMIN_ID and everyone added with /addadmin - before, an
  /addadmin admin never got the list and so could never press Solved.
- Each request has a ✅ Solved button. Pressing it marks the request solved in
  the bot, writes Status / Solved By / Solved Time on that row of the Movie
  Requests worksheet, updates the list in that message and tells the user who
  asked for the movie.
- Nothing is sent when nobody is waiting for a movie.

GROUP MEMBERS WORKSHEET
- One row per user the bot knows: User ID, Username, Name, Role (Super Admin /
  Admin / Member), Join Date, Last Active, Total Requests, Country, Mobile.
- Country and Mobile are the last two columns on purpose, so rows already in
  your sheet keep their column positions. The hourly job now also refreshes
  those two cells of an old row when a member finally picks a country or shares
  a number; no other cell of an existing row is ever rewritten.
- Telegram does not let a bot read a group's member list, so this sheet grows
  from group joins and from anyone who uses the bot.
- Runs every MEMBER_SHEET_INTERVAL seconds (default 3600).

MEMBER COUNTRY AND MOBILE (/country, /number)
- /country opens a picker with 110 countries, "🌍 More countries" pages through
  them, the choice is stored per user and lands in the sheet.
- /number (or the 📱 Share My Number button in the picker and in the group
  welcome) shows a Telegram button that sends the member's own contact. The bot
  stores that number and works out the country from the dialling code (+91 ->
  India), and the member can still correct the country with /country.
- The group welcome message carries both as buttons that open the bot privately
  (t.me/<BOT_USERNAME>?start=country and ?start=share_number).
- WHAT TELEGRAM MAKES IMPOSSIBLE: a bot can never read a member's number. Only
  a member who presses the Share button gives it, so numbers and countries of
  the people who joined before this feature existed cannot be generated
  afterwards - their rows stay blank until they tap it themselves.
- /members now also prints the country tally and how many members shared a
  number, so you can see which cinema to upload next.

PINNED GROUP RULES
- On every boot the bot posts GROUP_RULES_MSG in the group and in the community
  channel and pins it, so the same rules text sits on top of both.
- It edits its own earlier pinned post instead of posting a new copy - the
  message id is remembered in bot.db (settings table).
- The pinned rules are the only bot message the 10 minute sweep never deletes:
  its deletion booking is removed as soon as it is posted.
- Needs the bot to be an admin of both chats with "Pin Messages" on.
- To use your own wording, set GROUP_RULES_MSG in the .env file (HTML such as
  <b> works). A single space disables the pinning altogether.

GROUP WELCOME MESSAGE
- A new group member is greeted in the group with GROUP_WELCOME_MSG, which
  names them, shows GROUP_NAME and adds the pin line with SUPER_ADMIN_USERNAME
  when you have filled that in.
- Under the greeting sit two buttons, 🌍 Select Country and 📱 Share My Number,
  which open the bot in a private chat.
- The bot only receives join notifications when it reads all group messages:
  BotFather -> /setprivacy -> Disable, or make the bot a group admin.
- The greeting also records the member, which is how they reach the
  Group Members worksheet.

UPLOADER NAMES AND FILE CAPTION
- Storage uploads remember who uploaded the file, and the download page plus
  Movie Details show "Uploaded by: @name".
- The delivered file caption carries the title, the bold FILE_CAPTION_BADGE line
  ("No Theatre Print 🚫 • Only FHD Files 📀"), FILE_CAPTION_NOTE and links to
  GROUP_NAME/GROUP_USERNAME and CHANNEL_NAME/CHANNEL_USERNAME. Leaving one
  blank drops only that line. No admin username is printed there; SUPER_ADMIN_
  USERNAME is only used in the group welcome message.
- MyStorage is never linked in these messages, it stays private.

PENDING REQUESTS ON DEMAND (/pending)
- /pending (or /requests) sends the same solvable list the hourly reminder
  sends, straight away. /pending is in the admin menu and works in the group
  and in a private chat.
- In a group it answers as a private message to the admin who typed it, so no
  member sees admin tooling. If that admin has never opened /start the list
  falls back to a group reply, because Telegram blocks the private message.
- Any bot admin can press ✅ Solved, including people added with /addadmin.

EVERY BOT MESSAGE DELETES ITSELF
- AutoDeleteBot (services/auto_delete.py) is the bot object the whole app uses.
  Every Telegram message the bot sends is booked for deletion after
  AUTO_DELETE_TIME seconds (default 600 = 10 minutes), in the group, in the
  community channel and in private chats, without each handler having to
  remember.
- One exemption, on purpose: MyStorage (STORAGE_CHANNEL). Those posts hold the
  original files, so deleting them would empty the catalogue. Admin chats are
  swept like everybody else; set DELETE_ADMIN_MESSAGES=false if the pending
  request list should survive longer than 10 minutes.
- The pinned group rules are also exempt - core.pin_group_rules drops their
  booking straight after posting, so the rules stay on top.
- A handler that books a shorter timer (for example the 60-second group timer
  notice) still wins, because its own add_message call runs after the send.

MEMBER COUNTS, PRIVATELY (/members)
- /members (or /membercounts) reports the member count of the group, the
  community channel and MyStorage.
- It is always delivered to the admin who asked: a private message, or a reply
  in the group only if that admin has never opened /start.
- A chat the bot cannot read shows "not visible"; the bot must be a member, and
  an admin, of that chat.

MOVIE REQUEST FORMAT (/request)
- Users write: /request Movie Name - Year - Audio Language - Resolution
  Example: /request Don - 2002 - Hindi - 1080p
  The plain form /request Don 2002 Hindi 1080p works too.
- Year is a 1900-2099 number, quality is 480p/720p/1080p/2160p/4K/8K/HD/SD,
  audio is a known language name (Hindi, English, Tamil, Telugu, Dual Audio,
  Dubbed, ...). Anything left over is the movie name, so a multi-word title is
  safe.
- Year, audio and quality are stored in their own columns of bot.db and shown
  on the confirmation, the admin notice, the hourly pending list and the Movie
  Requests worksheet (which gets the full "Don (2002) - Hindi - 1080p" line).

USER LANGUAGES (/language)
- /language or the inline menu lets each user pick their own language; it is
  saved per user in bot.db and used for everything that user then sees: search
  results, the download button, Movie Details, the delivered file caption, the
  request confirmation, the 18+ confirmation, the private-search notice, the
  group timer and rule notices.
- The first page holds English, Hindi, Bangla, Tamil, Telugu, Marathi, Gujarati
  and Punjabi with full translations. "🌐 More languages" pages through 34
  languages in their own script.
- A language without a translation yet shows English, never a blank message:
  every string lives in services/i18n.py, and adding a language is one dict
  there.
- The four reply-keyboard buttons (🎬 Search Movie, 🎥 Request Movie,
  📢 Join Channel, 👥 Join Group) and /help stay English, because the bot
  matches on that exact button text; their answers are translated.

MESSAGE LOOKS
- User-facing messages share one shape: the brand line, a ━━━ divider, then
  emoji-labelled lines. Google Sheet status is no longer printed in front of
  users - a sheet that refused a row is logged instead.
