# backend/routes/ask_router.py

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
import tempfile
import os
import time
import uuid
from typing import Optional

router = APIRouter(prefix="/ask", tags=["Query"])

ALLOWED_IMAGE_MIME = {"image/jpeg", "image/png"}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_QUERY_CHARS = 2000


@router.post("/text")
async def ask_text(
    query: str = Form(...),
    session_id: Optional[str] = Form(None) # ✅ NEW
):
    """Text-only farming query endpoint."""
    start = time.time()
    
    if not query or not query.strip():
        raise HTTPException(400, "Please enter a text query.")
    
    query = query.strip()
    if len(query) > MAX_QUERY_CHARS:
        raise HTTPException(413, f"Query too long. Max {MAX_QUERY_CHARS} chars.")
    
    from backend.agents.master_agent import route_query
    
    try:
        response = route_query(query=query, image_path=None, session_id=session_id)
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")
    
    return {
        "request_id": str(uuid.uuid4()),
        "status": "success",
        "elapsed_ms": int((time.time() - start) * 1000),
        "query": query,
        "analysis": str(response)
    }


@router.post("/image")
async def ask_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None) # ✅ NEW
):
    """Image-only crop analysis endpoint."""
    start = time.time()
    tmp_path = ""
    
    if file.content_type not in ALLOWED_IMAGE_MIME:
        raise HTTPException(415, "Only JPEG/PNG images allowed.")
    
    try:
        data = await file.read()
        
        if not data:
            raise HTTPException(400, "Empty image file.")
        
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "File too large (max 8MB).")
        
        ext = ".jpg" if file.content_type == "image/jpeg" else ".png"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        
        from backend.agents.master_agent import route_query
        response = route_query(query=None, image_path=tmp_path, session_id=session_id)
        
        background_tasks.add_task(os.remove, tmp_path)
        
        return {
            "request_id": str(uuid.uuid4()),
            "status": "success",
            "elapsed_ms": int((time.time() - start) * 1000),
            "image_uploaded": True,
            "analysis": str(response)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        if tmp_path and os.path.exists(tmp_path):
            background_tasks.add_task(os.remove, tmp_path)
        raise HTTPException(500, f"Error: {str(e)}")


@router.post("/chat")
async def ask_chat(
    background_tasks: BackgroundTasks,
    query: str = Form(...),
    file: UploadFile = File(None),
    session_id: Optional[str] = Form(None) # ✅ NEW
):
    """
    Multimodal endpoint: text + optional image.
    Combines both analyses intelligently.
    """
    start = time.time()
    query_clean = query.strip()
    
    if not query_clean:
        raise HTTPException(400, "Query cannot be empty")
    
    if len(query_clean) > MAX_QUERY_CHARS:
        raise HTTPException(413, f"Query too long. Max {MAX_QUERY_CHARS} chars.")
    
    from backend.agents.master_agent import route_query
    
    # Text only (no file uploaded)
    if not file or not file.filename:
        try:
            response = route_query(query=query_clean, image_path=None, session_id=session_id)
        except Exception as e:
            raise HTTPException(500, f"Error: {str(e)}")
        
        return {
            "request_id": str(uuid.uuid4()),
            "status": "success",
            "elapsed_ms": int((time.time() - start) * 1000),
            "mode": "text_only",
            "query": query_clean,
            "analysis": str(response)
        }
    
    # Multimodal (text + image)
    if file.content_type not in ALLOWED_IMAGE_MIME:
        raise HTTPException(415, "Only JPEG/PNG images allowed.")
    
    tmp_path = ""
    
    try:
        data = await file.read()
        
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "File too large (max 8MB).")
        
        ext = ".jpg" if file.content_type == "image/jpeg" else ".png"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        
        response = route_query(query=query_clean, image_path=tmp_path, session_id=session_id)
        
        background_tasks.add_task(os.remove, tmp_path)
        
        return {
            "request_id": str(uuid.uuid4()),
            "status": "success",
            "elapsed_ms": int((time.time() - start) * 1000),
            "mode": "multimodal",
            "query": query_clean,
            "image_uploaded": True,
            "analysis": str(response)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        if tmp_path and os.path.exists(tmp_path):
            background_tasks.add_task(os.remove, tmp_path)
        raise HTTPException(500, f"Error: {str(e)}")
