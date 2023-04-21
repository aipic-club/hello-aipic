from datetime import datetime
from sqlalchemy.orm import Session

from . import models,schemas

def create_admin(db: Session, admin: schemas.CreateAdmin):
    db_admin = models.Admin(**admin.dict())
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin

def get_admin(db: Session, username: str):
    return db.query(models.Admin).filter(
        models.Admin.username == username
    ).first()

def create_user_with_token(
    db: Session, 
    user: schemas.CreateUser, 
    token: schemas.UserToken
):
    try:
        with db.begin_nested():
            db_user = models.User(**user.dict())
            db.add(db_user)
            db.flush()
            
            expire_at = datetime.fromtimestamp(token.expire_at / 1000)
            db_token = models.Token(
                access_token=token.access_token, 
                token_type=token.token_type,
                scopes=",".join(token.scopes),
                expire_at=expire_at,
                remaining=token.ramaining,
                user_id=db_user.id
            )
            db.add(db_token)
            db.flush()

            db.commit()
    except:
        db.rollback()
        raise

def get_user(db: Session, username: str):
    return db.query(models.User).filter(
        models.User.username == username
    ).first()
