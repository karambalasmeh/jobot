from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.models import ticket

# استيراد المسارات بما فيها Ingest
from app.api.routes import chat, hitl, ingest, logs

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
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