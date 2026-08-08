from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.db.seed import seed_data
from app.db.models import Customer

# Import API Routers
from app.api import simulations, customers, usage, ai, flexprice

# Initialize database tables
Base.metadata.create_all(bind=engine)

# Auto-seed the database if empty on startup
db = SessionLocal()
try:
    if db.query(Customer).count() == 0:
        print("Database is empty. Auto-seeding initial dataset...")
        seed_data(db)
finally:
    db.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to Vite origin (e.g. http://localhost:5173)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(simulations.router, prefix=settings.API_V1_STR)
app.include_router(customers.router, prefix=settings.API_V1_STR)
app.include_router(usage.router, prefix=settings.API_V1_STR)
app.include_router(ai.router, prefix=settings.API_V1_STR)
app.include_router(flexprice.router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {
        "name": settings.PROJECT_NAME,
        "status": "online",
        "api_prefix": settings.API_V1_STR
    }

# Manual seed endpoint if needed
@app.post(f"{settings.API_V1_STR}/seed")
def trigger_seed(db: Session = Depends(SessionLocal)):
    try:
        seed_data(db)
        return {"status": "success", "message": "Database seeded successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
