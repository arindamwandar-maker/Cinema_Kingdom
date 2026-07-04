from datetime import datetime, timedelta

class CooldownService:
    def __init__(self):
        self.cooldowns = {}  # user_id -> last_message_time
    
    def check_cooldown(self, user_id: int, cooldown_seconds: int = 60) -> bool:
        """
        Check if user is on cooldown.
        Returns True if user can send message, False if cooldown is active.
        """
        now = datetime.now()
        
        if user_id in self.cooldowns:
            last_time = self.cooldowns[user_id]
            if (now - last_time) < timedelta(seconds=cooldown_seconds):
                return False  # Cooldown active
        
        # Update cooldown
        self.cooldowns[user_id] = now
        return True  # Can send message
    
    def get_remaining_time(self, user_id: int, cooldown_seconds: int = 60) -> int:
        """Get remaining cooldown time in seconds"""
        if user_id not in self.cooldowns:
            return 0
        
        last_time = self.cooldowns[user_id]
        elapsed = (datetime.now() - last_time).seconds
        remaining = cooldown_seconds - elapsed
        
        return max(0, remaining)