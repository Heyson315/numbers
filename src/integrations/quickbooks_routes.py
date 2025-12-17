"""QuickBooks API Routes for FastAPI"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

qb_router = APIRouter(prefix="/quickbooks", tags=["QuickBooks"])

# Temporary storage (use Redis/database in production)
qb_tokens = {}
qb_states = {}


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
    
    qb_tokens["access_token"] = tokens["access_token"]
    qb_tokens["refresh_token"] = tokens["refresh_token"]
    qb_tokens["realm_id"] = realmId
    
    return {
        "message": "QuickBooks connected successfully!",
        "realm_id": realmId
    }


@qb_router.get("/status")
async def quickbooks_status():
    """Check if QuickBooks is connected."""
    if "access_token" in qb_tokens:
        return {"connected": True, "realm_id": qb_tokens.get("realm_id")}
    return {"connected": False}


@qb_router.get("/customers")
async def get_customers():
    """Get all customers from QuickBooks."""
    from src.integrations.quickbooks import QuickBooksClient
    
    if "access_token" not in qb_tokens:
        raise HTTPException(status_code=401, detail="QuickBooks not connected. Visit /quickbooks/connect first")
    
    qb = QuickBooksClient(
        qb_tokens["access_token"],
        qb_tokens["realm_id"],
        sandbox=True
    )
    customers = await qb.get_customers()
    return {"count": len(customers), "customers": customers}


@qb_router.get("/invoices")
async def get_invoices(start_date: str = None):
    """Get invoices from QuickBooks."""
    from src.integrations.quickbooks import QuickBooksClient
    
    if "access_token" not in qb_tokens:
        raise HTTPException(status_code=401, detail="QuickBooks not connected")
    
    qb = QuickBooksClient(
        qb_tokens["access_token"],
        qb_tokens["realm_id"],
        sandbox=True
    )
    invoices = await qb.get_invoices(start_date)
    return {"count": len(invoices), "invoices": invoices}


@qb_router.get("/expenses")
async def get_expenses(start_date: str = None):
    """Get expenses/purchases from QuickBooks."""
    from src.integrations.quickbooks import QuickBooksClient
    
    if "access_token" not in qb_tokens:
        raise HTTPException(status_code=401, detail="QuickBooks not connected")
    
    qb = QuickBooksClient(
        qb_tokens["access_token"],
        qb_tokens["realm_id"],
        sandbox=True
    )
    expenses = await qb.get_expenses(start_date)
    return {"count": len(expenses), "expenses": expenses}


@qb_router.get("/accounts")
async def get_accounts():
    """Get chart of accounts from QuickBooks."""
    from src.integrations.quickbooks import QuickBooksClient
    
    if "access_token" not in qb_tokens:
        raise HTTPException(status_code=401, detail="QuickBooks not connected")
    
    qb = QuickBooksClient(
        qb_tokens["access_token"],
        qb_tokens["realm_id"],
        sandbox=True
    )
    accounts = await qb.get_accounts()
    return {"count": len(accounts), "accounts": accounts}


@qb_router.get("/reports/profit-loss")
async def get_profit_loss(start_date: str, end_date: str):
    """Get Profit & Loss report."""
    from src.integrations.quickbooks import QuickBooksClient
    
    if "access_token" not in qb_tokens:
        raise HTTPException(status_code=401, detail="QuickBooks not connected")
    
    qb = QuickBooksClient(
        qb_tokens["access_token"],
        qb_tokens["realm_id"],
        sandbox=True
    )
    report = await qb.get_profit_loss(start_date, end_date)
    return report


@qb_router.get("/reports/balance-sheet")
async def get_balance_sheet(as_of_date: str):
    """Get Balance Sheet report."""
    from src.integrations.quickbooks import QuickBooksClient
    
    if "access_token" not in qb_tokens:
        raise HTTPException(status_code=401, detail="QuickBooks not connected")
    
    qb = QuickBooksClient(
        qb_tokens["access_token"],
        qb_tokens["realm_id"],
        sandbox=True
    )
    report = await qb.get_balance_sheet(as_of_date)
    return report
