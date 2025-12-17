"""
Microsoft 365 Graph Integration Module

Provides Azure AD OAuth 2.0 authentication and Microsoft Graph API integration
for OneDrive and SharePoint with enterprise security controls.
"""

from .graph_client import GraphClient
from .onedrive import OneDriveManager
from .sharepoint import SharePointManager
from .models import (
    M365File,
    M365DriveItem,
    M365SharePointList,
    M365SharePointItem,
    M365Webhook
)

__all__ = [
    "GraphClient",
    "OneDriveManager",
    "SharePointManager",
    "M365File",
    "M365DriveItem",
    "M365SharePointList",
    "M365SharePointItem",
    "M365Webhook"
]
