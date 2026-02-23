from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.models import ticket

# استيراد المسارات بما فيها Ingest
from app.api.routes import chat, hitl, ingest, logs

from contextlib import asynccontextmanager

# ... (rest of imports)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Starting up: initializing database...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization failed: {e}")
    yield
    # Shutdown logic (optional)
    print("Shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# السماح للفرونت إند بالاتصال بالباك إند (يجب إضافة الـ Middleware قبل تسجيل المسارات)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # في الإنتاج بنحط رابط الموقع الحقيقي، بس هسا بنسمح للكل عشان التطوير
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# دمج المسارات
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat Interface"])
app.include_router(hitl.router, prefix=f"{settings.API_V1_STR}/hitl", tags=["Human-in-the-Loop"])
app.include_router(ingest.router, prefix=f"{settings.API_V1_STR}/ingest", tags=["Data Ingestion"])
app.include_router(logs.router, prefix=f"{settings.API_V1_STR}/admin", tags=["Admin & Diagnostics"])

@app.get("/")
def read_root():
    return {"status": "success", "message": f"Welcome to {settings.PROJECT_NAME} API"}