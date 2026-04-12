"""Security schemas for request/response validation"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, validator


class ChangePasswordRequest(BaseModel):
    """Request schema for changing password"""

    current_password: str = Field(..., min_length=8, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

    @validator("new_password")
    def validate_password_strength(cls, v: str) -> str:
        """Ensure password meets security requirements"""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class ChangePasswordResponse(BaseModel):
    """Response schema for password change"""

    success: bool
    message: str


class LoginHistoryItem(BaseModel):
    """Single login history entry"""

    timestamp: datetime
    ip_address: str
    device_info: Optional[str] = None
    status: str  # success, failed, suspicious
    location: Optional[str] = None


class LoginHistoryResponse(BaseModel):
    """Response schema for login history"""

    total: int
    page: int
    page_size: int
    history: List[LoginHistoryItem]


class SecuritySettingsResponse(BaseModel):
    """Response schema for security settings"""

    two_factor_enabled: bool
    login_notifications: bool
    trusted_devices: List[Dict[str, Any]]
    security_questions: Dict[str, Any]
    last_password_change: Optional[datetime] = None
    active_sessions: int = 0


class UpdateSecuritySettingsRequest(BaseModel):
    """Request schema for updating security settings"""

    login_notifications: Optional[bool] = None
    security_questions: Optional[Dict[str, str]] = None


class TwoFactorSetupResponse(BaseModel):
    """Response schema for 2FA setup"""

    qr_code_url: str
    backup_codes: List[str]
    secret: str


class TwoFactorVerifyRequest(BaseModel):
    """Request schema for verifying 2FA"""

    code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")


class TwoFactorEnableRequest(BaseModel):
    """Request schema for enabling 2FA"""

    password: str = Field(..., description="Verify password before enabling 2FA")


class TwoFactorDisableRequest(BaseModel):
    """Request schema for disabling 2FA"""

    code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")


class AuditLogItem(BaseModel):
    """Single audit log entry"""

    timestamp: datetime
    event: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class AuditLogResponse(BaseModel):
    """Response schema for audit log"""

    total: int
    page: int
    page_size: int
    events: List[AuditLogItem]


class ReportSuspiciousActivityRequest(BaseModel):
    """Request schema for reporting suspicious activity"""

    activity_type: str = Field(..., description="Type of suspicious activity")
    description: str = Field(..., min_length=10, description="Detailed description")
    evidence: Optional[str] = Field(None, description="Any evidence or additional context")


class FreezeAccountRequest(BaseModel):
    """Request schema for freezing account"""

    reason: str = Field(..., min_length=10, description="Reason for freezing account")
    duration_hours: int = Field(
        ..., ge=1, le=720, description="Duration in hours (max 720 = 30 days)"
    )


class SecurityVulnerability(BaseModel):
    """Security vulnerability item"""

    severity: str  # low, medium, high, critical
    issue: str
    recommendation: str


class SecurityScoreResponse(BaseModel):
    """Response schema for security score"""

    score: int = Field(..., ge=0, le=100, description="Security score out of 100")
    vulnerabilities: List[SecurityVulnerability]
    recommendations: List[str]
    last_updated: datetime


class SuccessResponse(BaseModel):
    """Generic success response"""

    success: bool
    message: str
