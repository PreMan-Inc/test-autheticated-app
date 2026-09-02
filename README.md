# Notes Service

A small authenticated API. It exists to be onboarded: connect it to PreMan as
though it were a new customer's backend, and watch what happens when five of its
seven routes answer 401.

## Routes

| Method | Path | Auth |
|---|---|---|
| GET | `/health` | public |
| POST | `/auth/login` | public |
| GET | `/me` | bearer |
| GET | `/notes` | bearer |
| POST | `/notes` | bearer |
| GET | `/notes/{note_id}` | bearer |
| DELETE | `/notes/{note_id}` | bearer |

`POST /notes` and `DELETE /notes/{note_id}` are a matched pair, so a create can
always be undone.

## The login

```bash
curl -X POST "$BASE_URL/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@preman.live","password":"PremanDemo123!"}'
```

Returns `{"access_token": "...", "token_type": "bearer", "expires_in": 900}`.
Send it back as `Authorization: Bearer <access_token>`.

Tokens last fifteen minutes by default. Set `TOKEN_TTL_SECONDS` lower to watch
something outlive its own credential.

## Running it

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then <http://localhost:8000/docs>.

## Deploying it

```bash
./infra/deploy.sh
```

Builds an arm64 bundle, uploads it, rolls the CloudFormation stack, and prints
the public URL. Requires AWS credentials.

State is in memory and resets with the process. Nothing here is worth keeping.
