# 🚀 XeonStorage REST API Documentation (v2.0)

> **Language Selection / Pilihan Bahasa:**  
> 🇺🇸 [English Documentation](#-english-documentation) | 🇮🇩 [Dokumentasi Bahasa Indonesia](#-dokumentasi-bahasa-indonesia)

---

# 🇺🇸 English Documentation

## 📌 How to Obtain an API Key (Sign In Required)
> [!IMPORTANT]
> **Authentication Required:** To obtain an API Key, you **must register an account and sign in** to the XeonStorage platform, then navigate to your **User Console / Dashboard** (`/dashboard`).
> Under the *Manage API Keys* section, you can generate and revoke multiple API Keys at any time for Telegram bots, scripts, or backend web integrations.

---

## 🔐 1. Authentication

All requests to `/api/v1/*` endpoints must include an `Authorization` HTTP header with the `Bearer` scheme:

```http
Authorization: Bearer XST_your_api_key_here
```

If the API Key is missing, invalid, or revoked, the server will return `401 Unauthorized`.

---

## 📡 2. Endpoints Overview

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/v1/files` | Upload a new file (Max **40 MB**) | ✅ Yes |
| `GET` | `/api/v1/files/{file_id}` | Retrieve file metadata JSON | ✅ Yes |
| `DELETE` | `/api/v1/files/{file_id}` | Delete a file permanently | ✅ Yes |
| `GET` | `/api/v1/me/files` | List all files owned by your account | ✅ Yes |
| `GET` | `/f/{file_id}.{ext}` | **Direct Raw File URL (Hotlink & Stream)** | ❌ Public |
| `GET` | `/v/{file_id}` | **Web Gallery Viewer Page** | ❌ Public |

---

## 📥 3. Endpoint Reference

### A. Upload File (`POST /api/v1/files`)
Uploads a binary media file (Image, MP4/MOV Video, Audio, Document) to cloud storage with local edge caching.

- **Headers:** `Authorization: Bearer <API_KEY>`
- **Body:** `multipart/form-data`
  - `file`: Binary file stream
- **Size Limit:** Maximum **40 MB**

#### cURL Example:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/files \
  -H "Authorization: Bearer XST_your_api_key" \
  -F "file=@sample_video.mp4"
```

#### Success Response (`200 OK`):
```json
{
  "success": true,
  "data": {
    "id": "BUacSvpA4g",
    "user_id": "e70c00d9-d040-4c8e-9d29-90fbd18d5a47",
    "original_name": "sample_video.mp4",
    "extension": "mp4",
    "mime_type": "video/mp4",
    "size": 3224955,
    "storage_provider": "telegram",
    "storage_key": "29:BQACAgUAAyEGAAMBCX_QuwAD...",
    "created_at": "2026-08-26T07:40:35.266898+00:00",
    "url": "http://127.0.0.1:8000/f/BUacSvpA4g.mp4"
  }
}
```

---

### B. Get File Metadata (`GET /api/v1/files/{file_id}`)
Retrieve detailed technical metadata for any uploaded file.

#### cURL Example:
```bash
curl -X GET http://127.0.0.1:8000/api/v1/files/BUacSvpA4g \
  -H "Authorization: Bearer XST_your_api_key"
```

---

### C. List Account Files (`GET /api/v1/me/files`)
Retrieve all files belonging to the authenticated API Key account.

#### cURL Example:
```bash
curl -X GET http://127.0.0.1:8000/api/v1/me/files \
  -H "Authorization: Bearer XST_your_api_key"
```

---

### D. Delete File (`DELETE /api/v1/files/{file_id}`)
Deletes the file from the database, disk cache, and Telegram cloud storage.

#### cURL Example:
```bash
curl -X DELETE http://127.0.0.1:8000/api/v1/files/BUacSvpA4g \
  -H "Authorization: Bearer XST_your_api_key"
```

---

### E. Public URLs (No Login Required)
- **Direct Media URL (Hotlink / Video Stream with HTTP 206 Support):**
  ```http
  GET http://127.0.0.1:8000/f/{file_id}.{ext}
  ```
- **Web Gallery Viewer Page:**
  ```http
  GET http://127.0.0.1:8000/v/{file_id}
  ```

---

## 💻 4. Code Integration Examples

### Python (requests)
```python
import requests

API_KEY = "XST_your_api_key_here"
BASE_URL = "http://127.0.0.1:8000"
headers = {"Authorization": f"Bearer {API_KEY}"}

# 1. Upload Video or Image
with open("video.mp4", "rb") as f:
    r = requests.post(f"{BASE_URL}/api/v1/files", headers=headers, files={"file": f})
    data = r.json()
    print("Direct URL:", data["data"]["url"])
    file_id = data["data"]["id"]

# 2. Get Metadata
info = requests.get(f"{BASE_URL}/api/v1/files/{file_id}", headers=headers).json()
print("File Metadata:", info)
```

### Node.js / JavaScript (axios & form-data)
```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const API_KEY = 'XST_your_api_key_here';
const BASE_URL = 'http://127.0.0.1:8000';

async function upload() {
  const form = new FormData();
  form.append('file', fs.createReadStream('photo.jpg'));

  const response = await axios.post(`${BASE_URL}/api/v1/files`, form, {
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      ...form.getHeaders()
    }
  });

  console.log('Upload Result:', response.data);
}

upload();
```

---

## 🛑 5. HTTP Response & Error Codes

| Status Code | Meaning | Description |
| :--- | :--- | :--- |
| `200 OK` | Success | Request processed successfully |
| `206 Partial Content` | Streaming Media | Video Range seeking chunk streaming |
| `304 Not Modified` | Cache Hit | ETag matched, 0 bandwidth consumed |
| `401 Unauthorized` | Auth Failed | Invalid, revoked, or missing API Key |
| `404 Not Found` | Not Found | Requested file or endpoint does not exist |
| `413 Payload Too Large`| Size Exceeded | File exceeds maximum limit of 40 MB |
| `500 Internal Error` | Server Error | Failed to communicate with cloud backend |

---
---

# 🇮🇩 Dokumentasi Bahasa Indonesia

## 📌 Cara Mendapatkan API Key (Wajib Login)
> [!IMPORTANT]
> **Autentikasi Wajib:** Untuk mendapatkan token API Key, Anda **wajib mendaftarkan akun dan masuk (login)** ke platform XeonStorage, kemudian buka halaman **Konsol Pengguna / Dashboard** (`/dashboard`).
> Di bagian *Kelola API Key*, Anda dapat membuat token API Key baru kapan saja untuk keperluan integrasi bot, script, maupun backend.

---

## 🔐 1. Autentikasi

Setiap request ke endpoint `/api/v1/*` harus menyertakan header `Authorization` dengan skema `Bearer`:

```http
Authorization: Bearer XST_your_api_key_here
```

Jika API Key tidak disertakan atau salah, server mengembalikan status `401 Unauthorized`.

---

## 📡 2. Ringkasan Endpoint

| Method | Endpoint | Keterangan | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/v1/files` | Unggah berkas baru (Maks **40 MB**) | ✅ Ya |
| `GET` | `/api/v1/files/{file_id}` | Ambil metadata berkas | ✅ Ya |
| `DELETE` | `/api/v1/files/{file_id}` | Hapus berkas | ✅ Ya |
| `GET` | `/api/v1/me/files` | Daftar semua berkas milik akun Anda | ✅ Ya |
| `GET` | `/f/{file_id}.{ext}` | **Tautan Langsung (Hotlink & Stream Media)** | ❌ Publik |
| `GET` | `/v/{file_id}` | **Halaman Galeri Web Viewer** | ❌ Publik |

---

## 📥 3. Detail Endpoint & Contoh Request

### A. Upload Berkas (`POST /api/v1/files`)
Mengunggah berkas ke cloud Telegram dengan akselerasi cache lokal server.

- **Header:** `Authorization: Bearer <API_KEY>`
- **Body:** `multipart/form-data`
  - `file`: Berkas biner (Gambar, Video MP4/MOV, Audio, Dokumen)
- **Batas Ukuran:** Maksimum **40 MB**

#### Contoh cURL:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/files \
  -H "Authorization: Bearer XST_your_api_key" \
  -F "file=@sample_video.mp4"
```

#### Contoh Respon (200 OK):
```json
{
  "success": true,
  "data": {
    "id": "BUacSvpA4g",
    "user_id": "e70c00d9-d040-4c8e-9d29-90fbd18d5a47",
    "original_name": "sample_video.mp4",
    "extension": "mp4",
    "mime_type": "video/mp4",
    "size": 3224955,
    "storage_provider": "telegram",
    "storage_key": "29:BQACAgUAAyEGAAMBCX_QuwAD...",
    "created_at": "2026-08-26T07:40:35.266898+00:00",
    "url": "http://127.0.0.1:8000/f/BUacSvpA4g.mp4"
  }
}
```

---

### B. Ambil Metadata Berkas (`GET /api/v1/files/{file_id}`)
Mengambil informasi lengkap berkas yang tersimpan.

#### Contoh cURL:
```bash
curl -X GET http://127.0.0.1:8000/api/v1/files/BUacSvpA4g \
  -H "Authorization: Bearer XST_your_api_key"
```

---

### C. Daftar Berkas Akun Saya (`GET /api/v1/me/files`)
Mengambil seluruh daftar riwayat berkas yang diunggah oleh akun pemilik API Key.

#### Contoh cURL:
```bash
curl -X GET http://127.0.0.1:8000/api/v1/me/files \
  -H "Authorization: Bearer XST_your_api_key"
```

---

### D. Hapus Berkas (`DELETE /api/v1/files/{file_id}`)
Menghapus berkas dari database, cache lokal, dan cloud Telegram.

#### Contoh cURL:
```bash
curl -X DELETE http://127.0.0.1:8000/api/v1/files/BUacSvpA4g \
  -H "Authorization: Bearer XST_your_api_key"
```

---

### E. Tautan Publik (Tanpa Login)
- **Direct Hotlink & Streaming Video (Dukungan HTTP 206 Range Seeking):**
  ```http
  GET http://127.0.0.1:8000/f/{file_id}.{ext}
  ```
- **Web Gallery Viewer Page:**
  ```http
  GET http://127.0.0.1:8000/v/{file_id}
  ```

---

## 🛑 4. Kode Status HTTP

| Status Code | Makna | Keterangan |
| :--- | :--- | :--- |
| `200 OK` | Sukses | Request berhasil diproses |
| `206 Partial Content` | Streaming Media | Mengalirkan bagian video (Range Seeking) |
| `304 Not Modified` | Cache Hit | Menggunakan cache browser (0 Bandwidth) |
| `401 Unauthorized` | Autentikasi Gagal | API Key tidak valid atau tidak disertakan |
| `404 Not Found` | Tidak Ditemukan | Berkas atau endpoint tidak ditemukan |
| `413 Payload Too Large`| Ukuran Terlalu Besar | Berkas melebihi batas 40 MB |
| `500 Internal Error` | Kesalahan Server | Gagal menghubungi Telegram / database |
