from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
import logging

logger = logging.getLogger(__name__)


class AuthHandler:
    def __init__(self, config: Dict[str, Any]):
        self.secret_key = config["api"]["secret_key"]
        self.token_expiry = config["api"].get(
            "token_expiry", 3600)  # 1 hour default
        self.algorithm = "HS256"
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

    async def create_token(self, data: Dict[str, Any]) -> str:
        """Create new access token"""
        try:
            # Add expiry time
            expires = datetime.utcnow() + timedelta(seconds=self.token_expiry)
            to_encode = {
                **data,
                "exp": expires
            }

            # Create token
            token = jwt.encode(
                to_encode,
                self.secret_key,
                algorithm=self.algorithm
            )

            return token

        except Exception as e:
            logger.error(f"Error creating token: {str(e)}")
            raise

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode access token"""
        try:
            # Decode and verify token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            # Check expiry
            if datetime.fromtimestamp(payload["exp"]) < datetime.utcnow():
                raise HTTPException(
                    status_code=401,
                    detail="Token has expired"
                )

            return payload

        except jwt.JWTError as e:
            logger.error(f"JWT error: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Error verifying token"
            )

    async def get_current_user(
        self,
        token: str = Security(OAuth2PasswordBearer(tokenUrl="token"))
    ) -> Dict[str, Any]:
        """Get current authenticated user from token"""
        try:
            payload = await self.verify_token(token)
            return payload
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}")
            raise
