from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException

from .infrai_sms import InfraiError, InfraiSms
from .work_order_login import CodeRequest, DispatchView, LoginRequest, WorkOrderLogin


app = FastAPI(title="Field-service phone login")


def workflow() -> WorkOrderLogin:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise RuntimeError("INFRAI_API_KEY is required")
    return WorkOrderLogin(InfraiSms(api_key))


def client_error(error: InfraiError) -> HTTPException:
    status = error.status if 400 <= error.status < 500 else 502
    return HTTPException(status_code=status, detail={"code": error.code, "message": str(error)})


@app.post("/login/code", status_code=202)
def send_login_code(request: CodeRequest) -> dict[str, str]:
    try:
        workflow().send_code(request)
    except InfraiError as error:
        raise client_error(error) from error
    return {"status": "code_sent", "work_order_id": request.work_order_id}


@app.post("/login/verify", response_model=DispatchView)
def verify_login(request: LoginRequest) -> DispatchView:
    try:
        return workflow().verify_and_dispatch(request)
    except InfraiError as error:
        raise client_error(error) from error
