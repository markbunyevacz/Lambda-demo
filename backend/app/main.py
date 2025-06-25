from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from dotenv import load_dotenv

# Környezeti változók betöltése
load_dotenv()

app = FastAPI(
    title="Lambda.hu Építőanyag AI Rendszer",
    description="AI-alapú építőanyag keresési és ajánlási rendszer",
    version="1.0.0"
)

# CORS beállítások
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Adatbázis táblák létrehozása
@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root():
    return {
        "message": "Üdvözöljük a Lambda.hu AI API-ban",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Az API működik"} 