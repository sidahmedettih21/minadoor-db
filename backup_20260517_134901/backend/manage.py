import asyncio
import os
from app.database import async_session
from app.models import User
from app.auth import get_password_hash
import secrets

async def create_admin():
    email = os.getenv("ADMIN_EMAIL", "admin@minadoor.com")
    password = os.getenv("ADMIN_PASSWORD")
    if not password:
        password = secrets.token_urlsafe(16)
        print(f"No ADMIN_PASSWORD set. Generated one: {password}")
    async with async_session() as session:
        existing = await session.get(User, email)
        if existing:
            print("Admin already exists.")
            return
        user = User(
            email=email,
            password_hash=get_password_hash(password),
            full_name="Admin",
            role="admin"
        )
        session.add(user)
        await session.commit()
        print(f"Admin created: {email} / {password}")

if __name__ == "__main__":
    asyncio.run(create_admin())
