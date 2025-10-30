from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import auth, quizzes, challenges  # Import routers
from .db import database
from . import models

# ✅ إنشاء جميع الجداول في قاعدة البيانات (لو مش موجودة)
models.Base.metadata.create_all(bind=database.engine)

# ✅ تهيئة التطبيق
app = FastAPI(title="SCALE API", version="1.0.0")

# ✅ إعداد CORS (للسماح للـ Frontend بالاتصال)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",     # لـ React/Vite أثناء التطوير
        "http://127.0.0.1:5173"      # احتياطيًا للمسار المحلي
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ تسجيل Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(quizzes.router, prefix="/api/quizzes", tags=["Quizzes"])
app.include_router(challenges.router, prefix="/api/challenges", tags=["Challenges"])

# ✅ نقطة البداية (root endpoint)
@app.get("/")
def read_root():
    return {"message": "Welcome to the SCALE API 🚀"}
