# İstanbul Üniversitesi Mezun Takip Sistemi
## Alumni Tracking System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-blue?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00?style=flat&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

Bu proje, **İstanbul Üniversitesi Web Programlama** dersi kapsamında geliştirilmekte olan **Mezun Takip Sistemi**'nin (*Alumni Tracking System*) ilk aşamasıdır.

Bu ilk aşamada; FastAPI tabanlı modern, özgün ve responsive bir açılış sayfası (Landing Page), kurumsal hakkında sayfası, Swagger OpenAPI dokümantasyonu, katmanlı mimari iskeleti ve temel test uç noktaları hayata geçirilmiştir.

---

## 📌 İçindekiler
1. [Proje Hakkında](#-proje-hakkında)
2. [Teknoloji Yığını](#-teknoloji-yığını)
3. [Katmanlı Mimari (Layered Architecture)](#-katmanlı-mimari-layered-architecture)
4. [Proje Dizin Yapısı](#-proje-dizin-yapısı)
5. [Uç Noktalar (Endpoints)](#-uç-noktalar-endpoints)
6. [Yerel Kurulum ve Çalıştırma](#-yerel-kurulum-ve-çalıştırma)
7. [Docker ve Docker Compose ile Çalıştırma](#-docker-ve-docker-compose-ile-çalıştırma)
8. [Gelecek Aşamalar (Roadmap)](#-gelecek-aşamalar-roadmap)

---

## 📖 Proje Hakkında

İstanbul Üniversitesi Mezun Takip Sistemi; mezunlar, halen eğitim gören öğrenciler ve üniversite yönetimi arasında sürdürülebilir bir bağ kurmayı amaçlar.

### Bu Aşamadaki Temel Özellikler
- **Özgün ve Modern Web Arayüzü:** İstanbul Üniversitesi kurumsal renklerine (Lacivert `#0f2744` & Altın Sarısı `#d97706`) uygun, mobil uyumlu ve temiz Jinja2 + CSS/JS arayüzü.
- **Açılış Sayfası (`/`):** Proje tanıtımı, temel modül kartları, canlı test konsolu ve hızlı bağlantılar.
- **Hakkında Sayfası (`/about`):** Ders ve proje kapsamı, katmanlı mimarinin detayları ve teknoloji tablosu.
- **Etkileşimli Swagger API Dokümantasyonu (`/docs`):** FastAPI'nin otomatik oluşturduğu OpenAPI arayüzü.
- **Alternatif Dokümantasyon (`/redoc`):** ReDoc formatında API spesifikasyonu.
- **Etkileşimli Test Paneli:** Ana sayfadan doğrudan uç noktaları test edebileceğiniz yerleşik konsol.

---

## 🛠 Teknoloji Yığını

| Alan | Teknoloji | Versiyon / Standart | Açıklama |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com) | `^0.110.0` | Yüksek performanslı asenkron Python web çatısı |
| **ASGI Web Sunucusu** | [Uvicorn](https://www.uvicorn.org) | `^0.28.0` | Hızlı ve güvenilir ASGI HTTP sunucusu |
| **Şablon Motoru** | [Jinja2](https://palletsprojects.com/p/jinja/) | `^3.1.3` | Sunucu taraflı HTML oluşturma motoru |
| **Veritabanı** | [PostgreSQL](https://www.postgresql.org) | `16-alpine` | Kurumsal seviye ilişkisel veritabanı (Compose ile hazır) |
| **ORM** | [SQLAlchemy](https://www.sqlalchemy.org) | `^2.0.28` | Tip güvenli veritabanı modelleme ve sorgu motoru |
| **Veri Doğrulama** | [Pydantic v2](https://docs.pydantic.dev/) | `^2.6.0` | Şema modelleme ve tip denetimi |
| **Konteynerizasyon** | [Docker & Compose](https://www.docker.com/) | v3.8 | Taşınabilir ve izole çalışma ortamı |

---

## 🏛 Katmanlı Mimari (Layered Architecture)

Proje, kurumsal yazılım geliştirme standartlarına uygun olarak sorumlulukların ayrılması (*Separation of Concerns*) prensibiyle yapılandırılmıştır:

```
[ İstemci / Tarayıcı (Browser) ]
              │
              ▼
1. [ Sunum Katmanı (Presentation) ] ──▶ Jinja2 HTML Şablonları & Statik CSS/JS
              │
              ▼
2. [ Yönlendirme Katmanı (API/Controllers) ] ──▶ app/api/ (web_routes, test_routes)
              │
              ▼
3. [ İş Mantığı Katmanı (Services) ] ──▶ app/services/ (CalculatorService vb.)
              │
              ▼
4. [ Şema & Doğrulama Katmanı (Schemas) ] ──▶ app/schemas/ (Pydantic Modelleri)
              │
              ▼
5. [ Veri Modelleri & ORM Katmanı (Persistence) ] ──▶ app/models/ & app/core/database.py
              │
              ▼
[ PostgreSQL Veritabanı ]
```

- **`app/api/` (Controllers):** HTTP isteklerini karşılar, yetki kontrolü ve girdi parametrelerini doğrular.
- **`app/services/` (Business Logic):** İş kurallarını yürütür (örneğin matematiksel işlemler, mezun arama algoritmaları).
- **`app/schemas/` (Data Transfer Objects):** API girdi ve çıktı formatlarını tanımlar ve belgeler.
- **`app/models/` & `app/core/database.py` (Data Access):** Veritabanı tablolarını ve oturum yönetimini temsil eder.

---

## 📂 Proje Dizin Yapısı

```
alumni-tracking-system/
├── app/
│   ├── __init__.py                # Uygulama modül belirteci
│   ├── main.py                    # FastAPI uygulama örneği ve başlatıcı
│   ├── api/                       # API ve Web rotaları
│   │   ├── __init__.py
│   │   ├── web_routes.py          # / ve /about HTML sayfa yönlendirmeleri
│   │   └── test_routes.py         # /hello, /hello/{name}, /sum test uç noktaları
│   ├── core/                      # Temel konfigürasyon ve veritabanı
│   │   ├── __init__.py
│   │   ├── config.py              # Pydantic BaseSettings ortam ayarları
│   │   └── database.py            # SQLAlchemy engine, SessionLocal ve get_db
│   ├── models/                    # SQLAlchemy ORM modelleri (Aşama 2 hazırlığı)
│   │   └── __init__.py
│   ├── schemas/                   # Pydantic veri modelleri
│   │   ├── __init__.py
│   │   └── test_schemas.py        # Test istek/yanıt şemaları
│   ├── services/                  # İş mantığı (Business logic) servisleri
│   │   ├── __init__.py
│   │   └── calculator_service.py  # Örnek hesaplama servisi
│   ├── static/                    # Statik dosyalar
│   │   ├── css/
│   │   │   └── style.css          # Özel, modern ve responsive stil dosyası
│   │   └── js/
│   │       └── main.js            # Etkileşimli test paneli ve mobil menü betiği
│   └── templates/                 # Jinja2 HTML şablonları
│       ├── base.html              # Ortak düzen (header, nav, footer)
│       ├── index.html             # Ana sayfa (Landing page)
│       └── about.html             # Hakkında sayfası
├── Dockerfile                     # Python 3.11 konteyner tanımı
├── docker-compose.yml             # Web ve PostgreSQL servislerinin orkestrasyonu
├── requirements.txt               # Gerekli Python bağımlılıkları
├── .env.example                   # Örnek ortam değişkenleri şablonu
├── .gitignore                     # Git tarafından yok sayılacak dosyalar
└── README.md                      # Proje kılavuzu
```

---

## 🚀 Uç Noktalar (Endpoints)

| Metot | Yol (Path) | Tip | Açıklama | Örnek Yanıt |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | HTML | Modern Açılış Sayfası | HTML Belgesi |
| `GET` | `/about` | HTML | Proje & Mimari Hakkında Sayfası | HTML Belgesi |
| `GET` | `/docs` | HTML | Swagger UI İnteraktif Dokümantasyon | Swagger Arayüzü |
| `GET` | `/redoc` | HTML | ReDoc API Dokümantasyonu | ReDoc Arayüzü |
| `GET` | `/hello` | JSON | Genel selamlama mesajı | `{"message": "Hello, World!"}` |
| `GET` | `/hello/{name}` | JSON | İsme özel kişiselleştirilmiş selamlama | `{"message": "Hello, Ahmet!"}` |
| `GET` | `/sum/{a}/{b}`| JSON | İki sayının toplamını hesaplar | `{"number1": 15, "number2": 27, "operation": "sum", "result": 42}` |

---

## 💻 Yerel Kurulum ve Çalıştırma

### 1. Gereksinimler
- Python 3.9 veya daha güncel bir sürüm
- `pip` paket yöneticisi

### 2. Depoyu Hazırlama & Sanal Ortam (Virtual Environment)
Terminalinizde proje dizinine gelin:

```bash
cd alumni-tracking-system
```

Python sanal ortamı oluşturun ve aktif edin:

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Bağımlılıkları Yükleme
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Uygulamayı Başlatma
Uvicorn ile uygulamayı canlı yeniden yükleme (`--reload`) modunda başlatın:

```bash
uvicorn app.main:app --reload --port 8000
```

Uygulama başarıyla başlatıldığında aşağıdaki adresleri tarayıcınızda açabilirsiniz:
- **Açılış Sayfası (Landing Page):** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Hakkında Sayfası:** [http://127.0.0.1:8000/about](http://127.0.0.1:8000/about)
- **Swagger API Dokümantasyonu:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🐳 Docker ve Docker Compose ile Çalıştırma

Sisteminizde Docker ve Docker Compose yüklü ise, uygulamayı ve PostgreSQL veritabanını tek bir komutla ayağa kaldırabilirsiniz:

```bash
docker compose up --build
```

Arka planda (detached modda) çalıştırmak için:
```bash
docker compose up -d --build
```

Durdurmak için:
```bash
docker compose down
```

---

## 🔮 Gelecek Aşamalar (Roadmap)

- [x] **Aşama 1 (Tamamlandı):** Katmanlı mimari iskeleti, HTML/CSS arayüzü, Swagger dokümantasyonu, test uç noktaları ve Docker konfigürasyonu.
- [ ] **Aşama 2:** PostgreSQL üzerinde Mezun, Fakülte, Bölüm, Kariyer ve İletişim tablolarının SQLAlchemy modelleri ile tanımlanması ve Alembic migrasyonları.
- [ ] **Aşama 3:** JWT (JSON Web Token) tabanlı güvenli kimlik doğrulama, kullanıcı rolleri (Öğrenci, Mezun, Akademisyen, Admin).
- [ ] **Aşama 4:** Mezun arama, filtreleme, kariyer geçmişi ekleme ve mentorluk başvuru modülleri.
- [ ] **Aşama 5:** Veri analitiği ve üniversite mezun istihdam raporları paneli.

---

**Geliştirici:** İstanbul Üniversitesi Web Programlama Dersi Öğrencisi  
**Telif Hakkı:** &copy; 2026 İstanbul Üniversitesi. Tüm hakları saklıdır.
