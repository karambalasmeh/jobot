# استخدام نسخة خفيفة ومستقرة من بايثون
FROM python:3.11-slim

# منع بايثون من كتابة ملفات .pyc وتفعيل طباعة الـ logs مباشرة
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# تحديد مجلد العمل داخل الحاوية
WORKDIR /code

# تحديث النظام وتنزيل الحزم الأساسية التي قد تحتاجها بعض المكتبات
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملف المتطلبات أولاً (للاستفادة من الـ Docker Cache)
COPY requirements.txt /code/

# تثبيت المكتبات
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# تنزيل نموذج الـ Embeddings مسبقاً داخل الحاوية (اختياري لكنه يسرع التشغيل الأول)
# RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-large')"

# نسخ باقي ملفات المشروع
COPY ./app /code/app

# كشف البورت الذي سيعمل عليه FastAPI
EXPOSE 8000

# أمر التشغيل الأساسي للسيرفر
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]