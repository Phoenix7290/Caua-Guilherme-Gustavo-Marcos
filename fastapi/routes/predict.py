import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from database import get_session
from models.schemas import PredictRequest, PredictResponse, PredictionRead
from models.tables import Prediction, User
from security.auth import get_current_user

router = APIRouter(prefix="/predict", tags=["Predict"])

_INTENT_RULES = [
    (r"\b(reembolso|reembolsar|devolu|refund|dinheiro de volta)\b", "Refund Request", 0.91),
    (r"\b(cancelar|cancelamento|cancel)\b", "Cancellation Request", 0.88),
    (r"\b(cobran|fatura|boleto|billing|invoice|charge)\b", "Billing Inquiry", 0.85),
    (
        r"\b(erro|bug|falha|crash|n[ãa]o funciona|technical|problema t[eé]cnico)\b",
        "Technical Issue",
        0.87,
    ),
    (r"\b(informa|d[úu]vida|como funciona|product|produto)\b", "Product Inquiry", 0.82),
]


def _classify(text: str):
    lower = text.lower()
    for pattern, intent, confidence in _INTENT_RULES:
        if re.search(pattern, lower):
            return intent, confidence
    return "Product Inquiry", 0.60


@router.post("", response_model=PredictResponse)
def predict(
    body: PredictRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Classifica a intenção do ticket e salva o registro associado ao owner_id do usuário autenticado.
    Rejeita campos extras no body graças a extra='forbid' no schema PredictRequest.
    """
    intent, confidence = _classify(body.text)
    prediction = Prediction(
        owner_id=current_user.id,
        text=body.text,
        intent=intent,
        confidence=confidence,
    )
    session.add(prediction)
    session.commit()
    session.refresh(prediction)
    return PredictResponse(
        id=prediction.id,
        intent=intent,
        confidence=confidence,
        message="Intenção classificada por stub rule-based (modelo ML pendente).",
    )


@router.get("", response_model=list[PredictionRead])
def list_predictions(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Lista apenas as predições de posse do usuário autenticado."""
    return session.exec(select(Prediction).where(Prediction.owner_id == current_user.id)).all()


@router.get("/{prediction_id}", response_model=PredictionRead)
def get_prediction(
    prediction_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Retorna uma predição por ID do usuário autenticado.

    Mitigação de BOLA (Broken Object Level Authorization - OWASP Top 10):
    Valida se o recurso pertence ao usuário autenticado (prediction.owner_id == current_user.id).
    Caso o ID não exista ou pertença a outro usuário, a API não retorna o recurso e responde com
    404 (Not Found) para evitar enumeração de recursos e vazamento de metadados.
    """
    prediction = session.get(Prediction, prediction_id)
    if prediction is None or prediction.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Predição não encontrada.",
        )
    return prediction
