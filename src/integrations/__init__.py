from .quickbooks import QuickBooksAuth, QuickBooksClient
from .quickbooks_routes import qb_router
from .qb_storage import QBTokenStorage, get_qb_storage

# Microsoft 365 integrations (optional - requires azure-identity, httpx)
try:
    from .graph_client import (
        GraphClient,
        EncyclopediaClient,
        ProjectManagementClient,
        PowerAutomateClient,
        DriveItem,
        SharePointSite,
        SharePointList
    )
    from .m365_routes import m365_router
    M365_AVAILABLE = True
except ImportError:
    M365_AVAILABLE = False
    GraphClient = None
    EncyclopediaClient = None
    ProjectManagementClient = None
    PowerAutomateClient = None
    m365_router = None

__all__ = [
    # QuickBooks
    'QuickBooksAuth',
    'QuickBooksClient',
    'qb_router',
    'QBTokenStorage',
    'get_qb_storage',
    # Microsoft 365
    'GraphClient',
    'EncyclopediaClient',
    'ProjectManagementClient',
    'PowerAutomateClient',
    'm365_router',
    'M365_AVAILABLE'
]