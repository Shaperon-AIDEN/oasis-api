from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import sqlite3
import pandas as pd
import os

app = FastAPI(title="OASis DB Peptide Lookup API", version="1.0.0")

# Read DB path from environment variable, default to local relative path
OASIS_DB_PATH = os.environ.get("OASIS_DB_PATH", "data/OASis_9mers_v1.db")

class PeptideRequest(BaseModel):
    peptides: List[str]
    chain_type: str = None  # "Heavy" or "Light", optional (matches humanness.py)

class PeptideResponse(BaseModel):
    num_total_oas_subjects: int
    hits: List[Dict[str, Any]]

@app.on_event("startup")
def startup_event():
    if not os.path.exists(OASIS_DB_PATH):
        raise FileNotFoundError(f"Database not found at {OASIS_DB_PATH}. Please ensure the volume is mounted correctly.")

@app.post("/api/peptides/", response_model=PeptideResponse)
def check_peptides(request: PeptideRequest):
    
    if not request.peptides:
        return {"num_total_oas_subjects": 0, "hits": []}
    
    # 1. Get total number of subjects based on chain type filter (matches logic in humanness.py)
    filter_chain_statement = ""
    chain_filter = request.chain_type  # Accept chain_type (sent by humanness.py)
    if chain_filter:
        if chain_filter not in ['Heavy', 'Light']:
            raise HTTPException(status_code=400, detail="chain_type must be 'Heavy' or 'Light'")
        filter_chain_statement = f"AND Complete{chain_filter}Seqs >= 10000"
        count_query = f"SELECT COUNT(*) FROM subjects WHERE Complete{chain_filter}Seqs >= 10000"
    else:
        count_query = "SELECT COUNT(*) FROM subjects"
        
    try:
        with sqlite3.connect(OASIS_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(count_query)
            num_total_oas_subjects = int(cursor.fetchone()[0])
            
            # 2. Get peptide hits
            peptides_tuple = tuple(request.peptides)
            placeholders = ",".join("?" * len(peptides_tuple))
            statement = (
                f"SELECT peptides.* FROM peptides "
                f"LEFT JOIN subjects ON peptides.subject=subjects.id "
                f"WHERE peptide IN ({placeholders}) AND subjects.StudyPath <> 'Corcoran_2016' "
                f"{filter_chain_statement}"
            )
            
            # Using pandas for fast data loading and dict serialization
            hits_df = pd.read_sql_query(statement, params=peptides_tuple, con=conn)
            hits = hits_df.to_dict(orient='records')
            
            return {
                "num_total_oas_subjects": num_total_oas_subjects,
                "hits": hits
            }
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"ERROR processing peptides: {error_msg}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    db_size = os.path.getsize(OASIS_DB_PATH) if os.path.exists(OASIS_DB_PATH) else 0
    return {"status": "ok", "db_path": OASIS_DB_PATH, "db_exists": os.path.exists(OASIS_DB_PATH), "db_size_bytes": db_size}
