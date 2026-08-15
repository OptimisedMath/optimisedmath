# API contract

When changing request/response shapes, update the backend Pydantic models and the frontend types that mirror them. JSON field names are stable wire format — see `CONTEXT.md` for domain terms.

Current locations:


| Side                     | Path                            |
| ------------------------ | ------------------------------- |
| Backend models           | `backend/models.py`             |
| Session wire types       | `frontend/lib/session/types.ts` |
| Curriculum catalog types | `frontend/lib/types.ts`         |


## API calls

Relative `/api/`* paths; Next.js rewrites to FastAPI on `:8000`.