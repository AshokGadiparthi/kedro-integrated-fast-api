"""
Authentication Utilities - PHASE 0
====================================
Password hashing and JWT token management

HOW IT WORKS:
1. User registers with password
2. Password is hashed with bcrypt
3. Hash is stored in database (not password!)
4. User logs in with email + password
5. Password verified against hash
6. JWT token created if password matches
7. Token sent to frontend
8. Frontend sends token with every request
9. Token verified - user_id extracted
10. User can only access their own data
"""

from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# PASSWORD HASHING
# ============================================================================

# BCrypt configuration
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Security level (higher = slower but more secure)
)

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password (safe to store in database)
        
    Example:
        hashed = hash_password("mypassword123")
        # Output: $2b$12$...long hash string...
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hash
    
    Args:
        plain_password: Plain text password from user
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
        
    Example:
        is_correct = verify_password("mypassword123", "$2b$12$...")
        # Output: True or False
    """
    return pwd_context.verify(plain_password, hashed_password)

# ============================================================================
# JWT TOKEN HANDLING
# ============================================================================

try:
    from jose import JWTError, jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    logger.warning("⚠️  python-jose not installed. JWT tokens disabled.")
    JWTError = Exception
    jwt = None

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-to-random-string")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Token expires in 30 minutes

# Security warning
if SECRET_KEY == "dev-secret-key-change-in-production-to-random-string":
    logger.warning("⚠️  Using default SECRET_KEY. Change in production!")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    
    Args:
        data: Dictionary to encode in token (e.g., {"sub": user_id})
        expires_delta: Token expiration time (uses default if not provided)
        
    Returns:
        JWT token string
        
    Example:
        token = create_access_token({"sub": "user_id_123"})
        # Output: "eyJ0eXAiOiJKV1QiLCJhbGc..."
    """
    if not JWT_AVAILABLE:
        raise RuntimeError("python-jose is required for JWT tokens")
    
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add expiration to token
    to_encode.update({"exp": expire})
    
    # Encode token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    logger.info(f"✅ Token created, expires at {expire}")
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """
    Verify JWT token and extract user_id
    
    Args:
        token: JWT token string
        
    Returns:
        user_id if token is valid, None otherwise
        
    Example:
        user_id = verify_token("eyJ0eXAiOiJKV1QiLCJhbGc...")
        if user_id:
            # Token is valid, user_id is extracted
        else:
            # Token is invalid
    """
    if not JWT_AVAILABLE:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if not user_id:
            logger.warning("⚠️  Token has no 'sub' claim")
            return None
        
        return user_id
        
    except JWTError as e:
        logger.warning(f"⚠️  Token verification failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error verifying token: {str(e)}")
        return None

# ============================================================================
# TOKEN EXTRACTION FROM HEADER
# ============================================================================

def extract_token_from_header(auth_header: Optional[str]) -> Optional[str]:
    """
    Extract Bearer token from Authorization header
    
    Args:
        auth_header: Authorization header value (e.g., "Bearer token123...")
        
    Returns:
        Token string if valid format, None otherwise
        
    Example:
        token = extract_token_from_header("Bearer eyJ0eXAi...")
        # Output: "eyJ0eXAi..."
    """
    if not auth_header:
        return None
    
    parts = auth_header.split()
    
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]
