from fastapi import APIRouter, Body, HTTPException

home_router = APIRouter()

@home_router.get('/')
async def index() -> dict:
    return {"message" : "HAHAHAHAHHAHAHAHAH"}