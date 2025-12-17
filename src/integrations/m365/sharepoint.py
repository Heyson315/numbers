"""
SharePoint Manager

SharePoint List/Library integration for financial documents.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import os

from src.audit_logging import AuditLogger, AuditEventType
from .graph_client import GraphClient
from .models import M365SharePointList, M365SharePointItem


class SharePointManager:
    """Manage SharePoint List and Library operations."""
    
    def __init__(
        self,
        graph_client: GraphClient,
        site_id: Optional[str] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize SharePoint manager.
        
        Args:
            graph_client: GraphClient instance
            site_id: SharePoint site ID
            audit_logger: Audit logger
        """
        self.graph_client = graph_client
        self.site_id = site_id or os.getenv("SHAREPOINT_SITE_ID")
        self.audit_logger = audit_logger or AuditLogger()
        
        if not self.site_id:
            raise ValueError("SHAREPOINT_SITE_ID must be configured")
    
    async def get_lists(self, user_id: str = "system") -> List[M365SharePointList]:
        """
        Get all SharePoint lists in the site.
        
        Args:
            user_id: User ID for audit logging
        
        Returns:
            List of M365SharePointList objects
        """
        endpoint = f"sites/{self.site_id}/lists"
        
        try:
            response = await self.graph_client.request(
                "GET",
                endpoint,
                user_id=user_id
            )
            
            lists = []
            for list_data in response.get("value", []):
                sp_list = M365SharePointList(
                    id=list_data["id"],
                    display_name=list_data["displayName"],
                    name=list_data.get("name"),
                    description=list_data.get("description"),
                    created_datetime=datetime.fromisoformat(list_data["createdDateTime"].replace("Z", "+00:00")),
                    last_modified_datetime=datetime.fromisoformat(list_data["lastModifiedDateTime"].replace("Z", "+00:00")),
                    web_url=list_data.get("webUrl"),
                    list_template=list_data.get("list", {}).get("template")
                )
                lists.append(sp_list)
            
            self.audit_logger.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                user_id=user_id,
                action="get_sharepoint_lists",
                resource=f"sharepoint/site/{self.site_id}",
                status="success",
                details={"count": len(lists)}
            )
            
            return lists
            
        except Exception as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user_id,
                action="get_sharepoint_lists",
                resource=f"sharepoint/site/{self.site_id}",
                status="error",
                details={"error": str(e)}
            )
            raise
    
    async def get_list_items(
        self,
        list_id: str,
        user_id: str = "system"
    ) -> List[M365SharePointItem]:
        """
        Get items from a SharePoint list.
        
        Args:
            list_id: SharePoint list ID
            user_id: User ID for audit logging
        
        Returns:
            List of M365SharePointItem objects
        """
        endpoint = f"sites/{self.site_id}/lists/{list_id}/items?expand=fields"
        
        try:
            response = await self.graph_client.request(
                "GET",
                endpoint,
                user_id=user_id
            )
            
            items = []
            for item_data in response.get("value", []):
                sp_item = M365SharePointItem(
                    id=item_data["id"],
                    fields=item_data.get("fields", {}),
                    created_datetime=datetime.fromisoformat(item_data["createdDateTime"].replace("Z", "+00:00")) if "createdDateTime" in item_data else None,
                    last_modified_datetime=datetime.fromisoformat(item_data["lastModifiedDateTime"].replace("Z", "+00:00")) if "lastModifiedDateTime" in item_data else None,
                    web_url=item_data.get("webUrl"),
                    etag=item_data.get("eTag")
                )
                items.append(sp_item)
            
            self.audit_logger.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                user_id=user_id,
                action="get_sharepoint_items",
                resource=f"sharepoint/list/{list_id}",
                status="success",
                details={"count": len(items)}
            )
            
            return items
            
        except Exception as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user_id,
                action="get_sharepoint_items",
                resource=f"sharepoint/list/{list_id}",
                status="error",
                details={"error": str(e)}
            )
            raise
    
    async def create_list_item(
        self,
        list_id: str,
        fields: Dict[str, Any],
        user_id: str = "system"
    ) -> M365SharePointItem:
        """
        Create item in SharePoint list.
        
        Args:
            list_id: SharePoint list ID
            fields: Field values for the item
            user_id: User ID for audit logging
        
        Returns:
            M365SharePointItem object
        """
        endpoint = f"sites/{self.site_id}/lists/{list_id}/items"
        
        try:
            response = await self.graph_client.request(
                "POST",
                endpoint,
                user_id=user_id,
                json={"fields": fields}
            )
            
            sp_item = M365SharePointItem(
                id=response["id"],
                fields=response.get("fields", {}),
                created_datetime=datetime.fromisoformat(response["createdDateTime"].replace("Z", "+00:00")) if "createdDateTime" in response else None,
                last_modified_datetime=datetime.fromisoformat(response["lastModifiedDateTime"].replace("Z", "+00:00")) if "lastModifiedDateTime" in response else None,
                web_url=response.get("webUrl"),
                etag=response.get("eTag")
            )
            
            self.audit_logger.log_event(
                event_type=AuditEventType.DATA_MODIFY,
                user_id=user_id,
                action="create_sharepoint_item",
                resource=f"sharepoint/list/{list_id}",
                status="success",
                details={"item_id": sp_item.id}
            )
            
            return sp_item
            
        except Exception as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user_id,
                action="create_sharepoint_item",
                resource=f"sharepoint/list/{list_id}",
                status="error",
                details={"error": str(e)}
            )
            raise
    
    async def sync_financial_documents(
        self,
        list_id: str,
        documents: List[Dict[str, Any]],
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """
        Sync financial document metadata to SharePoint list.
        
        Args:
            list_id: SharePoint list ID
            documents: List of document metadata
            user_id: User ID for audit logging
        
        Returns:
            Sync result
        """
        created_items = []
        errors = []
        
        for doc in documents:
            try:
                item = await self.create_list_item(list_id, doc, user_id)
                created_items.append(item.dict())
            except Exception as e:
                errors.append({"document": doc, "error": str(e)})
        
        result = {
            "status": "success" if not errors else "partial",
            "created_count": len(created_items),
            "error_count": len(errors),
            "created_items": created_items,
            "errors": errors,
            "synced_at": datetime.utcnow().isoformat()
        }
        
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_MODIFY,
            user_id=user_id,
            action="sync_financial_documents",
            resource=f"sharepoint/list/{list_id}",
            status=result["status"],
            details={"created": len(created_items), "errors": len(errors)}
        )
        
        return result
