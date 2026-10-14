#!/usr/bin/env python3
"""Interactive or automated helper script for 'The Forgetting Test'.

Verifies that announcements created in PostgreSQL persist across
'docker compose down' and 'docker compose up -d' without volume removal.

Conditions enforced:
1. 'created_by' is explicitly null.
2. The announcement ID is dynamically retrieved from the creation response.
3. No docker volumes are removed.
"""

import json
import sys
import time
import urllib.error
import urllib.request

BASE_URL = "http://localhost:8000"


def send_request(method: str, path: str, payload: dict = None) -> tuple:
    """Dispatches HTTP request using standard library urllib."""
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = body
        return e.code, parsed
    except Exception as e:
        return 0, str(e)


def wait_for_service(max_retries: int = 15, delay: float = 2.0) -> bool:
    """Waits until the FastAPI service is healthy and reachable."""
    print("⏳ Servisin hazır olması bekleniyor (GET /api/health)...")
    for attempt in range(1, max_retries + 1):
        status, body = send_request("GET", "/api/health")
        if status == 200:
            print(f"✅ Servis hazır! (Deneme {attempt})")
            return True
        time.sleep(delay)
    return False


def step1_create():
    """Step 1: Create record with created_by=None and extract dynamic ID."""
    print("\n--- [AŞAMA 1] Kayıt Oluşturma ---")
    payload = {
        "title": "The Forgetting Test Duyurusu",
        "content": "PostgreSQL kalıcılık ve volume testi için oluşturulmuş duyuru metni.",
        "created_by": None,  # Condition 1: created_by is null
    }

    status, resp = send_request("POST", "/api/announcements", payload)
    if status != 201 or resp.get("status") != "success":
        print(f"❌ Duyuru oluşturulamadı! Status: {status}, Response: {resp}")
        sys.exit(1)

    # Condition 2: Dynamically retrieve real ID from response
    announcement_id = resp["data"]["id"]
    print(f"✅ Duyuru başarıyla oluşturuldu!")
    print(f"   Dinamik Atanan ID : {announcement_id}")
    print(f"   Başlık            : {resp['data']['title']}")
    print(f"   created_by        : {resp['data']['created_by']}")

    return announcement_id


def step2_verify(announcement_id: int):
    """Step 2: Verify record persists after restart."""
    print(f"\n--- [AŞAMA 2] Kayıt Doğrulama (ID: {announcement_id}) ---")
    status, resp = send_request("GET", f"/api/announcements/{announcement_id}")

    if status != 200 or resp.get("status") != "success":
        print(f"❌ Duyuru bulunamadı! Status: {status}, Response: {resp}")
        print("💥 The Forgetting Test BAŞARISIZ: Kayıt yeniden başlatma sonrası kayboldu!")
        sys.exit(1)

    record = resp.get("data", {})
    print(f"✅ Kayıt başarıyla bulundu!")
    print(f"   ID        : {record.get('id')}")
    print(f"   Başlık    : {record.get('title')}")
    print(f"   İçerik    : {record.get('content')}")
    print(f"   created_by: {record.get('created_by')}")

    if record.get("id") == announcement_id and record.get("created_by") is None:
        print("\n🎉 TEBRİKLER! THE FORGETTING TEST BAŞARIYLA TAMAMLANDI!")
        print("   PostgreSQL 'postgres_data' volume'ü üzerinden veriler başarıyla kalıcı olarak saklandı.")
    else:
        print("⚠️ Kayıt içeriğinde uyuşmazlık tespit edildi.")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        if len(sys.argv) < 3:
            print("Kullanım: python verify_forgetting_test.py verify <ID>")
            sys.exit(1)
        target_id = int(sys.argv[2])
        if not wait_for_service():
            print("❌ Servise ulaşılamadı!")
            sys.exit(1)
        step2_verify(target_id)
        return

    print("==================================================")
    print("   THE FORGETTING TEST DOĞRULAMA ARACI")
    print("==================================================")

    if not wait_for_service():
        print("❌ Servise ulaşılamadı! Lütfen önce 'docker compose up -d --build' çalıştırın.")
        sys.exit(1)

    created_id = step1_create()

    print("\n--------------------------------------------------")
    print(f"Şimdi terminalinizde şu komutları sırasıyla çalıştırın:")
    print("  1) docker compose down")
    print("  2) docker compose up -d")
    print(f"  3) python scripts/verify_forgetting_test.py verify {created_id}")
    print("--------------------------------------------------")


if __name__ == "__main__":
    main()
