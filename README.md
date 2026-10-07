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
4. [MVC Architecture](#-mvc-architecture)
5. [Kullanıcı Modeli & Bellek İçi CRUD Servisi](#-kullanıcı-modeli--bellek-içi-crud-servisi)
6. [Project Directory Structure](#-project-directory-structure)
7. [Uç Noktalar (Endpoints)](#-uç-noktalar-endpoints)
8. [Yerel Kurulum ve Çalıştırma](#-yerel-kurulum-ve-çalıştırma)
9. [Docker ve Docker Compose ile Çalıştırma](#-docker-ve-docker-compose-ile-çalıştırma)
10. [Gelecek Aşamalar (Roadmap)](#-gelecek-aşamalar-roadmap)

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

## 🏛 MVC Architecture

Bu proje, modern ve asenkron Python web çatısı olan **FastAPI** ile geliştirilmiştir. FastAPI, Django veya Ruby on Rails gibi geleneksel monolitik MVC (Model-View-Controller) kalıplarını zorunlu kılmak yerine, esnek, modüler ve yüksek performanslı bir **Katmanlı Mimari (Layered Architecture)** yaklaşımını benimser.

Bununla birlikte, sorumlulukların ayrılması (*Separation of Concerns*) prensibi doğrultusunda, projedeki klasör ve dosya yapısı klasik MVC mimarisinin temel kavramlarıyla doğrudan eşleştirilebilir:

### 🧩 MVC Bileşenlerinin Proje Yapısıyla İlişkisi

- **Model (`app/models/`):**  
  Veri modellerini ve veritabanı şemalarını temsil eder. SQLAlchemy ORM modelleri bu klasör altında tanımlanır. Verinin yapısını, tabloları, sütunları ve ilişkileri yöneten kalıcılık (persistence) katmanıdır.
- **View (`app/templates/` ve `app/static/`):**  
  Kullanıcıya sunulan arayüz ve sunum katmanıdır. `app/templates/` altındaki Jinja2 HTML şablonları (`index.html`, `about.html`, `base.html`) dinamik web sayfalarını üretir; `app/static/` altındaki CSS ve JavaScript dosyaları ise arayüz stilini ve istemci taraflı etkileşimleri sağlar. REST API uç noktalarında ise istemciye döndürülen standart JSON formatı veri sunum katmanı (View) olarak işlev görür.
- **Controller / API Routes (`app/api/`):**  
  İstemciden gelen HTTP isteklerini (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) karşılayan, rota parametrelerini doğrulayan ve isteği uygun servis katmanına veya HTML şablonuna yönlendiren kontrol katmanıdır (`web_routes.py`, `test_routes.py`, `health_routes.py`, `user_routes.py`).
- **Service Layer (`app/services/`):**  
  İş mantığının (Business Logic) yürütüldüğü katmandır. Rotaların (controller) hafif ve temiz kalmasını sağlayarak hesaplama, doğrulama ve iş kurallarını bağımsız olarak yürütür (örneğin `CalculatorService`).
- **Core / Configuration (`app/core/`):**  
  Uygulamanın merkezi ortam yapılandırmalarını (`config.py`) ve SQLAlchemy motoru ile veritabanı oturum yönetimini (`database.py`) barındıran altyapı katmanıdır.
- **Application Entry Point (`app/main.py`):**  
  FastAPI uygulamasını başlatan, ara yazılımları (middleware) ve statik dosya dizinini bağlayan, tüm API router'larını uygulamaya dahil eden ana giriş noktasıdır.

> [!IMPORTANT]
> **Kullanıcı Endpoint'leri Simülasyon Durumu (Mock/Test JSON):**  
> Controller katmanında yer alan `app/api/user_routes.py` dosyasındaki `GET`, `PUT`, `PATCH` ve `DELETE` `/api/users/{id}` endpoint'leri şu an **veritabanı üzerinde gerçek bir CRUD işlemi gerçekleştirmemektedir**. Katmanlı mimarinin HTTP metotlarını ve yönlendirme mantığını test etmek amacıyla statik/örnek JSON yanıtları (`{"id": id, "method": "...", "status": "..."}`) döndürmektedir.

---

## 👤 Kullanıcı Modeli & Bellek İçi CRUD Servisi

Katmanlı mimarinin Model ve Service katmanlarını somutlaştırmak üzere bir **User Modeli** ve veritabanı bağımsız çalışan bir **Bellek İçi CRUD Servisi** hayata geçirilmiştir.

### 1. User Modeli (`app/models/user.py`)
FastAPI ve Pydantic v2 mimarisine uygun olarak `User` varlık modeli oluşturulmuştur. Temel mezun/kullanıcı bilgilerini temsil eden alanlar şunlardır:
- `id`: Benzersiz kullanıcı kimliği (`Optional[int]`, servis tarafından otomatik olarak atanır).
- `name`: Kullanıcı / mezun adı soyadı (`str`, zorunlu alan).
- `email`: Kullanıcı e-posta adresi (`str`, zorunlu alan).
- `department`: Mezun olunan veya kayıtlı olunan bölüm (`str`, zorunlu alan).
- `graduation_year`: Mezuniyet yılı (`int`, 1900-2100 aralığında geçerli).

### 2. Bellek İçi CRUD Servisi (`app/services/user_service.py`)
Kullanıcılar üzerinde temel CRUD işlemlerini gerçekleştiren `UserService` sınıfı ve fonksiyonel kısayolları tanımlanmıştır:
- `create_user(...)`: Yeni bir kullanıcı oluşturur, otomatik artan `id` değeri atar ve belleğe kaydeder.
- `get_user(user_id)`: Belirtilen `id` değerine sahip kullanıcıyı getirir (bulunamazsa `None`).
- `get_users()`: Bellekteki tüm kullanıcıları liste halinde döndürür.
- `update_user(user_id, ...)`: Belirtilen kullanıcının alanlarını günceller (bulunamazsa `None`).
- `delete_user(user_id)`: Belirtilen kullanıcıyı bellekten siler (başarılıysa `True`, bulunamazsa `False`).

Kullanıcı verileri geçici olarak bellek içinde basit bir Python veri yapısında (`Dict[int, User]`) saklanmaktadır.

### 3. Veritabanı Durumu & Gelecek Aşamalar
> [!NOTE]
> **Henüz Veritabanı Bağlantısı Kullanılmamaktadır:**  
> Bu aşamada PostgreSQL veya SQLAlchemy üzerinden herhangi bir veritabanı bağlantısı kurulmamış ve veritabanı işlemi gerçekleştirilmemiştir. Model ve servis tamamen bağımsız ve bellek içi (in-memory) çalışacak şekilde tasarlanmıştır.  
> Gerçek veritabanı entegrasyonu (PostgreSQL tabloları, Alembic migrasyonları ve SQLAlchemy ORM kalıcılığı) projenin sonraki aşamalarında eklenecektir.

---

## 📂 Project Directory Structure

Projede yer alan gerçek dizin ve dosya yapısı aşağıda gösterilmektedir:

```
alumni-tracking-system/
├── app/
│   ├── __init__.py                # Uygulama paket modülü belirteci
│   ├── main.py                    # FastAPI uygulama örneği ve router kayıtları (Giriş Noktası)
│   ├── api/                       # Controller Katmanı: HTTP rotaları ve uç noktalar
│   │   ├── __init__.py
│   │   ├── health_routes.py       # Sistem sağlık kontrolü rotası (/api/health)
│   │   ├── test_routes.py         # Test ve hesaplama uç noktaları (/hello, /sum)
│   │   ├── user_routes.py         # Kullanıcı simülasyon rotaları (/api/users/{id})
│   │   └── web_routes.py          # Web sayfaları HTML şablon rotaları (/ ve /about)
│   ├── core/                      # Temel konfigürasyon ve veritabanı altyapısı
│   │   ├── __init__.py
│   │   ├── config.py              # Pydantic BaseSettings ortam ayarları
│   │   └── database.py            # SQLAlchemy engine, SessionLocal ve get_db oturum yönetimi
│   ├── models/                    # Model Katmanı: Veri modelleri
│   │   ├── __init__.py            # Modeller paket belirteci ve export listesi
│   │   └── user.py                # Pydantic User (Mezun/Kullanıcı) modeli
│   ├── schemas/                   # Pydantic veri modelleri ve DTO (Data Transfer Object) şemaları
│   │   ├── __init__.py
│   │   └── test_schemas.py        # Test uç noktaları için girdi/çıktı doğrulama şemaları
│   ├── services/                  # İş Mantığı Katmanı (Business Logic / Service Layer)
│   │   ├── __init__.py            # Servisler paket belirteci ve export listesi
│   │   ├── calculator_service.py  # Örnek hesaplama iş mantığı servisi
│   │   └── user_service.py        # Bellek içi User CRUD servisi
│   ├── static/                    # View Katmanı: Statik varlıklar
│   │   ├── css/
│   │   │   └── style.css          # Özel responsive CSS stil dosyası
│   │   └── js/
│   │       └── main.js            # İstemci taraflı etkileşim ve test konsolu betiği
│   └── templates/                 # View Katmanı: Jinja2 HTML şablonları
│       ├── base.html              # Ortak düzen iskeleti (header, navbar, footer)
│       ├── index.html             # Ana açılış sayfası (Landing Page)
│       └── about.html             # Proje hakkında sayfası
├── tests/                         # Birim test paketi
│   ├── __init__.py                # Test paketi belirteci
│   └── test_user_service.py       # User modeli ve bellek içi CRUD servisi birim testleri
├── Dockerfile                     # Python 3.11 konteyner ortam tanımı
├── docker-compose.yml             # Web ve PostgreSQL servislerinin orkestrasyonu
├── requirements.txt               # Proje bağımlılıkları listesi
├── .env.example                   # Ortam değişkenleri örnek şablonu
├── .gitignore                     # Git sürüm kontrolü hariç tutma kuralları
└── README.md                      # Proje dokümantasyonu ve mimari kılavuz
```

### 📁 Klasör ve Dosyaların Görevleri

#### 1. Ana Uygulama Klasörü (`app/`)
- **`app/api/` (Controller / API Routes):**  
  HTTP isteklerini yakalayan ve yönlendiren uç noktaları barındırır.
  - **`app/api/web_routes.py`:** Jinja2 şablon motorunu kullanarak tarayıcıya HTML sayfalarını (`/` açılış sayfası ve `/about` hakkında sayfası) sunan web yönlendirmesidir.
  - **`app/api/test_routes.py`:** Katmanlı mimari işleyişini, Pydantic doğrulamasını ve servis katmanı entegrasyonunu doğrulamak için `/hello`, `/hello/{name}` ve `/sum/{a}/{b}` test uç noktalarını barındırır.
  - **`app/api/health_routes.py`:** Sistemin ve sunucunun ayakta olduğunu denetleyen `/api/health` sağlık kontrolü GET endpoint'ini (`{"status": "ok"}`) sunar.
  - **`app/api/user_routes.py`:** Kullanıcı işlemleri için `/api/users/{id}` rotası altında `GET`, `PUT`, `PATCH` ve `DELETE` HTTP metotlarını karşılar. *(Gerçek veritabanı işlemi yapmaksızın test/simülasyon amaçlı örnek JSON yanıtları döner.)*
- **`app/core/` (Core / Configuration):**  
  Uygulamanın temel ayarlarını ve veritabanı altyapısını yönetir.
  - **`app/core/config.py`:** Pydantic `BaseSettings` ile `.env` dosyasından ve ortam değişkenlerinden uygulama adı, sürüm, port ve veritabanı URL'si gibi yapılandırmaları okur.
  - **`app/core/database.py`:** SQLAlchemy veritabanı motorunu (`create_engine`), oturum fabrikasını (`sessionmaker`) ve FastAPI bağımlılık enjeksiyonunda kullanılan `get_db` fonksiyonunu tanımlar.
- **`app/models/` (Model Katmanı):**  
  Veri modellerini barındırır.
  - **`app/models/user.py`:** Temel mezun/kullanıcı varlığını temsil eden Pydantic modelidir (`id`, `name`, `email`, `department`, `graduation_year`).
- **`app/schemas/` (Data Transfer Objects / Pydantic Schemas):**  
  İstek ve yanıt verilerinin tiplerini, doğrulamalarını ve OpenAPI şemalarını belirleyen Pydantic modellerini (`test_schemas.py`) içerir.
- **`app/services/` (Service Layer / Business Logic):**  
  İş mantığının yürütüldüğü servis sınıflarını barındırır.
  - **`app/services/calculator_service.py`:** Örnek hesaplama iş mantığını yürütür.
  - **`app/services/user_service.py`:** Bellek içinde geçici olarak saklanan kullanıcılar üzerinde `create_user`, `get_user`, `get_users`, `update_user` ve `delete_user` CRUD işlemlerini gerçekleştirir.
- **`app/static/` (View / Statik Dosyalar):**  
  Arayüzün görsel tasarımını sağlayan CSS stillerini (`css/style.css`) ve sayfa içi dinamik özellikleri yöneten JavaScript dosyalarını (`js/main.js`) barındırır.
- **`app/templates/` (View / Jinja2 Şablonları):**  
  Sunucu taraflı render edilen HTML şablonlarını (`base.html`, `index.html`, `about.html`) barındırır.

#### 2. Uygulama Giriş Noktası (`app/main.py`)
- **`app/main.py`:**  
  FastAPI uygulamasının ana giriş noktasıdır.
  - `FastAPI(...)` örneğini oluşturur ve OpenAPI/Swagger başlıklarını, açıklamalarını yapılandırır,
  - `/static` dizinini `StaticFiles` ile uygulamaya bağlar (`app.mount("/static", ...)`),
  - Tüm router'ları (`web_router`, `test_router`, `health_router`, `user_router`) `app.include_router(...)` fonksiyonu ile merkezi olarak uygulamaya dahil eder,
  - Doğrudan çalıştırıldığında Uvicorn ASGI sunucusunu başlatır.

#### 3. Test Paketi (`tests/`)
- **`tests/test_user_service.py`:**  
  Herhangi bir harici veritabanına ihtiyaç duymaksızın `User` modelinin Pydantic doğrulamalarını ve `UserService` bellek içi CRUD fonksiyonlarını (`create_user`, `get_user`, `get_users`, `update_user`, `delete_user`) test eden 9 adet birim test içerir (`python -m unittest discover -s tests`).

#### 4. Kök Dizin Yapılandırma Dosyaları
- **`Dockerfile`:** Uygulamanın Python 3.11 tabanlı konteyner ortamında çalışması için gereken adımları tanımlar.
- **`docker-compose.yml`:** FastAPI web uygulaması ile PostgreSQL 16 veritabanı konteynerini birlikte başlatan orkestrasyon dosyasıdır.
- **`requirements.txt`:** FastAPI, Uvicorn, SQLAlchemy, Pydantic, Jinja2 vb. bağımlılıkları listeler.
- **`.env.example`:** Ortam değişkenleri için örnek konfigürasyon şablonudur.
- **`.gitignore`:** `venv/`, `__pycache__/`, `.env` gibi Git tarafından takip edilmemesi gereken dosya ve dizinleri tanımlar.
- **`README.md`:** Projenin mimarisini, dizin yapısını, kurulum ve çalıştırma adımlarını açıklayan kapsamlı kılavuzdur.

---

## 🚀 Uç Noktalar (Endpoints)

FastAPI, OpenAPI standardını kullanarak etkileşimli API dokümantasyonunu otomatik olarak üretir:
- **Swagger UI:** `http://127.0.0.1:8000/docs` adresinden erişilebilir. Swagger UI, FastAPI tarafından otomatik olarak sağlanmaktadır. Bu arayüz üzerinden tüm uç noktalar tarayıcı üzerinden doğrudan test edilebilir, parametreler ve şemalar görüntülenebilir.
- **ReDoc:** `http://127.0.0.1:8000/redoc` adresinden erişilebilen alternatif API dokümantasyonudur.

### 📋 Uç Nokta Listesi

| Metot | Yol (Path) | Tip | Açıklama | Örnek Yanıt |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | HTML | Modern Açılış Sayfası | HTML Belgesi |
| `GET` | `/about` | HTML | Proje & Mimari Hakkında Sayfası | HTML Belgesi |
| `GET` | `/docs` | HTML | Swagger UI Dokümantasyonu (FastAPI otomatik sağlar) | Swagger Arayüzü (`http://127.0.0.1:8000/docs`) |
| `GET` | `/redoc` | HTML | ReDoc API Dokümantasyonu | ReDoc Arayüzü |
| `GET` | `/api/health` | JSON | Servisin çalışır durumda olduğunu ve sağlık durumunu kontrol eder | `{"status": "ok"}` |
| `GET` | `/api/users/{id}` | JSON | Kullanıcı getirme için örnek/test amaçlı JSON yanıtı döner (veritabanı işlemi yapmaz) | `{"id": 1, "method": "GET", "status": "ok"}` |
| `PUT` | `/api/users/{id}` | JSON | Kullanıcı güncelleme için örnek/test amaçlı JSON yanıtı döner (veritabanı işlemi yapmaz) | `{"id": 1, "method": "PUT", "status": "updated"}` |
| `PATCH` | `/api/users/{id}` | JSON | Kullanıcı kısmi güncelleme için örnek/test amaçlı JSON yanıtı döner (veritabanı işlemi yapmaz) | `{"id": 1, "method": "PATCH", "status": "updated"}` |
| `DELETE` | `/api/users/{id}` | JSON | Kullanıcı silme için örnek/test amaçlı JSON yanıtı döner (veritabanı işlemi yapmaz) | `{"id": 1, "method": "DELETE", "status": "deleted"}` |
| `GET` | `/hello` | JSON | Genel selamlama mesajı döner | `{"message": "Hello, World!"}` |
| `GET` | `/hello/{name}` | JSON | İsme özel kişiselleştirilmiş selamlama mesajı döner | `{"message": "Hello, Ahmet!"}` |
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
- **Swagger API Dokümantasyonu:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (FastAPI tarafından otomatik olarak sağlanır)
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
