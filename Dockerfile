# ═══════════════════════════════════════════
# صورة Python الرسمية النحيفة (slim) لتقليل الحجم
# ═══════════════════════════════════════════
FROM python:3.11-slim

# منع Python من كتابة ملفات pyc وتفعيل الإخراج الفوري للسجلات
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# مجلد العمل
WORKDIR /app

# تثبيت أدوات النظام المطلوبة (ffmpeg لتحميل الوسائط)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# نسخ المتطلبات أولاً (للاستفادة من Docker Cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ بقية المشروع
COPY . .

# إنشاء مجلدات السجلات والنسخ الاحتياطي
RUN mkdir -p logs backups

# تشغيل البوت
CMD ["python", "main.py"]
