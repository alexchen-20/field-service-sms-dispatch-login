import os

from src.infrai_sms import InfraiSms
from src.work_order_login import CodeRequest, LoginRequest, Photo, WorkOrderLogin


phone = os.environ.get("TECHNICIAN_PHONE")
work_order_id = os.environ.get("WORK_ORDER_ID", "WO-1042")
if not phone:
    raise SystemExit("TECHNICIAN_PHONE is required")

login = WorkOrderLogin(InfraiSms(os.environ["INFRAI_API_KEY"]))
login.send_code(CodeRequest(phone=phone, work_order_id=work_order_id))
code = input("Code from the technician's phone: ").strip()
result = login.verify_and_dispatch(
    LoginRequest(
        phone=phone,
        code=code,
        work_order_id=work_order_id,
        photos=[Photo(photo_id="photo-1", label="arrival")],
    )
)
print(result.model_dump_json(indent=2))
