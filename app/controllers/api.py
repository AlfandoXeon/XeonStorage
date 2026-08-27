from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from app.dependencies import get

router=APIRouter(prefix="/api/v1",tags=["API"])

def api_user(request):
    h=request.headers.get("Authorization","")
    if not h.startswith("Bearer "): raise HTTPException(401,"Missing Bearer token")
    k=get("auth").authenticate_api_key(h[7:].strip())
    if not k: raise HTTPException(401,"Invalid API key")
    return k["user_id"]

from app.config.settings import get_settings

@router.post("/files")
def upload(request: Request, file: UploadFile = File(...)):
    max_mb = get_settings().max_upload_size_mb
    max_bytes = max_mb * 1024 * 1024
    if file.size and file.size > max_bytes:
        raise HTTPException(413, f"File size exceeds the {max_mb} MB limit.")
    uid = api_user(request)
    r = get("files").upload(file, uid)
    host = str(request.base_url).rstrip("/")
    ext = f".{r['extension']}" if r["extension"] else ""
    return {"success": True, "data": {**r, "url": f"{host}/f/{r['id']}{ext}"}}

@router.get("/files/{file_id}")
def info(file_id):
    r=get("files").get(file_id)
    if not r: raise HTTPException(404,"File not found")
    return {"success":True,"data":dict(r)}

@router.delete("/files/{file_id}")
def delete(file_id,request:Request):
    uid=api_user(request)
    if not get("files").delete(file_id,uid): raise HTTPException(404,"File not found")
    return {"success":True}

@router.get("/me/files")
def my_files(request:Request):
    return {"success":True,"data":[dict(x) for x in get("files").list(api_user(request))]}
