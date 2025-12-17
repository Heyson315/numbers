"""
Microsoft 365 Pydantic Models

Defines data models for Microsoft Graph API entities with validation.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class FileType(Enum):
    """Supported financial document file types."""
    PDF = "pdf"
    EXCEL = "xlsx"
    EXCEL_OLD = "xls"
    CSV = "csv"
    WORD = "docx"
    IMAGE = "jpg"
    IMAGE_PNG = "png"


class M365File(BaseModel):
    """Microsoft 365 file metadata."""
    id: str
    name: str
    size: int = Field(..., ge=0)
    created_datetime: datetime
    modified_datetime: datetime
    web_url: Optional[str] = None
    download_url: Optional[str] = None
    file_type: Optional[str] = None
    parent_reference: Optional[Dict[str, str]] = None
    created_by: Optional[Dict[str, Any]] = None
    modified_by: Optional[Dict[str, Any]] = None
    
    @validator('file_type', pre=True, always=True)
    def extract_file_type(cls, v, values):
        """Extract file type from name if not provided."""
        if v:
            return v
        name = values.get('name', '')
        if '.' in name:
            return name.split('.')[-1].lower()
        return None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class M365DriveItem(BaseModel):
    """OneDrive/SharePoint drive item."""
    id: str
    name: str
    size: Optional[int] = 0
    created_datetime: datetime
    last_modified_datetime: datetime
    web_url: Optional[str] = None
    download_url: Optional[str] = None
    etag: Optional[str] = None
    ctag: Optional[str] = None
    is_folder: bool = False
    parent_reference: Optional[Dict[str, Any]] = None
    file: Optional[Dict[str, Any]] = None
    folder: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class M365SharePointList(BaseModel):
    """SharePoint List metadata."""
    id: str
    display_name: str
    name: Optional[str] = None
    description: Optional[str] = None
    created_datetime: datetime
    last_modified_datetime: datetime
    web_url: Optional[str] = None
    list_template: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class M365SharePointItem(BaseModel):
    """SharePoint List item."""
    id: str
    fields: Dict[str, Any] = Field(default_factory=dict)
    created_datetime: Optional[datetime] = None
    last_modified_datetime: Optional[datetime] = None
    web_url: Optional[str] = None
    etag: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class M365Webhook(BaseModel):
    """Microsoft Graph webhook subscription."""
    id: Optional[str] = None
    resource: str = Field(..., description="Resource to monitor")
    change_type: str = Field(..., description="Comma-separated: created,updated,deleted")
    notification_url: str = Field(..., description="Webhook callback URL")
    expiration_datetime: datetime
    client_state: Optional[str] = None
    
    @validator('change_type')
    def validate_change_type(cls, v):
        """Validate change types."""
        valid_types = {'created', 'updated', 'deleted'}
        types = set(t.strip() for t in v.split(','))
        if not types.issubset(valid_types):
            raise ValueError(f"Invalid change types. Must be one of: {valid_types}")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class M365TokenStorage(BaseModel):
    """Azure AD token storage."""
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: datetime
    token_type: str = "Bearer"
    scope: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DeltaSyncState(BaseModel):
    """Delta sync state for efficient change tracking."""
    resource_id: str
    delta_token: str
    last_sync: datetime
    sync_type: str = Field(..., description="files or lists")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FileValidationResult(BaseModel):
    """File validation result."""
    is_valid: bool
    file_type: Optional[str] = None
    file_size: int
    validation_errors: List[str] = Field(default_factory=list)
    mime_type: Optional[str] = None
    is_encrypted: Optional[bool] = None
