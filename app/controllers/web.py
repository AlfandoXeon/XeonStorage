from fastapi import APIRouter, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.dependencies import get
from app.i18n.translations import get_translator
from app.config.settings import get_settings

router = APIRouter()

def user(request: Request):
    return request.session.get("user_id")

def is_ajax(request: Request) -> bool:
    return (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or "application/json" in request.headers.get("accept", "")
        or request.headers.get("content-type", "").startswith("application/json")
    )

def get_context(request: Request, extra: dict = None) -> dict:
    lang_code = request.session.get("lang", "en")
    t, current_lang = get_translator(lang_code)
    ctx = {
        "request": request,
        "user_id": user(request),
        "username": request.session.get("username"),
        "t": t,
        "current_lang": current_lang,
        "max_upload_size_mb": get_settings().max_upload_size_mb
    }
    if extra:
        ctx.update(extra)
    return ctx

@router.get("/lang/{lang_code}")
def change_language(request: Request, lang_code: str):
    if lang_code.lower() in ["id", "en"]:
        request.session["lang"] = lang_code.lower()
    referer = request.headers.get("referer", "/")
    return RedirectResponse(referer, 303)

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return get("templates").TemplateResponse(
        request,
        "index.html",
        get_context(request)
    )

@router.post("/upload")
def upload_ajax(request: Request, file: UploadFile = File(...)):
    """Upload endpoint: Requires user login"""
    uid = user(request)
    lang_code = request.session.get("lang", "id")

    if not uid:
        err_msg = (
            "Please sign in or create an account to upload files."
            if lang_code == "en"
            else "Silakan masuk atau buat akun terlebih dahulu untuk mengunggah berkas."
        )
        return JSONResponse({
            "success": False,
            "error": err_msg,
            "require_auth": True
        })

    max_mb = get_settings().max_upload_size_mb
    max_bytes = max_mb * 1024 * 1024
    if file.size and file.size > max_bytes:
        err_msg = (
            f"File size exceeds the {max_mb} MB limit."
            if lang_code == "en"
            else f"Ukuran berkas melebihi batas maksimum {max_mb} MB."
        )
        return JSONResponse({"success": False, "error": err_msg}, status_code=413)

    try:
        record = get("files").upload(file, uid)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    host = str(request.base_url).rstrip("/")
    ext = f".{record['extension']}" if record.get("extension") else ""
    direct_url = f"{host}/f/{record['id']}{ext}"
    gallery_url = f"{host}/v/{record['id']}"

    return JSONResponse({
        "success": True,
        "data": {
            "id": record["id"],
            "direct_url": direct_url,
            "gallery_url": gallery_url,
            "url": direct_url,
            "name": record["original_name"],
            "size": record["size"],
            "mime_type": record["mime_type"],
            "is_authenticated": True
        }
    })

@router.post("/web/upload")
def web_upload(request: Request, file: UploadFile = File(...)):
    uid = user(request)
    if not uid:
        return RedirectResponse("/?auth=login", 303)

    max_mb = get_settings().max_upload_size_mb
    max_bytes = max_mb * 1024 * 1024
    if file.size and file.size > max_bytes:
        return RedirectResponse("/dashboard?error=size_limit", 303)

    get("files").upload(file, uid)
    return RedirectResponse("/dashboard", 303)

@router.post("/web/files/delete/{file_id}")
def delete_file_web(request: Request, file_id: str):
    uid = user(request)
    if not uid:
        return RedirectResponse("/?auth=login", 303)
    get("files").delete(file_id, uid)
    return RedirectResponse("/dashboard", 303)

@router.get("/v/{file_id}", response_class=HTMLResponse)
@router.get("/view/{file_id}", response_class=HTMLResponse)
@router.get("/gallery/{file_id}", response_class=HTMLResponse)
def gallery_view(request: Request, file_id: str):
    """Public web gallery viewer for images, audio, video, or files (No login required to view)"""
    r = get("files").get(file_id)
    host = str(request.base_url).rstrip("/")

    if not r:
        return get("templates").TemplateResponse(
            request,
            "viewer.html",
            get_context(request, {
                "file_found": False,
                "file_id": file_id
            }),
            status_code=404
        )

    ext = r.get("extension") or ""
    ext_suffix = f".{ext}" if ext else ""
    direct_url = f"{host}/f/{r['id']}{ext_suffix}"
    gallery_url = f"{host}/v/{r['id']}"
    mime = (r.get("mime_type") or "").lower()
    ext_clean = ext.lower()

    is_image = mime.startswith("image/") or ext_clean in ["png", "jpg", "jpeg", "gif", "webp", "svg", "ico", "bmp", "avif"]
    is_video = mime.startswith("video/") or ext_clean in ["mp4", "webm", "mov", "mkv", "avi"]
    is_audio = mime.startswith("audio/") or ext_clean in ["mp3", "wav", "ogg", "m4a", "flac", "aac"]

    is_owner = bool(user(request) and user(request) == r.get("user_id"))

    return get("templates").TemplateResponse(
        request,
        "viewer.html",
        get_context(request, {
            "file_found": True,
            "file": r,
            "direct_url": direct_url,
            "gallery_url": gallery_url,
            "is_image": is_image,
            "is_video": is_video,
            "is_audio": is_audio,
            "is_owner": is_owner
        })
    )

@router.get("/login")
def login_redirect(request: Request):
    if user(request):
        return RedirectResponse("/dashboard", 303)
    return RedirectResponse("/?auth=login", 303)

@router.get("/register")
def register_redirect(request: Request):
    if user(request):
        return RedirectResponse("/dashboard", 303)
    return RedirectResponse("/?auth=register", 303)

@router.post("/login")
async def login(request: Request, login: str = Form(...), password: str = Form(...)):
    u = get("auth").login(login, password)
    if not u:
        lang_code = request.session.get("lang", "id")
        err_msg = (
            "Login failed. Check your username/email or password."
            if lang_code == "en"
            else "Login gagal. Periksa username/email atau kata sandi Anda."
        )
        if is_ajax(request):
            return JSONResponse({"success": False, "error": err_msg}, status_code=400)
        return RedirectResponse("/?auth=login&error=1", 303)

    request.session["user_id"] = u["id"]
    request.session["username"] = u["username"]

    if is_ajax(request):
        return JSONResponse({"success": True, "redirect": "/dashboard"})
    return RedirectResponse("/dashboard", 303)

@router.post("/register")
async def register(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    try:
        uid = get("auth").register(username, email, password)
        request.session["user_id"] = uid
        request.session["username"] = username

        if is_ajax(request):
            return JSONResponse({"success": True, "redirect": "/dashboard"})
        return RedirectResponse("/dashboard", 303)
    except ValueError as e:
        if is_ajax(request):
            return JSONResponse({"success": False, "error": str(e)}, status_code=400)
        return RedirectResponse("/?auth=register&error=1", 303)

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", 303)

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    uid = user(request)
    if not uid:
        return RedirectResponse("/?auth=login", 303)
    stats = get("files").stats(uid)
    files = get("files").list(uid)
    return get("templates").TemplateResponse(
        request,
        "dashboard.html",
        get_context(request, {
            "stats": stats,
            "files": files
        })
    )

@router.get("/api-keys", response_class=HTMLResponse)
@router.get("/keys", response_class=HTMLResponse)
def api_keys_page(request: Request):
    uid = user(request)
    if not uid:
        return RedirectResponse("/?auth=login", 303)
    keys = get("keys").list_for_user(uid)
    return get("templates").TemplateResponse(
        request,
        "keys.html",
        get_context(request, {
            "keys": keys,
            "new_key": request.session.pop("new_key", None)
        })
    )

@router.post("/web/key")
def create_key(request: Request, name: str = Form(...)):
    uid = user(request)
    if not uid:
        return RedirectResponse("/?auth=login", 303)
    raw = get("auth").create_api_key(uid, name)
    request.session["new_key"] = raw
    referer = request.headers.get("referer", "/api-keys")
    return RedirectResponse(referer if "api-keys" in referer or "keys" in referer else "/api-keys", 303)

@router.post("/web/key/revoke/{key_id}")
def revoke_key(request: Request, key_id: str):
    uid = user(request)
    if not uid:
        return RedirectResponse("/?auth=login", 303)
    get("keys").revoke(key_id, uid)
    referer = request.headers.get("referer", "/api-keys")
    return RedirectResponse(referer if "api-keys" in referer or "keys" in referer else "/api-keys", 303)

@router.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return get("templates").TemplateResponse(
        request,
        "about.html",
        get_context(request)
    )

@router.get("/docs-page", response_class=HTMLResponse)
def docs(request: Request):
    return get("templates").TemplateResponse(
        request,
        "docs.html",
        get_context(request)
    )

@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    uid = user(request)
    if not uid:
        return RedirectResponse("/?auth=login", 303)
    account_user = get("auth").users.by_id(uid)
    if not account_user:
        return RedirectResponse("/logout", 303)

    success_msg = request.session.pop("settings_success", None)
    error_msg = request.session.pop("settings_error", None)

    return get("templates").TemplateResponse(
        request,
        "settings.html",
        get_context(request, {
            "account_user": account_user,
            "success_msg": success_msg,
            "error_msg": error_msg
        })
    )

@router.post("/settings/password")
def change_password_post(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...)
):
    uid = user(request)
    if not uid:
        return RedirectResponse("/?auth=login", 303)

    lang_code = request.session.get("lang", "id")
    try:
        get("auth").change_password(uid, current_password, new_password, confirm_password)
        request.session["settings_success"] = (
            "Password updated successfully!"
            if lang_code == "en"
            else "Kata sandi akun Anda berhasil diperbarui!"
        )
    except ValueError as e:
        request.session["settings_error"] = str(e)

    return RedirectResponse("/settings", 303)

