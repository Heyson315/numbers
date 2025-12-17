"""
OneDrive Manager

File sync operations with delta sync and validation for financial documents.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os

from src.audit_logging import AuditLogger, AuditEventType
from src.security import SecureDataHandler
from .graph_client import GraphClient
from .models import M365DriveItem, M365Webhook, DeltaSyncState, FileValidationResult, FileType


class OneDriveManager:
    """Manage OneDrive file operations with delta sync."""
    
    ALLOWED_FILE_TYPES = [ft.value for ft in FileType]
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    
    def __init__(
        self,
        graph_client: GraphClient,
        root_folder: Optional[str] = None,
        audit_logger: Optional[AuditLogger] = None,
        secure_data_handler: Optional[SecureDataHandler] = None
    ):
        """
        Initialize OneDrive manager.
        
        Args:
            graph_client: GraphClient instance
            root_folder: Root folder name for financial documents
            audit_logger: Audit logger
            secure_data_handler: Secure data handler for encryption
        """
        self.graph_client = graph_client
        self.root_folder = root_folder or os.getenv("ONEDRIVE_ROOT_FOLDER", "FinancialDocuments")
        self.audit_logger = audit_logger or AuditLogger()
        self.secure_data_handler = secure_data_handler or SecureDataHandler()
        self._delta_tokens: Dict[str, str] = {}
    
    def validate_file(self, file_data: M365DriveItem) -> FileValidationResult:
        """
        Validate file type and size for financial documents.
        
        Args:
            file_data: M365DriveItem to validate
        
        Returns:
            FileValidationResult
        """
        errors = []
        file_type = None
        
        # Extract file extension
        if '.' in file_data.name:
            file_type = file_data.name.split('.')[-1].lower()
        
        # Validate file type
        if file_type not in self.ALLOWED_FILE_TYPES:
            errors.append(f"File type .{file_type} not allowed. Allowed types: {', '.join(self.ALLOWED_FILE_TYPES)}")
        
        # Validate file size
        if file_data.size and file_data.size > self.MAX_FILE_SIZE:
            errors.append(f"File size {file_data.size} bytes exceeds maximum {self.MAX_FILE_SIZE} bytes")
        
        return FileValidationResult(
            is_valid=len(errors) == 0,
            file_type=file_type,
            file_size=file_data.size or 0,
            validation_errors=errors
        )
    
    async def list_files(
        self,
        folder_path: Optional[str] = None,
        user_id: str = "system"
    ) -> List[M365DriveItem]:
        """
        List files in OneDrive folder.
        
        Args:
            folder_path: Optional specific folder path (relative to root)
            user_id: User ID for audit logging
        
        Returns:
            List of M365DriveItem objects
        """
        folder = folder_path or self.root_folder
        endpoint = f"me/drive/root:/{folder}:/children"
        
        try:
            response = await self.graph_client.request(
                "GET",
                endpoint,
                user_id=user_id
            )
            
            items = []
            for item_data in response.get("value", []):
                drive_item = M365DriveItem(
                    id=item_data["id"],
                    name=item_data["name"],
                    size=item_data.get("size", 0),
                    created_datetime=datetime.fromisoformat(item_data["createdDateTime"].replace("Z", "+00:00")),
                    last_modified_datetime=datetime.fromisoformat(item_data["lastModifiedDateTime"].replace("Z", "+00:00")),
                    web_url=item_data.get("webUrl"),
                    download_url=item_data.get("@microsoft.graph.downloadUrl"),
                    is_folder="folder" in item_data,
                    parent_reference=item_data.get("parentReference"),
                    file=item_data.get("file"),
                    folder=item_data.get("folder")
                )
                items.append(drive_item)
            
            self.audit_logger.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                user_id=user_id,
                action="list_onedrive_files",
                resource=f"onedrive/{folder}",
                status="success",
                details={"count": len(items)}
            )
            
            return items
            
        except Exception as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user_id,
                action="list_onedrive_files",
                resource=f"onedrive/{folder}",
                status="error",
                details={"error": str(e)}
            )
            raise
    
    async def upload_file(
        self,
        file_name: str,
        content: bytes,
        folder_path: Optional[str] = None,
        user_id: str = "system",
        encrypt: bool = True
    ) -> M365DriveItem:
        """
        Upload file to OneDrive with optional encryption.
        
        Args:
            file_name: Name of file to upload
            content: File content as bytes
            folder_path: Optional folder path (relative to root)
            user_id: User ID for audit logging
            encrypt: Whether to encrypt file before upload
        
        Returns:
            M365DriveItem for uploaded file
        """
        folder = folder_path or self.root_folder
        
        # Validate file size
        if len(content) > self.MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds maximum of {self.MAX_FILE_SIZE} bytes")
        
        # Encrypt if requested
        if encrypt:
            content = self.secure_data_handler.encrypt_file(content)
            file_name = f"{file_name}.encrypted"
        
        endpoint = f"me/drive/root:/{folder}/{file_name}:/content"
        
        try:
            response = await self.graph_client.request(
                "PUT",
                endpoint,
                user_id=user_id,
                content=content,
                headers={"Content-Type": "application/octet-stream"}
            )
            
            drive_item = M365DriveItem(
                id=response["id"],
                name=response["name"],
                size=response.get("size", 0),
                created_datetime=datetime.fromisoformat(response["createdDateTime"].replace("Z", "+00:00")),
                last_modified_datetime=datetime.fromisoformat(response["lastModifiedDateTime"].replace("Z", "+00:00")),
                web_url=response.get("webUrl"),
                download_url=response.get("@microsoft.graph.downloadUrl")
            )
            
            self.audit_logger.log_event(
                event_type=AuditEventType.FILE_UPLOAD,
                user_id=user_id,
                action="upload_to_onedrive",
                resource=f"onedrive/{folder}/{file_name}",
                status="success",
                details={"size": len(content), "encrypted": encrypt}
            )
            
            return drive_item
            
        except Exception as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user_id,
                action="upload_to_onedrive",
                resource=f"onedrive/{folder}/{file_name}",
                status="error",
                details={"error": str(e)}
            )
            raise
    
    async def download_file(
        self,
        file_id: str,
        user_id: str = "system",
        decrypt: bool = True
    ) -> bytes:
        """
        Download file from OneDrive.
        
        Args:
            file_id: OneDrive file ID
            user_id: User ID for audit logging
            decrypt: Whether to decrypt file after download
        
        Returns:
            File content as bytes
        """
        endpoint = f"me/drive/items/{file_id}/content"
        
        try:
            # Get download URL
            item_response = await self.graph_client.request(
                "GET",
                f"me/drive/items/{file_id}",
                user_id=user_id
            )
            
            download_url = item_response.get("@microsoft.graph.downloadUrl")
            if not download_url:
                raise ValueError("No download URL available")
            
            # Download file content
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(download_url, timeout=60.0)
                response.raise_for_status()
                content = response.content
            
            # Decrypt if requested and file is encrypted
            if decrypt and item_response["name"].endswith(".encrypted"):
                content = self.secure_data_handler.decrypt_file(content)
            
            self.audit_logger.log_event(
                event_type=AuditEventType.FILE_DOWNLOAD,
                user_id=user_id,
                action="download_from_onedrive",
                resource=f"onedrive/file/{file_id}",
                status="success",
                details={"size": len(content), "decrypted": decrypt}
            )
            
            return content
            
        except Exception as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user_id,
                action="download_from_onedrive",
                resource=f"onedrive/file/{file_id}",
                status="error",
                details={"error": str(e)}
            )
            raise
    
    async def get_delta_changes(
        self,
        folder_path: Optional[str] = None,
        user_id: str = "system"
    ) -> tuple[List[M365DriveItem], str]:
        """
        Get file changes using delta sync.
        
        Args:
            folder_path: Optional folder path
            user_id: User ID for audit logging
        
        Returns:
            Tuple of (changed items, new delta token)
        """
        folder = folder_path or self.root_folder
        delta_token = self._delta_tokens.get(folder)
        
        # Build endpoint with delta token if available
        if delta_token:
            endpoint = f"me/drive/root:/{folder}:/delta?token={delta_token}"
        else:
            endpoint = f"me/drive/root:/{folder}:/delta"
        
        try:
            response = await self.graph_client.request(
                "GET",
                endpoint,
                user_id=user_id
            )
            
            items = []
            for item_data in response.get("value", []):
                if "file" in item_data:  # Only process files, not folders
                    drive_item = M365DriveItem(
                        id=item_data["id"],
                        name=item_data["name"],
                        size=item_data.get("size", 0),
                        created_datetime=datetime.fromisoformat(item_data["createdDateTime"].replace("Z", "+00:00")),
                        last_modified_datetime=datetime.fromisoformat(item_data["lastModifiedDateTime"].replace("Z", "+00:00")),
                        web_url=item_data.get("webUrl"),
                        is_folder=False,
                        file=item_data.get("file")
                    )
                    items.append(drive_item)
            
            # Extract new delta token from response
            new_delta_token = response.get("@odata.deltaLink", "").split("token=")[-1] if "@odata.deltaLink" in response else delta_token
            
            if new_delta_token:
                self._delta_tokens[folder] = new_delta_token
            
            self.audit_logger.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                user_id=user_id,
                action="get_delta_changes",
                resource=f"onedrive/{folder}",
                status="success",
                details={"changes": len(items)}
            )
            
            return items, new_delta_token
            
        except Exception as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user_id,
                action="get_delta_changes",
                resource=f"onedrive/{folder}",
                status="error",
                details={"error": str(e)}
            )
            raise
    
    async def create_webhook(
        self,
        notification_url: str,
        folder_path: Optional[str] = None,
        user_id: str = "system"
    ) -> M365Webhook:
        """
        Create webhook for real-time file change notifications.
        
        Args:
            notification_url: URL to receive webhooks
            folder_path: Optional folder path to monitor
            user_id: User ID for audit logging
        
        Returns:
            M365Webhook object
        """
        folder = folder_path or self.root_folder
        resource = f"/me/drive/root:/{folder}"
        
        webhook = M365Webhook(
            resource=resource,
            change_type="created,updated,deleted",
            notification_url=notification_url,
            expiration_datetime=datetime.utcnow() + timedelta(days=3),  # Max 3 days for drive
            client_state="SecureRandomState123"
        )
        
        try:
            response = await self.graph_client.request(
                "POST",
                "subscriptions",
                user_id=user_id,
                json=webhook.dict(exclude_none=True, exclude={"id"})
            )
            
            webhook.id = response["id"]
            
            self.audit_logger.log_event(
                event_type=AuditEventType.SYSTEM_CONFIG,
                user_id=user_id,
                action="create_onedrive_webhook",
                resource=f"onedrive/{folder}",
                status="success",
                details={"webhook_id": webhook.id}
            )
            
            return webhook
            
        except Exception as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user_id,
                action="create_onedrive_webhook",
                resource=f"onedrive/{folder}",
                status="error",
                details={"error": str(e)}
            )
            raise
