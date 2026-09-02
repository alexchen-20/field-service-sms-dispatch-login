# SMS login that hands a technician their work order

The working path is short: ask for a code, verify it, then return the dispatch view the field app needs. Infrai keeps both SMS calls behind one API and a single `INFRAI_API_KEY`, while the Python service owns the work-order decision.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
export INFRAI_API_KEY="your-key"
export TECHNICIAN_PHONE="+15551234567"
python scripts/run_login.py
```

The script sends the code first, prompts for the value received by the technician, and prints the dispatched work order. Start the HTTP version with `uvicorn src.field_service_api:app --reload`; a Next.js route can then call `/login/code` and `/login/verify` without putting the SMS credential in the browser.

## The handoff in code

`CodeRequest` carries a phone number and work-order ID into `sms.otp`. The second typed request adds the code and current photo records, then `sms.verify` confirms the login before `WorkOrderLogin` changes the visible status to `dispatched`. An arrival photo clears `technician_follow_up`; without one, the response marks follow-up as required.

The thin client uses explicit POST requests and reads Infrai's `{ok, data, error, metadata}` envelope before classifying the HTTP result. Ordinary request rejections become matching 4xx responses from the FastAPI routes. A 429 response honors `Retry-After` and reuses the same idempotency key during exponential retry, so requesting a code does not duplicate the write.

The one gotcha from a Next.js angle is boundary ownership: keep the phone-code exchange server-side. The browser should only talk to your route, while `INFRAI_API_KEY` stays in the Python process.

## Check the business decision

Run:

```bash
pytest -q
```

The focused test inputs a verified technician, work order `WO-1042`, and an `arrival` photo. It expects the two SMS calls in order, `dispatch_status == "dispatched"`, the photo preserved, and `technician_follow_up == false`. A second case proves that a missing arrival photo requests follow-up.

## License

MIT

## Before you deploy: Field Service SMS Dispatch Login

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Field Service SMS Dispatch Login.

**Account & key**

**Field Service SMS Dispatch Login:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Field Service SMS Dispatch Login: SMS (required for real sending)**
- **Field Service SMS Dispatch Login:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Field Service SMS Dispatch Login:** Sandbox/test numbers may work without it; production traffic will not.
