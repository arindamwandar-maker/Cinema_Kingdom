import keepalive
from config import Config
from services.db_backup import DbBackupService

config = Config()
backup = DbBackupService(config)

# Runs before bot is imported: Database() silently creates an empty bot.db,
# which would leave nothing to restore afterwards.
backup.restore_if_missing()
backup.backup()
backup.start()

keepalive.start()

from bot import CinemaKingdomBot

CinemaKingdomBot().run()
