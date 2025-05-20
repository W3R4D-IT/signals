from fastapi import APIRouter
from sqlmodel import text

from api.deps import SessionDep

router = APIRouter()


@router.get("/HealthCheck")  # dependencies=[Depends(verify_api_key)]
async def health_check(session: SessionDep):
    try:
        # Attempt to execute a simple query to check database connectivity
        session.exec(text('SELECT 1'))
        return {"status": "healthy", "database": "connected"}
    except Exception as ex:
        return {"status": "unhealthy", "database": f"not connected, Error: {ex}"}
