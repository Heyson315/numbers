"""QuickBooks API Routes for FastAPI with Azure SQL persistent storage"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
import os

qb_router = APIRouter(prefix="/quickbooks", tags=["QuickBooks"])

# In-memory state storage (only for OAuth flow, not tokens)
qb_states = {}

# Legacy in-memory dict for backward compatibility with tests
qb_tokens = {}


def _get_storage():
    """Get QB token storage (lazy import to avoid circular deps)."""
    from src.integrations.qb_storage import get_qb_storage
    return get_qb_storage()


def _is_sandbox() -> bool:
    """Check if running in sandbox mode."""
    return os.getenv("QB_ENVIRONMENT", "sandbox").lower() == "sandbox"


@qb_router.get("/connect")
async def connect_quickbooks():
    """Start QuickBooks OAuth flow - redirects to Intuit login."""
    from src.integrations.quickbooks import QuickBooksAuth
    auth = QuickBooksAuth()
    url, state = auth.get_authorization_url()
    qb_states[state] = True
    return RedirectResponse(url)


@qb_router.get("/callback")
async def quickbooks_callback(code: str, state: str, realmId: str):
    """Handle OAuth callback from QuickBooks."""
    from src.integrations.quickbooks import QuickBooksAuth
    
    if state not in qb_states:
        raise HTTPException(status_code=400, detail="Invalid state")
    del qb_states[state]
    
    auth = QuickBooksAuth()
    tokens = await auth.exchange_code(code, realmId)
    
    # Save to persistent storage (Azure SQL)
    storage = _get_storage()
    storage.save_tokens({
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "realm_id": realmId,
        "token_type": tokens.get("token_type", "Bearer"),
    })
    
    # Also update legacy dict for backward compatibility
    qb_tokens["access_token"] = tokens["access_token"]
    qb_tokens["refresh_token"] = tokens["refresh_token"]
    qb_tokens["realm_id"] = realmId
    
    return {
        "message": "QuickBooks connected successfully!",
        "realm_id": realmId,
        "storage": "azure_sql" if storage.connection_string else "memory"
    }


@qb_router.get("/status")
async def quickbooks_status():
    """Check if QuickBooks is connected."""
    storage = _get_storage()
    tokens = storage.get_tokens()
    
    if tokens and "access_token" in tokens:
        return {
            "connected": True,
            "realm_id": tokens.get("realm_id"),
            "storage": "azure_sql" if storage.connection_string else "memory"
        }
    
    # Fallback to legacy dict
    if "access_token" in qb_tokens:
        return {"connected": True, "realm_id": qb_tokens.get("realm_id"), "storage": "memory"}
    
    return {"connected": False}


def _get_qb_client():
    """Get authenticated QuickBooks client."""
    from src.integrations.quickbooks import QuickBooksClient
    
    storage = _get_storage()
    tokens = storage.get_tokens()
    
    # Fallback to legacy dict
    if not tokens:
        tokens = qb_tokens
    
    if not tokens or "access_token" not in tokens:
        raise HTTPException(status_code=401, detail="QuickBooks not connected. Visit /quickbooks/connect first")
    
    return QuickBooksClient(
        tokens["access_token"],
        tokens["realm_id"],
        sandbox=_is_sandbox()
    )


@qb_router.get("/customers")
async def get_customers():
    """Get all customers from QuickBooks."""
    qb = _get_qb_client()
    customers = await qb.get_customers()
    return {"count": len(customers), "customers": customers}


@qb_router.get("/invoices")
async def get_invoices(start_date: str = None):
    """Get invoices from QuickBooks."""
    qb = _get_qb_client()
    invoices = await qb.get_invoices(start_date)
    return {"count": len(invoices), "invoices": invoices}


@qb_router.get("/expenses")
async def get_expenses(start_date: str = None):
    """Get expenses/purchases from QuickBooks."""
    qb = _get_qb_client()
    expenses = await qb.get_expenses(start_date)
    return {"count": len(expenses), "expenses": expenses}


@qb_router.get("/accounts")
async def get_accounts():
    """Get chart of accounts from QuickBooks."""
    qb = _get_qb_client()
    accounts = await qb.get_accounts()
    return {"count": len(accounts), "accounts": accounts}


@qb_router.get("/reports/profit-loss")
async def get_profit_loss(start_date: str, end_date: str):
    """Get Profit & Loss report."""
    qb = _get_qb_client()
    report = await qb.get_profit_loss(start_date, end_date)
    return report


@qb_router.get("/reports/balance-sheet")
async def get_balance_sheet(as_of_date: str):
    """Get Balance Sheet report."""
    qb = _get_qb_client()
    report = await qb.get_balance_sheet(as_of_date)
    return report


@qb_router.post("/refresh")
async def refresh_quickbooks_token():
    """Refresh QuickBooks access token."""
    from src.integrations.quickbooks import QuickBooksAuth
    
    storage = _get_storage()
    tokens = storage.get_tokens()
    
    # Fallback to legacy dict
    if not tokens:
        tokens = qb_tokens
    
    if not tokens or "refresh_token" not in tokens:
        raise HTTPException(status_code=401, detail="QuickBooks not connected")
    
    auth = QuickBooksAuth()
    try:
        new_tokens = await auth.refresh_token(tokens["refresh_token"])
        
        # Save updated tokens to persistent storage
        storage.save_tokens({
            "access_token": new_tokens["access_token"],
            "refresh_token": new_tokens.get("refresh_token", tokens["refresh_token"]),
            "realm_id": tokens.get("realm_id"),
            "token_type": new_tokens.get("token_type", "Bearer"),
        })
        
        # Update legacy dict
        qb_tokens["access_token"] = new_tokens["access_token"]
        qb_tokens["refresh_token"] = new_tokens.get("refresh_token", tokens["refresh_token"])
        
        return {"message": "Token refreshed successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token refresh failed: {str(e)}")


@qb_router.post("/disconnect")
async def disconnect_quickbooks():
    """Disconnect QuickBooks and clear tokens."""
    storage = _get_storage()
    storage.delete_tokens()
    
    # Clear legacy dicts
    qb_tokens.clear()
    qb_states.clear()
    
    return {"message": "QuickBooks disconnected successfully"}
