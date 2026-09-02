from src.work_order_login import CodeRequest, LoginRequest, Photo, WorkOrderLogin


class RecordingSms:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def request_code(self, phone: str, idempotency_key: str) -> dict:
        self.calls.append(("otp", phone, idempotency_key))
        return {"status": "sent"}

    def verify_code(self, phone: str, code: str, idempotency_key: str) -> dict:
        self.calls.append(("verify", phone, code, idempotency_key))
        return {"verified": True}


def test_verified_technician_is_dispatched_with_no_follow_up_when_arrival_photo_exists() -> None:
    sms = RecordingSms()
    login = WorkOrderLogin(sms)
    code_request = CodeRequest(phone="+15551234567", work_order_id="WO-1042")
    login.send_code(code_request)

    result = login.verify_and_dispatch(
        LoginRequest(
            phone=code_request.phone,
            code="123456",
            work_order_id=code_request.work_order_id,
            photos=[Photo(photo_id="photo-1", label="arrival")],
        )
    )

    assert [call[0] for call in sms.calls] == ["otp", "verify"]
    assert result.dispatch_status == "dispatched"
    assert result.technician_follow_up is False
    assert result.photos[0].photo_id == "photo-1"


def test_missing_arrival_photo_marks_technician_follow_up() -> None:
    login = WorkOrderLogin(RecordingSms())
    result = login.verify_and_dispatch(
        LoginRequest(
            phone="+15551234567",
            code="123456",
            work_order_id="WO-1043",
            photos=[],
        )
    )
    assert result.dispatch_status == "dispatched"
    assert result.technician_follow_up is True
