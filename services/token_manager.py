import secrets


class TokenManager:
    def __init__(self, db):
        self.db = db

    def generate_token(self, movie_id: int, seconds: int = 300) -> str:
        self.db.cleanup_tokens()
        token = secrets.token_urlsafe(18)
        self.db.create_download_token(token, movie_id, seconds)
        return token

    def verify_token(self, token: str):
        return self.db.verify_download_token(token)

    def remove_token(self, token: str):
        self.db.consume_download_token(token)
