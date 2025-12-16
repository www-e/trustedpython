from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from dotenv import load_dotenv

from app.database.core import engine
from app.models.user import create_db_and_tables
from app.auth.routers import auth_router
from app.users.routers import users_router

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    await create_db_and_tables()
    yield

app = FastAPI(
    title="TrustedPython Backend API",
    description="Secure authentication system with role-based access control for Flutter frontend",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - production ready for any Flutter port
# Using environment variable for allowed origins, defaults to all for development
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/users", tags=["Users"])

@app.get("/")
def read_root():
    return {"message": "Welcome to TrustedPython Backend API", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "trustedpython-backend"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )