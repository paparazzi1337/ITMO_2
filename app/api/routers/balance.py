from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..schemas import TransactionCreate, TransactionResponse, BalanceResponse
from services.balance_services import BalanceService
from ..dependencies import get_current_user
from database.database import get_session
from models.base_user import BaseUser
from typing import List
from datetime import datetime

router = APIRouter(prefix="/balance", tags=["balance"])

@router.get("/", response_model=BalanceResponse)
def get_user_balance(
    current_user: BaseUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    balance_service = BalanceService(db)
    amount = balance_service.get_balance(current_user)
    return {"amount": amount, "updated_at": datetime.utcnow()}

@router.post("/deposit")
async def deposit_balance(
    request: Request,
    current_user: BaseUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    form_data = await request.form()
    try:
        amount = Decimal(form_data.get("amount"))
        description = form_data.get("description", "")
        
        balance_service = BalanceService(db)
        transaction_id = balance_service.deposit(
            user=current_user,
            amount=amount,
            description=description
        )
        
        return RedirectResponse(url="/balance", status_code=303)
        
    except ValueError as e:
        from fastapi.templating import Jinja2Templates
        templates = Jinja2Templates(directory="app/templates")
        
        return templates.TemplateResponse(
            "balance.html",
            {
                "request": request,
                "current_user": current_user,
                "error": str(e),
                "transactions": BalanceService(db).get_transaction_history(current_user.user_id)
            },
            status_code=400
        )

@router.get("/history", response_model=List[TransactionResponse])
def get_transaction_history(
    current_user: BaseUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    balance_service = BalanceService(db)
    return balance_service.get_transaction_history(current_user.user_id)