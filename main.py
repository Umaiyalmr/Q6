
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import jwt, JWTError, ExpiredSignatureError

# --------------------------------------------------
# Exact assigned JWT configuration
# --------------------------------------------------

ISSUER = "https://idp.exam.local"
AUDIENCE = "tds-dzkopdin.apps.exam.local"
ALGORITHM = "RS256"

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""

app = FastAPI(title="JWT Verification API")


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Request schema
# --------------------------------------------------

class VerifyRequest(BaseModel):
    token: str


# --------------------------------------------------
# POST /verify
# --------------------------------------------------

@app.post("/verify")
async def verify_token(body: VerifyRequest):
    try:
        # Verify signature, issuer, audience and expiration.
        claims = jwt.decode(
            body.token,
            PUBLIC_KEY,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            audience=AUDIENCE,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iss": True,
                "verify_aud": True,
                "require_exp": True,
                "require_iss": True,
                "require_aud": True,
            },
        )

        return {
            "valid": True,
            "email": claims.get("email", ""),
            "sub": claims.get("sub", ""),
            "aud": claims.get("aud", ""),
        }

    except (ExpiredSignatureError, JWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail={"valid": False},
        )
