import secrets
from datetime import datetime, timedelta


class TokenManager:
    _tokens = {}

    def generate_token(self, movie_id: int, seconds: int = 300) -> str:
        self.cleanup_expired_tokens()
        token = secrets.token_urlsafe(18)
        self._tokens[token] = {
            "movie_id": movie_id,
            "expire_time": datetime.now() + timedelta(seconds=seconds),
        }
        return token

    def verify_token(self, token: str):
        data = self._tokens.get(token)
        if not data:
            return None
        if datetime.now() > data["expire_time"]:
            self.remove_token(token)
            return None
        return data["movie_id"]

    def remove_token(self, token: str):
        self._tokens.pop(token, None)

    def cleanup_expired_tokens(self):
        now = datetime.now()
        for token in [t for t, d in self._tokens.items() if now > d["expire_time"]]:
            self.remove_token(token)
