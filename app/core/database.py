from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# إعداد الـ Engine للاتصال بقاعدة البيانات (SQLite حالياً كما حددنا في .env)
# connect_args={"check_same_thread": False} ضرورية فقط لـ SQLite في FastAPI
engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# إنشاء الـ SessionFactory لإدارة جلسات الاتصال
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# الـ Base class الذي سترث منه كل الـ Models الخاصة بنا
Base = declarative_base()