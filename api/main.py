"""
Fraud Detection API - FastAPI
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging

from database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HSBC Fraud Detection API",
    version="1.0.0",
    description="Real-time fraud detection alerts API"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class FraudAlert(BaseModel):
    transaction_id: str
    transaction_time: datetime
    amount: float
    merchant: str
    category: str
    cc_num: Optional[str] = None
    first: Optional[str] = None
    last: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    is_fraud: float
    detected_at: datetime

class Stats(BaseModel):
    total_alerts: int
    total_amount: float
    avg_amount: float
    by_category: dict
    by_state: dict

@app.on_event("startup")
async def startup():
    """Connect to Cassandra on startup"""
    db.connect()

@app.on_event("shutdown")
async def shutdown():
    """Close Cassandra connection"""
    db.close()

@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "HSBC Fraud Detection API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/fraud/alerts", response_model=List[FraudAlert])
async def get_fraud_alerts(
    limit: Optional[int] = Query(None, ge=1, le=100000),
    category: Optional[str] = None,
    state: Optional[str] = None
):
    """
    Get fraud alerts from Cassandra
    """
    try:
        # Build query
        query = """
            SELECT transaction_id, transaction_time, amount, merchant, 
                   category, cc_num, first, last, state, city, 
                   is_fraud, detected_at
            FROM fraud_alerts
        """
        
        # Note: Cassandra không support WHERE với non-primary key
        # Nên ta query hết rồi filter trong Python
        if limit:
            rows = db.session.execute(query + f" LIMIT {limit}")
        else:
            rows = db.session.execute(query)
        
        alerts = []
        for row in rows:
            # Filter by category/state if provided
            if category and row.category != category:
                continue
            if state and row.state != state:
                continue
            
            alert = FraudAlert(
                transaction_id=row.transaction_id,
                transaction_time=row.transaction_time,
                amount=row.amount,
                merchant=row.merchant,
                category=row.category,
                cc_num=row.cc_num,
                first=row.first,
                last=row.last,
                state=row.state,
                city=row.city,
                is_fraud=row.is_fraud,
                detected_at=row.detected_at
            )
            alerts.append(alert)
        
        logger.info(f"Returned {len(alerts)} fraud alerts")
        return alerts
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/fraud/stats", response_model=Stats)
async def get_fraud_stats():
    """
    Get fraud statistics
    """
    try:
        # Get all alerts
        query = "SELECT * FROM fraud_alerts"
        rows = list(db.session.execute(query))
        
        if not rows:
            return Stats(
                total_alerts=0,
                total_amount=0.0,
                avg_amount=0.0,
                by_category={},
                by_state={}
            )
        
        # Calculate stats
        total_alerts = len(rows)
        total_amount = sum(row.amount for row in rows)
        avg_amount = total_amount / total_alerts
        
        # By category
        by_category = {}
        for row in rows:
            by_category[row.category] = by_category.get(row.category, 0) + 1
        
        # By state
        by_state = {}
        for row in rows:
            if row.state:
                by_state[row.state] = by_state.get(row.state, 0) + 1
        
        return Stats(
            total_alerts=total_alerts,
            total_amount=round(total_amount, 2),
            avg_amount=round(avg_amount, 2),
            by_category=by_category,
            by_state=by_state
        )
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/fraud/count")
async def get_fraud_count():
    """Get total fraud alerts count"""
    try:
        query = "SELECT COUNT(*) FROM fraud_alerts"
        row = db.session.execute(query).one()
        return {"count": row.count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
