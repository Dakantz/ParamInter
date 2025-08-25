from fastapi import FastAPI

# cors
from fastapi.middleware.cors import CORSMiddleware
from .routers import data_router, dp_router


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data_router)
app.include_router(dp_router)