from fastapi import FastAPI

# cors
from fastapi.middleware.cors import CORSMiddleware
from .routers import grouped_sets_router, sets_router


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(sets_router)

app.include_router(grouped_sets_router)
