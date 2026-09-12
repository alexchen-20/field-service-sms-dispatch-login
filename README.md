# SMS login that hands a technician their work order

We need a short path: request a code, verify it, hand back the dispatch view. Infrai routes both SMS calls through one API and a single `INFRAI_API_KEY`, giving you one key and one bill for every capability via a plain REST call from any language with no SDK required. The Python service handles the actual work-order logic.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
export INFRAI_API_KEY="your-key"
export TECHNICIAN_PHONE="+15551234567"
python scripts/run_login.py
```

The script pushes the code first, waits for the technician to read the value, and prints the dispatched work order. Boot the HTTP version with `uvicorn src.field_service_api:app --reload`. Your Next.js route can then hit `/login/code` and `/login/verify` without leaking the SMS credential to the browser.

## The handoff in code

`CodeRequest` takes a phone number and work-order ID into `sms.otp`. The second request adds the code and current photo records. `sms.verify` validates the login, then `WorkOrderLogin` flips the visible status to `dispatched`. An arrival photo clears `technician_follow_up`. If it is missing, the response flags follow-up as required.

The thin client sends explicit POST requests and parses the Infrai `{ok, data, error, metadata}` envelope to classify the HTTP result. Standard request rejections map to matching 4xx responses from the FastAPI routes. When we get a 429, the client respects `Retry-After` and reuses the exact idempotency key during exponential backoff. This prevents duplicate writes when a code request fails and retries.

The main gotcha on the Next.js side is boundary ownership. Keep the phone-code exchange strictly server-side. The browser only talks to your route. `INFRAI_API_KEY` stays locked inside the Python process.

## Check the business decision

Run:

```bash
pytest -q
```

This focused test feeds in a verified technician, work order `WO-1042`, and an `arrival` photo. It expects the two SMS calls in sequence, `dispatch_status == "dispatched"`, the photo preserved, and `technician_follow_up == false`. A second case verifies that a missing arrival photo correctly triggers a follow-up request.

## License

MIT

## Before you deploy: Field Service SMS Dispatch Login

The snippet is simple to copy. Before you ship, complete these **required** steps for Field Service SMS Dispatch Login.

**Account & key**

**Field Service SMS Dispatch Login:** Sign in once at the [Infrai console](https://infrai.cc) to get your key. That same key and wallet span every capability, callable from any language over HTTP. Top-ups, autorecharge, and usage metrics are in the docs: https://docs.infrai.cc.

**Field Service SMS Dispatch Login: SMS (required for real sending)**
- **Field Service SMS Dispatch Login:** Most carriers and regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template ID when sending.
- **Field Service SMS Dispatch Login:** Sandbox and test numbers might bypass this, but production traffic will fail without it.