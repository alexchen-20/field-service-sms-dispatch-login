from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field
from typing import Any


class Photo(BaseModel):
    photo_id: str
    label: str


class CodeRequest(BaseModel):
    phone: str = Field(pattern=r"^\+[1-9]\d{7,14}$")
    work_order_id: str = Field(min_length=1)


class LoginRequest(BaseModel):
    phone: str = Field(pattern=r"^\+[1-9]\d{7,14}$")
    code: str = Field(pattern=r"^\d{4,8}$")
    work_order_id: str = Field(min_length=1)
    photos: list[Photo] = Field(default_factory=list)


class DispatchView(BaseModel):
    work_order_id: str
    dispatch_status: str
    photos: list[Photo]
    technician_follow_up: bool


@dataclass
class WorkOrderLogin:
    sms: Any

    def send_code(self, request: CodeRequest) -> None:
        key = f"work-order:{request.work_order_id}:otp:{request.phone}"
        self.sms.request_code(request.phone, key)

    def verify_and_dispatch(self, request: LoginRequest) -> DispatchView:
        key = f"work-order:{request.work_order_id}:verify:{request.phone}:{request.code}"
        self.sms.verify_code(request.phone, request.code, key)
        has_arrival_photo = any(photo.label == "arrival" for photo in request.photos)
        return DispatchView(
            work_order_id=request.work_order_id,
            dispatch_status="dispatched",
            photos=request.photos,
            technician_follow_up=not has_arrival_photo,
        )
