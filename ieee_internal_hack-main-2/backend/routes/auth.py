from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import httpx

from ..database import get_db
from ..models.user import User
from ..schemas.user import UserCreate, UserLogin, FirebaseAuthRequest, TokenResponse, UserOut, UserUpdate
from ..auth import hash_password, verify_password, create_access_token, get_current_user
from ..config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_CERTS_URL = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
GOOGLE_TOKEN_INFO_URL = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/getAccountInfo"

@router.post("/register", response_model=TokenResponse)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        age=payload.age,
        sex=payload.sex,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))

@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))

@router.post("/google", response_model=TokenResponse)
async def google_auth(payload: FirebaseAuthRequest, db: Session = Depends(get_db)):
    """Verify Firebase ID token using Google's API and upsert user."""
    try:
        # Verify the Firebase ID token by calling Google's getAccountInfo
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={settings.FIREBASE_API_KEY}",
                json={"idToken": payload.firebase_token},
                timeout=5.0,
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid Firebase token")
            data = resp.json()
            users_data = data.get("users", [])
            if not users_data:
                raise HTTPException(status_code=401, detail="No user found for token")
            firebase_user = users_data[0]
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Could not verify Firebase token")

    firebase_uid = firebase_user.get("localId", "")
    email = firebase_user.get("email", "")
    name = payload.full_name or firebase_user.get("displayName", "")
    photo = payload.photo_url or firebase_user.get("photoUrl", "")

    if not email:
        raise HTTPException(status_code=400, detail="No email associated with this Google account")

    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(
            email=email,
            full_name=name,
            photo_url=photo,
            firebase_uid=firebase_uid,
        )
        db.add(user)
    else:
        user.firebase_uid = firebase_uid
        if name:
            user.full_name = name
        if photo:
            user.photo_url = photo

    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user
