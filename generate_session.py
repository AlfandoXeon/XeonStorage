import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

# Muat variabel dari .env
load_dotenv()

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")

if not API_ID or not API_HASH:
    print("❌ TELEGRAM_API_ID atau TELEGRAM_API_HASH tidak ditemukan di .env!")
    print("Pastikan Anda sudah mengisi kedua nilai tersebut di file .env")
    exit(1)

async def main():
    print("==================================================")
    print("🔑 XeonStorage - Telegram MTProto Session Generator")
    print("==================================================")
    print("Silakan masukkan nomor HP Telegram Anda (beserta kode negara, contoh: +628123456789)")
    
    # Gunakan StringSession kosong untuk membuat sesi baru yang nantinya bisa di-export
    client = TelegramClient(StringSession(), int(API_ID), API_HASH)
    
    await client.start()
    
    print("\n✅ Berhasil Login!")
    session_string = client.session.save()
    
    print("\n==================================================")
    print("📜 SESSION STRING ANDA (SIMPAN DENGAN AMAN!):")
    print("==================================================")
    print(session_string)
    print("==================================================")
    print("\n💡 Langkah selanjutnya:")
    print("Salin string di atas dan masukkan ke dalam file .env Anda seperti ini:")
    print("TELEGRAM_SESSION_STRING=" + session_string[:15] + "...\n")
    print("⚠️  PENTING: Jangan pernah membagikan Session String ini kepada siapapun!")

if __name__ == "__main__":
    asyncio.run(main())
