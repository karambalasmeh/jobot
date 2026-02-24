from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine

# Import models so SQLAlchemy registers tables for create_all().
import app.models.log_record  # noqa: F401
import app.models.ticket  # noqa: F401
import app.models.user  # noqa: F401
import app.models.conversation  # noqa: F401
import app.models.message  # noqa: F401
import app.models.resolved_answer  # noqa: F401

# Routes
from app.api.routes import auth, chat, conversations, hitl, ingest, logs
from app.models.conversation import Conversation
from app.models.user import User
from app.services.auth_service import hash_password
from app.services.text_repair import repair_utf8_mojibake_cp1252

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up: initializing database...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Database initialized successfully.")

        # Optional admin bootstrap for first-time setup (or password reset).
        if settings.ADMIN_BOOTSTRAP_USERNAME and settings.ADMIN_BOOTSTRAP_PASSWORD:
            db = SessionLocal()
            try:
                admin = db.query(User).filter(User.username == settings.ADMIN_BOOTSTRAP_USERNAME).first()
                password_hash = hash_password(settings.ADMIN_BOOTSTRAP_PASSWORD)
                if not admin:
                    admin = User(
                        username=settings.ADMIN_BOOTSTRAP_USERNAME,
                        password_hash=password_hash,
                        is_admin=True,
                    )
                    db.add(admin)
                    db.commit()
                    logger.info("Bootstrapped admin user '%s'", settings.ADMIN_BOOTSTRAP_USERNAME)
                else:
                    admin.password_hash = password_hash
                    admin.is_admin = True
                    db.commit()
                    logger.info("Updated admin user '%s' from bootstrap settings", settings.ADMIN_BOOTSTRAP_USERNAME)
            finally:
                db.close()

        # Repair legacy mojibake in persisted conversation titles (Arabic text stored with wrong decoding).
        db = SessionLocal()
        try:
            changed = 0
            for conv in db.query(Conversation).all():
                if not conv.title:
                    continue
                fixed = repair_utf8_mojibake_cp1252(conv.title)
                if fixed != conv.title:
                    conv.title = fixed
                    changed += 1
            if changed:
                db.commit()
                logger.info("Repaired %s conversation title(s) with mojibake text", changed)
        finally:
            db.close()
    except Exception as e:
        print(f"Database initialization failed: {e}")

    yield
    print("Shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Allow frontend access (tighten allow_origins in production).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat Interface"])
app.include_router(conversations.router, prefix=f"{settings.API_V1_STR}/conversations", tags=["Conversations"])
app.include_router(hitl.router, prefix=f"{settings.API_V1_STR}/hitl", tags=["Human-in-the-Loop"])
app.include_router(ingest.router, prefix=f"{settings.API_V1_STR}/ingest", tags=["Data Ingestion"])
app.include_router(logs.router, prefix=f"{settings.API_V1_STR}/admin", tags=["Admin & Diagnostics"])


@app.get("/")
def read_root():
    return {"status": "success", "message": f"Welcome to {settings.PROJECT_NAME} API"}
