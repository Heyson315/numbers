"""
Microsoft Graph API Client for M365 Integration

Provides access to SharePoint, OneDrive, Power BI, and Power Automate
for the numbers QuickBooks integration project.
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Optional imports with graceful fallback
try:
    from azure.identity import ClientSecretCredential
    AZURE_IDENTITY_AVAILABLE = True
except ImportError:
    AZURE_IDENTITY_AVAILABLE = False
    logger.warning("azure-identity not installed. Install with: pip install azure-identity")

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.warning("httpx not installed. Install with: pip install httpx")


@dataclass
class DriveItem:
    """Represents a file or folder in OneDrive/SharePoint."""
    id: str
    name: str
    path: str
    size: int
    is_folder: bool
    modified: Optional[datetime] = None
    web_url: Optional[str] = None
    download_url: Optional[str] = None


@dataclass
class SharePointSite:
    """Represents a SharePoint site."""
    id: str
    name: str
    display_name: str
    web_url: str


@dataclass
class SharePointList:
    """Represents a SharePoint list."""
    id: str
    name: str
    display_name: str
    web_url: Optional[str] = None


class GraphClient:
    """
    Microsoft Graph API client for M365 services.
    
    Supports:
    - SharePoint sites, lists, and document libraries
    - OneDrive file operations
    - Power BI dataset push (via REST API)
    - Power Automate webhook triggers
    """
    
    GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
    POWER_BI_API_URL = "https://api.powerbi.com/v1.0/myorg"
    
    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        scopes: Optional[list[str]] = None
    ):
        """
        Initialize Graph client with service principal credentials.
        
        Args:
            tenant_id: Azure AD tenant ID
            client_id: App registration client ID
            client_secret: App registration client secret
            scopes: Optional list of scopes (defaults to .default)
        """
        if not AZURE_IDENTITY_AVAILABLE:
            raise ImportError("azure-identity required. Install: pip install azure-identity")
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx required. Install: pip install httpx")
            
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.scopes = scopes or ["https://graph.microsoft.com/.default"]
        
        self._credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        self._token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
        
    @classmethod
    def from_env(cls) -> "GraphClient":
        """
        Create GraphClient from environment variables.
        
        Required env vars:
            M365_TENANT_ID: Azure AD tenant ID
            M365_CLIENT_ID: App registration client ID
            M365_CLIENT_SECRET: App registration client secret
        """
        tenant_id = os.environ.get("M365_TENANT_ID", "")
        client_id = os.environ.get("M365_CLIENT_ID", "")
        client_secret = os.environ.get("M365_CLIENT_SECRET", "")
        
        if not all([tenant_id, client_id, client_secret]):
            raise ValueError(
                "Missing M365 credentials. Set M365_TENANT_ID, M365_CLIENT_ID, M365_CLIENT_SECRET"
            )
            
        return cls(tenant_id, client_id, client_secret)
    
    def _get_token(self) -> str:
        """Get or refresh access token."""
        if self._token and self._token_expires and datetime.now() < self._token_expires:
            return self._token
            
        token = self._credential.get_token(*self.scopes)
        self._token = token.token
        self._token_expires = datetime.fromtimestamp(token.expires_on)
        return self._token
    
    def _headers(self) -> dict[str, str]:
        """Get HTTP headers with bearer token."""
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json"
        }
    
    async def _request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> dict[str, Any]:
        """Make authenticated request to Graph API."""
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                headers=self._headers(),
                **kwargs
            )
            response.raise_for_status()
            return response.json() if response.content else {}
    
    # =========================================================================
    # SharePoint Operations
    # =========================================================================
    
    async def get_site(self, site_path: str) -> SharePointSite:
        """
        Get SharePoint site by path.
        
        Args:
            site_path: Site path like "contoso.sharepoint.com:/sites/Encyclopedia"
        
        Returns:
            SharePointSite object
        """
        url = f"{self.GRAPH_BASE_URL}/sites/{site_path}"
        data = await self._request("GET", url)
        return SharePointSite(
            id=data["id"],
            name=data["name"],
            display_name=data["displayName"],
            web_url=data["webUrl"]
        )
    
    async def search_sites(self, query: str) -> list[SharePointSite]:
        """
        Search for SharePoint sites.
        
        Args:
            query: Search query (e.g., "encyclopedia")
        
        Returns:
            List of matching SharePointSite objects
        """
        url = f"{self.GRAPH_BASE_URL}/sites?search={query}"
        data = await self._request("GET", url)
        return [
            SharePointSite(
                id=site["id"],
                name=site["name"],
                display_name=site["displayName"],
                web_url=site["webUrl"]
            )
            for site in data.get("value", [])
        ]
    
    async def get_site_lists(self, site_id: str) -> list[SharePointList]:
        """
        Get all lists in a SharePoint site.
        
        Args:
            site_id: SharePoint site ID
        
        Returns:
            List of SharePointList objects
        """
        url = f"{self.GRAPH_BASE_URL}/sites/{site_id}/lists"
        data = await self._request("GET", url)
        return [
            SharePointList(
                id=lst["id"],
                name=lst["name"],
                display_name=lst["displayName"],
                web_url=lst.get("webUrl")
            )
            for lst in data.get("value", [])
        ]
    
    async def get_list_items(
        self,
        site_id: str,
        list_id: str,
        expand_fields: bool = True
    ) -> list[dict[str, Any]]:
        """
        Get items from a SharePoint list.
        
        Args:
            site_id: SharePoint site ID
            list_id: List ID
            expand_fields: Whether to expand field values
        
        Returns:
            List of item dictionaries
        """
        url = f"{self.GRAPH_BASE_URL}/sites/{site_id}/lists/{list_id}/items"
        if expand_fields:
            url += "?expand=fields"
        data = await self._request("GET", url)
        return data.get("value", [])
    
    async def create_list_item(
        self,
        site_id: str,
        list_id: str,
        fields: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Create a new item in a SharePoint list.
        
        Args:
            site_id: SharePoint site ID
            list_id: List ID
            fields: Dictionary of field values
        
        Returns:
            Created item data
        """
        url = f"{self.GRAPH_BASE_URL}/sites/{site_id}/lists/{list_id}/items"
        return await self._request("POST", url, json={"fields": fields})
    
    async def update_list_item(
        self,
        site_id: str,
        list_id: str,
        item_id: str,
        fields: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an item in a SharePoint list."""
        url = f"{self.GRAPH_BASE_URL}/sites/{site_id}/lists/{list_id}/items/{item_id}/fields"
        return await self._request("PATCH", url, json=fields)
    
    # =========================================================================
    # Document Library / OneDrive Operations
    # =========================================================================
    
    async def list_drive_items(
        self,
        site_id: str,
        folder_path: str = "root"
    ) -> list[DriveItem]:
        """
        List files in a SharePoint document library.
        
        Args:
            site_id: SharePoint site ID
            folder_path: Folder path or "root" for root folder
        
        Returns:
            List of DriveItem objects
        """
        if folder_path == "root":
            url = f"{self.GRAPH_BASE_URL}/sites/{site_id}/drive/root/children"
        else:
            url = f"{self.GRAPH_BASE_URL}/sites/{site_id}/drive/root:/{folder_path}:/children"
        
        data = await self._request("GET", url)
        items = []
        for item in data.get("value", []):
            items.append(DriveItem(
                id=item["id"],
                name=item["name"],
                path=item.get("parentReference", {}).get("path", ""),
                size=item.get("size", 0),
                is_folder="folder" in item,
                modified=datetime.fromisoformat(item["lastModifiedDateTime"].replace("Z", "+00:00")) if "lastModifiedDateTime" in item else None,
                web_url=item.get("webUrl"),
                download_url=item.get("@microsoft.graph.downloadUrl")
            ))
        return items
    
    async def upload_file(
        self,
        site_id: str,
        folder_path: str,
        filename: str,
        content: bytes
    ) -> DriveItem:
        """
        Upload a file to SharePoint document library.
        
        Args:
            site_id: SharePoint site ID
            folder_path: Destination folder path
            filename: Name for the uploaded file
            content: File content as bytes
        
        Returns:
            DriveItem for the uploaded file
        """
        url = f"{self.GRAPH_BASE_URL}/sites/{site_id}/drive/root:/{folder_path}/{filename}:/content"
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                url,
                headers={
                    "Authorization": f"Bearer {self._get_token()}",
                    "Content-Type": "application/octet-stream"
                },
                content=content
            )
            response.raise_for_status()
            item = response.json()
        
        return DriveItem(
            id=item["id"],
            name=item["name"],
            path=item.get("parentReference", {}).get("path", ""),
            size=item.get("size", 0),
            is_folder=False,
            web_url=item.get("webUrl")
        )
    
    async def download_file(self, site_id: str, item_id: str) -> bytes:
        """Download a file from SharePoint."""
        url = f"{self.GRAPH_BASE_URL}/sites/{site_id}/drive/items/{item_id}/content"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._headers(), follow_redirects=True)
            response.raise_for_status()
            return response.content
    
    # =========================================================================
    # Power BI Operations (Push Dataset API)
    # =========================================================================
    
    async def get_powerbi_datasets(self, workspace_id: Optional[str] = None) -> list[dict]:
        """
        Get Power BI datasets.
        
        Args:
            workspace_id: Optional workspace/group ID (uses 'My Workspace' if not provided)
        
        Returns:
            List of dataset dictionaries
        """
        if workspace_id:
            url = f"{self.POWER_BI_API_URL}/groups/{workspace_id}/datasets"
        else:
            url = f"{self.POWER_BI_API_URL}/datasets"
        
        return (await self._request("GET", url)).get("value", [])
    
    async def push_rows_to_dataset(
        self,
        dataset_id: str,
        table_name: str,
        rows: list[dict],
        workspace_id: Optional[str] = None
    ) -> None:
        """
        Push rows to a Power BI push dataset.
        
        Args:
            dataset_id: Power BI dataset ID
            table_name: Table name in the dataset
            rows: List of row dictionaries
            workspace_id: Optional workspace ID
        """
        if workspace_id:
            url = f"{self.POWER_BI_API_URL}/groups/{workspace_id}/datasets/{dataset_id}/tables/{table_name}/rows"
        else:
            url = f"{self.POWER_BI_API_URL}/datasets/{dataset_id}/tables/{table_name}/rows"
        
        await self._request("POST", url, json={"rows": rows})
        logger.info(f"Pushed {len(rows)} rows to Power BI dataset {dataset_id}/{table_name}")
    
    async def clear_dataset_table(
        self,
        dataset_id: str,
        table_name: str,
        workspace_id: Optional[str] = None
    ) -> None:
        """Clear all rows from a Power BI push dataset table."""
        if workspace_id:
            url = f"{self.POWER_BI_API_URL}/groups/{workspace_id}/datasets/{dataset_id}/tables/{table_name}/rows"
        else:
            url = f"{self.POWER_BI_API_URL}/datasets/{dataset_id}/tables/{table_name}/rows"
        
        await self._request("DELETE", url)
        logger.info(f"Cleared table {table_name} in dataset {dataset_id}")


class EncyclopediaClient:
    """
    Client for SharePoint Encyclopedia knowledge base.
    
    Manages knowledge base articles stored in SharePoint lists/pages.
    """
    
    def __init__(self, graph_client: GraphClient, site_id: str):
        """
        Initialize Encyclopedia client.
        
        Args:
            graph_client: Authenticated GraphClient instance
            site_id: SharePoint site ID for the Encyclopedia
        """
        self.graph = graph_client
        self.site_id = site_id
        self._articles_list_id: Optional[str] = None
    
    @classmethod
    async def from_env(cls, site_name: str = "Encyclopedia") -> "EncyclopediaClient":
        """
        Create EncyclopediaClient from environment.
        
        Args:
            site_name: Name of the SharePoint site (default: "Encyclopedia")
        """
        graph = GraphClient.from_env()
        sites = await graph.search_sites(site_name)
        if not sites:
            raise ValueError(f"SharePoint site '{site_name}' not found")
        return cls(graph, sites[0].id)
    
    async def _get_articles_list(self) -> str:
        """Get or find the Articles list ID."""
        if self._articles_list_id:
            return self._articles_list_id
        
        lists = await self.graph.get_site_lists(self.site_id)
        for lst in lists:
            if lst.name.lower() in ["articles", "knowledgebase", "kb", "pages"]:
                self._articles_list_id = lst.id
                return lst.id
        
        raise ValueError("No articles list found in Encyclopedia site")
    
    async def get_articles(self, category: Optional[str] = None) -> list[dict]:
        """
        Get knowledge base articles.
        
        Args:
            category: Optional category filter
        
        Returns:
            List of article dictionaries
        """
        list_id = await self._get_articles_list()
        items = await self.graph.get_list_items(self.site_id, list_id)
        
        articles = []
        for item in items:
            fields = item.get("fields", {})
            if category and fields.get("Category") != category:
                continue
            articles.append({
                "id": item["id"],
                "title": fields.get("Title", ""),
                "content": fields.get("Content", ""),
                "category": fields.get("Category", ""),
                "tags": fields.get("Tags", ""),
                "modified": item.get("lastModifiedDateTime")
            })
        return articles
    
    async def create_article(
        self,
        title: str,
        content: str,
        category: str = "General",
        tags: Optional[list[str]] = None
    ) -> dict:
        """
        Create a new knowledge base article.
        
        Args:
            title: Article title
            content: Article content (HTML or plain text)
            category: Article category
            tags: Optional list of tags
        
        Returns:
            Created article data
        """
        list_id = await self._get_articles_list()
        fields = {
            "Title": title,
            "Content": content,
            "Category": category,
            "Tags": ",".join(tags) if tags else ""
        }
        return await self.graph.create_list_item(self.site_id, list_id, fields)
    
    async def search_articles(self, query: str) -> list[dict]:
        """
        Search articles by title or content.
        
        Args:
            query: Search query
        
        Returns:
            Matching articles
        """
        articles = await self.get_articles()
        query_lower = query.lower()
        return [
            a for a in articles
            if query_lower in a["title"].lower() or query_lower in a["content"].lower()
        ]


class ProjectManagementClient:
    """
    Client for SharePoint Project Management integration.
    
    Manages project tasks, milestones, and status in SharePoint lists.
    """
    
    def __init__(self, graph_client: GraphClient, site_id: str):
        """
        Initialize Project Management client.
        
        Args:
            graph_client: Authenticated GraphClient instance
            site_id: SharePoint site ID
        """
        self.graph = graph_client
        self.site_id = site_id
        self._tasks_list_id: Optional[str] = None
        self._projects_list_id: Optional[str] = None
    
    async def _find_list(self, names: list[str]) -> str:
        """Find a list by possible names."""
        lists = await self.graph.get_site_lists(self.site_id)
        for lst in lists:
            if lst.name.lower() in [n.lower() for n in names]:
                return lst.id
        raise ValueError(f"No list found matching: {names}")
    
    async def get_tasks(self, status: Optional[str] = None) -> list[dict]:
        """
        Get project tasks.
        
        Args:
            status: Optional status filter (e.g., "In Progress", "Completed")
        
        Returns:
            List of task dictionaries
        """
        if not self._tasks_list_id:
            self._tasks_list_id = await self._find_list(["Tasks", "ProjectTasks", "To Do"])
        
        items = await self.graph.get_list_items(self.site_id, self._tasks_list_id)
        tasks = []
        for item in items:
            fields = item.get("fields", {})
            if status and fields.get("Status") != status:
                continue
            tasks.append({
                "id": item["id"],
                "title": fields.get("Title", ""),
                "status": fields.get("Status", "Not Started"),
                "priority": fields.get("Priority", "Normal"),
                "assigned_to": fields.get("AssignedTo", ""),
                "due_date": fields.get("DueDate"),
                "description": fields.get("Description", "")
            })
        return tasks
    
    async def create_task(
        self,
        title: str,
        description: str = "",
        status: str = "Not Started",
        priority: str = "Normal",
        due_date: Optional[str] = None,
        assigned_to: Optional[str] = None
    ) -> dict:
        """Create a new task in the project management list."""
        if not self._tasks_list_id:
            self._tasks_list_id = await self._find_list(["Tasks", "ProjectTasks", "To Do"])
        
        fields = {
            "Title": title,
            "Description": description,
            "Status": status,
            "Priority": priority
        }
        if due_date:
            fields["DueDate"] = due_date
        if assigned_to:
            fields["AssignedTo"] = assigned_to
        
        return await self.graph.create_list_item(self.site_id, self._tasks_list_id, fields)
    
    async def update_task_status(self, task_id: str, status: str) -> dict:
        """Update task status."""
        if not self._tasks_list_id:
            self._tasks_list_id = await self._find_list(["Tasks", "ProjectTasks", "To Do"])
        
        return await self.graph.update_list_item(
            self.site_id,
            self._tasks_list_id,
            task_id,
            {"Status": status}
        )


class PowerAutomateClient:
    """
    Client for triggering Power Automate flows via webhooks.
    """
    
    def __init__(self):
        """Initialize Power Automate client."""
        self._webhook_urls: dict[str, str] = {}
    
    def register_webhook(self, name: str, url: str) -> None:
        """
        Register a Power Automate webhook URL.
        
        Args:
            name: Friendly name for the webhook
            url: Power Automate HTTP trigger URL
        """
        self._webhook_urls[name] = url
        logger.info(f"Registered Power Automate webhook: {name}")
    
    async def trigger_flow(
        self,
        name: str,
        payload: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Trigger a Power Automate flow.
        
        Args:
            name: Registered webhook name
            payload: JSON payload to send to the flow
        
        Returns:
            Flow response data
        """
        if name not in self._webhook_urls:
            raise ValueError(f"Webhook '{name}' not registered. Call register_webhook first.")
        
        url = self._webhook_urls[name]
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json() if response.content else {"status": "triggered"}
    
    async def trigger_quickbooks_sync(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Trigger QuickBooks data sync flow.
        
        Args:
            data: QuickBooks data to sync (invoices, customers, etc.)
        """
        return await self.trigger_flow("quickbooks_sync", {
            "source": "numbers_app",
            "timestamp": datetime.now().isoformat(),
            "data": data
        })
    
    async def trigger_report_generation(
        self,
        report_type: str,
        parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Trigger report generation flow.
        
        Args:
            report_type: Type of report (e.g., "profit_loss", "invoice_summary")
            parameters: Report parameters (date range, filters, etc.)
        """
        return await self.trigger_flow("generate_report", {
            "report_type": report_type,
            "parameters": parameters,
            "requested_at": datetime.now().isoformat()
        })
