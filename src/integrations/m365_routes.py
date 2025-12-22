"""
Microsoft 365 Integration Routes

FastAPI routes for SharePoint, OneDrive, Power BI, and Power Automate integration.
"""

import os
import logging
from typing import Optional, Any
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Try to import graph client
try:
    from .graph_client import (
        GraphClient,
        EncyclopediaClient,
        ProjectManagementClient,
        PowerAutomateClient
    )
    GRAPH_AVAILABLE = True
except ImportError:
    GRAPH_AVAILABLE = False
    logger.warning("Graph client not available. Install azure-identity and httpx.")

m365_router = APIRouter(prefix="/m365", tags=["Microsoft 365"])

# Global instances (initialized on first use)
_graph_client: Optional[GraphClient] = None
_encyclopedia_client: Optional[EncyclopediaClient] = None
_project_client: Optional[ProjectManagementClient] = None
_powerautomate_client: Optional[PowerAutomateClient] = None


# =============================================================================
# Pydantic Models
# =============================================================================

class ArticleCreate(BaseModel):
    """Request model for creating a knowledge base article."""
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    category: str = Field(default="General")
    tags: list[str] = Field(default_factory=list)


class TaskCreate(BaseModel):
    """Request model for creating a project task."""
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(default="")
    status: str = Field(default="Not Started")
    priority: str = Field(default="Normal")
    due_date: Optional[str] = None
    assigned_to: Optional[str] = None


class TaskStatusUpdate(BaseModel):
    """Request model for updating task status."""
    status: str = Field(..., min_length=1)


class PowerBIPushRequest(BaseModel):
    """Request model for pushing data to Power BI."""
    dataset_id: str
    table_name: str
    rows: list[dict[str, Any]]
    workspace_id: Optional[str] = None


class WebhookRegister(BaseModel):
    """Request model for registering a Power Automate webhook."""
    name: str = Field(..., min_length=1, max_length=100)
    url: str = Field(..., min_length=1)


class FlowTrigger(BaseModel):
    """Request model for triggering a Power Automate flow."""
    name: str
    payload: dict[str, Any] = Field(default_factory=dict)


class FileUpload(BaseModel):
    """Request model for file upload."""
    folder_path: str
    filename: str
    content_base64: str  # Base64-encoded file content


# =============================================================================
# Helper Functions
# =============================================================================

def get_graph_client() -> GraphClient:
    """Get or create Graph client instance."""
    global _graph_client
    if not GRAPH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Microsoft Graph not available. Install dependencies.")
    
    if _graph_client is None:
        try:
            _graph_client = GraphClient.from_env()
        except ValueError as e:
            raise HTTPException(status_code=503, detail=f"Graph client configuration error: {e}")
    return _graph_client


def get_powerautomate_client() -> PowerAutomateClient:
    """Get or create Power Automate client instance."""
    global _powerautomate_client
    if _powerautomate_client is None:
        _powerautomate_client = PowerAutomateClient()
    return _powerautomate_client


# =============================================================================
# Status Endpoint
# =============================================================================

@m365_router.get("/status")
async def m365_status():
    """Get Microsoft 365 integration status."""
    has_credentials = all([
        os.environ.get("M365_TENANT_ID"),
        os.environ.get("M365_CLIENT_ID"),
        os.environ.get("M365_CLIENT_SECRET")
    ])
    
    return {
        "available": GRAPH_AVAILABLE,
        "configured": has_credentials,
        "tenant_id": os.environ.get("M365_TENANT_ID", "")[:8] + "..." if has_credentials else None,
        "features": {
            "sharepoint": GRAPH_AVAILABLE and has_credentials,
            "onedrive": GRAPH_AVAILABLE and has_credentials,
            "power_bi": GRAPH_AVAILABLE and has_credentials,
            "power_automate": True  # Always available (webhook-based)
        }
    }


# =============================================================================
# SharePoint Sites
# =============================================================================

@m365_router.get("/sites/search")
async def search_sharepoint_sites(query: str = Query(..., min_length=1)):
    """
    Search for SharePoint sites.
    
    Args:
        query: Search query (e.g., "encyclopedia", "project")
    
    Returns:
        List of matching SharePoint sites
    """
    client = get_graph_client()
    try:
        sites = await client.search_sites(query)
        return {
            "sites": [
                {
                    "id": s.id,
                    "name": s.name,
                    "display_name": s.display_name,
                    "web_url": s.web_url
                }
                for s in sites
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search sites: {e}")


@m365_router.get("/sites/{site_id}/lists")
async def get_site_lists(site_id: str):
    """Get all lists in a SharePoint site."""
    client = get_graph_client()
    try:
        lists = await client.get_site_lists(site_id)
        return {
            "lists": [
                {
                    "id": lst.id,
                    "name": lst.name,
                    "display_name": lst.display_name,
                    "web_url": lst.web_url
                }
                for lst in lists
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get lists: {e}")


@m365_router.get("/sites/{site_id}/lists/{list_id}/items")
async def get_list_items(site_id: str, list_id: str):
    """Get items from a SharePoint list."""
    client = get_graph_client()
    try:
        items = await client.get_list_items(site_id, list_id)
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get list items: {e}")


@m365_router.post("/sites/{site_id}/lists/{list_id}/items")
async def create_list_item(site_id: str, list_id: str, fields: dict[str, Any] = Body(...)):
    """Create a new item in a SharePoint list."""
    client = get_graph_client()
    try:
        result = await client.create_list_item(site_id, list_id, fields)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create item: {e}")


# =============================================================================
# Encyclopedia (Knowledge Base)
# =============================================================================

@m365_router.get("/encyclopedia/articles")
async def get_encyclopedia_articles(
    site_id: str = Query(..., description="SharePoint site ID for Encyclopedia"),
    category: Optional[str] = None
):
    """
    Get knowledge base articles from Encyclopedia.
    
    Args:
        site_id: SharePoint site ID
        category: Optional category filter
    """
    client = get_graph_client()
    try:
        enc = EncyclopediaClient(client, site_id)
        articles = await enc.get_articles(category)
        return {"articles": articles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get articles: {e}")


@m365_router.post("/encyclopedia/articles")
async def create_encyclopedia_article(
    site_id: str = Query(..., description="SharePoint site ID"),
    article: ArticleCreate = Body(...)
):
    """Create a new knowledge base article."""
    client = get_graph_client()
    try:
        enc = EncyclopediaClient(client, site_id)
        result = await enc.create_article(
            title=article.title,
            content=article.content,
            category=article.category,
            tags=article.tags
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create article: {e}")


@m365_router.get("/encyclopedia/search")
async def search_encyclopedia(
    site_id: str = Query(..., description="SharePoint site ID"),
    query: str = Query(..., min_length=1)
):
    """Search knowledge base articles."""
    client = get_graph_client()
    try:
        enc = EncyclopediaClient(client, site_id)
        articles = await enc.search_articles(query)
        return {"articles": articles, "query": query}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")


# =============================================================================
# Project Management
# =============================================================================

@m365_router.get("/projects/tasks")
async def get_project_tasks(
    site_id: str = Query(..., description="SharePoint site ID"),
    status: Optional[str] = None
):
    """
    Get project tasks from SharePoint.
    
    Args:
        site_id: SharePoint site ID
        status: Optional status filter
    """
    client = get_graph_client()
    try:
        pm = ProjectManagementClient(client, site_id)
        tasks = await pm.get_tasks(status)
        return {"tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {e}")


@m365_router.post("/projects/tasks")
async def create_project_task(
    site_id: str = Query(..., description="SharePoint site ID"),
    task: TaskCreate = Body(...)
):
    """Create a new project task."""
    client = get_graph_client()
    try:
        pm = ProjectManagementClient(client, site_id)
        result = await pm.create_task(
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            due_date=task.due_date,
            assigned_to=task.assigned_to
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {e}")


@m365_router.patch("/projects/tasks/{task_id}/status")
async def update_task_status(
    task_id: str,
    site_id: str = Query(..., description="SharePoint site ID"),
    update: TaskStatusUpdate = Body(...)
):
    """Update task status."""
    client = get_graph_client()
    try:
        pm = ProjectManagementClient(client, site_id)
        result = await pm.update_task_status(task_id, update.status)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task: {e}")


# =============================================================================
# Document Library / Files
# =============================================================================

@m365_router.get("/files/list")
async def list_files(
    site_id: str = Query(..., description="SharePoint site ID"),
    folder_path: str = Query(default="root")
):
    """List files in a SharePoint document library."""
    client = get_graph_client()
    try:
        items = await client.list_drive_items(site_id, folder_path)
        return {
            "items": [
                {
                    "id": item.id,
                    "name": item.name,
                    "path": item.path,
                    "size": item.size,
                    "is_folder": item.is_folder,
                    "modified": item.modified.isoformat() if item.modified else None,
                    "web_url": item.web_url
                }
                for item in items
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {e}")


@m365_router.post("/files/upload")
async def upload_file(
    site_id: str = Query(..., description="SharePoint site ID"),
    upload: FileUpload = Body(...)
):
    """Upload a file to SharePoint document library."""
    import base64
    client = get_graph_client()
    try:
        content = base64.b64decode(upload.content_base64)
        item = await client.upload_file(
            site_id,
            upload.folder_path,
            upload.filename,
            content
        )
        return {
            "id": item.id,
            "name": item.name,
            "web_url": item.web_url,
            "size": item.size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {e}")


# =============================================================================
# Power BI
# =============================================================================

@m365_router.get("/powerbi/datasets")
async def get_powerbi_datasets(workspace_id: Optional[str] = None):
    """Get Power BI datasets."""
    client = get_graph_client()
    try:
        datasets = await client.get_powerbi_datasets(workspace_id)
        return {"datasets": datasets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get datasets: {e}")


@m365_router.post("/powerbi/push")
async def push_to_powerbi(request: PowerBIPushRequest):
    """
    Push data rows to a Power BI push dataset.
    
    This is useful for real-time dashboards showing QuickBooks data.
    """
    client = get_graph_client()
    try:
        await client.push_rows_to_dataset(
            dataset_id=request.dataset_id,
            table_name=request.table_name,
            rows=request.rows,
            workspace_id=request.workspace_id
        )
        return {
            "success": True,
            "rows_pushed": len(request.rows),
            "dataset_id": request.dataset_id,
            "table_name": request.table_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to push to Power BI: {e}")


@m365_router.delete("/powerbi/datasets/{dataset_id}/tables/{table_name}/rows")
async def clear_powerbi_table(
    dataset_id: str,
    table_name: str,
    workspace_id: Optional[str] = None
):
    """Clear all rows from a Power BI push dataset table."""
    client = get_graph_client()
    try:
        await client.clear_dataset_table(dataset_id, table_name, workspace_id)
        return {"success": True, "message": f"Cleared table {table_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear table: {e}")


# =============================================================================
# Power Automate
# =============================================================================

@m365_router.post("/powerautomate/webhooks")
async def register_webhook(webhook: WebhookRegister):
    """
    Register a Power Automate webhook URL.
    
    Get the URL from Power Automate when creating an HTTP trigger flow.
    """
    client = get_powerautomate_client()
    client.register_webhook(webhook.name, webhook.url)
    return {
        "success": True,
        "message": f"Webhook '{webhook.name}' registered"
    }


@m365_router.post("/powerautomate/trigger")
async def trigger_flow(trigger: FlowTrigger):
    """
    Trigger a Power Automate flow.
    
    The webhook must be registered first using POST /powerautomate/webhooks.
    """
    client = get_powerautomate_client()
    try:
        result = await client.trigger_flow(trigger.name, trigger.payload)
        return {
            "success": True,
            "flow_name": trigger.name,
            "response": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger flow: {e}")


@m365_router.get("/powerautomate/webhooks")
async def list_webhooks():
    """List registered Power Automate webhooks."""
    client = get_powerautomate_client()
    return {
        "webhooks": list(client._webhook_urls.keys())
    }
