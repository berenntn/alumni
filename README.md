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
6. [User Controllers (UserController & ApiUserController)](#-user-controllers-usercontroller--apiusercontroller)
7. [View Katmanı & Kullanıcı Yönetim Sayfaları (View Layer)](#-view-katmanı--kullanıcı-yönetim-sayfaları-view-layer)
8. [Project Directory Structure](#-project-directory-structure)
9. [Uç Noktalar (Endpoints) & Swagger UI](#-uç-noktalar-endpoints--swagger-ui)
10. [Yerel Kurulum ve Çalıştırma](#-yerel-kurulum-ve-çalıştırma)
11. [Docker ve Docker Compose ile Çalıştırma](#-docker-ve-docker-compose-ile-çalıştırma)
12. [Gelecek Aşamalar (Roadmap)](#-gelecek-aşamalar-roadmap)

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
- **Controller (`app/controllers/`) & API Routes (`app/api/`):**  
  İstemciden gelen HTTP isteklerini (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) karşılayan, rota parametrelerini ve gövde verilerini (Pydantic şemaları) doğrulayan ve isteği uygun controller katmanına yönlendiren kontrol katmanıdır (`web_routes.py` -> `UserController`, `user_routes.py` -> `ApiUserController`, `test_routes.py`, `health_routes.py`). Rotalar doğrudan servis katmanına erişmez; tüm işlemler controller sınıfları üzerinden delege edilir.
- **Service Layer (`app/services/`):**  
  İş mantığının (Business Logic) yürütüldüğü katmandır. Rotaların (controller) hafif ve temiz kalmasını sağlayarak hesaplama, doğrulama ve iş kurallarını bağımsız olarak yürütür (örneğin `CalculatorService`, `UserService`).
- **Core / Configuration (`app/core/`):**  
  Uygulamanın merkezi ortam yapılandırmalarını (`config.py`) ve SQLAlchemy motoru ile veritabanı oturum yönetimini (`database.py`) barındıran altyapı katmanıdır.
- **Application Entry Point (`app/main.py`):**  
  FastAPI uygulamasını başlatan, ara yazılımları (middleware) ve statik dosya dizinini bağlayan, tüm API router'larını uygulamaya dahil eden ana giriş noktasıdır.

> [!NOTE]
> **Controller ve Rota Entegrasyonu (Route-to-Controller Delegation):**  
> `app/api/web_routes.py` altındaki web rotaları `UserController`'a, `app/api/user_routes.py` altındaki REST API rotaları ise `ApiUserController`'a bağlanmıştır. Rotalar doğrudan `UserService` ile temas kurmaz; tüm veri akışı ilgili controller sınıfı üzerinden yürütülür.

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

## 🎮 User Controllers (UserController & ApiUserController)

MVC mimarisinde Controller bileşeni, kullanıcı/istemci isteklerini karşılayarak iş mantığı ve model katmanıyla aradaki koordinasyonu sağlar. Bu aşamada kullanıcı işlemleri için sorumlulukları net olarak ayrılmış iki farklı controller sınıfı hayata geçirilmiştir:

### 1. UserController (`app/controllers/user_controller.py`)
Genel ve web arayüzüne yönelik kullanıcı işlemlerini yöneten controller katmanıdır:
- **Sorumluluk Alanı:** Web/Jinja2 şablon sunumuna yönelik iş akışları, web portalı kullanıcı koordinasyonu.
- **CRUD Metotları:**
  - `create_user(...)`: Yeni kullanıcı oluşturur, web durum ve sonuç sözlüğü döner (`{"success": True, "message": "...", "user": ...}`).
  - `get_user(user_id)`: Tekil kullanıcıyı sorgular (`{"success": True, "user": ...}`). Bulunamazsa `success=False` döner.
  - `get_users()`: Tüm kullanıcıları web arayüzü listelemesine uygun olarak döner (`{"success": True, "users": [...], "count": N}`).
  - `update_user(user_id, ...)`: Kullanıcı bilgilerini günceller ve güncel sonucu döner.
  - `delete_user(user_id)`: Kullanıcıyı siler ve başarı durumunu döner.

### 2. ApiUserController (`app/controllers/api_user_controller.py`)
REST API istemcilerine (mobil uygulamalar, harici servisler veya AJAX/fetch istekleri) yönelik kullanıcı işlemlerini yöneten controller katmanıdır:
- **Sorumluluk Alanı:** JSON tabanlı RESTful API uç noktaları için girdi/çıktı biçimlendirmesi ve durum yönetimi.
- **CRUD Metotları:**
  - `create_user(...)`: API standardında serileştirilmiş JSON çıktısı döner (`{"status": "success", "data": {...}, "message": "..."}`).
  - `get_user(user_id)`: İlgili kullanıcıyı serileştirilmiş veriyle döner (`{"status": "success", "data": {...}}`); bulunamazsa hata durumunu raporlar (`{"status": "error", ...}`).
  - `get_users()`: Tüm kullanıcıları serileştirilmiş liste olarak döner (`{"status": "success", "data": [...], "count": N}`).
  - `update_user(user_id, ...)`: Kullanıcıyı günceller ve güncellenmiş API veri nesnesini döner.
  - `delete_user(user_id)`: Kullanıcıyı siler ve API başarı/hata durumunu döner.

### 3. Controller ve UserService İşbirliği (Delegation Pattern)
- **Mantık Tekrarının Önlenmesi:** Her iki controller sınıfı da veritabanı veya bellek içi veri saklama mantığını kendi içerisinde **kesinlikle tekrarlamaz**.
- **Servis Katmanına Delegasyon:** Tüm CRUD işlemleri, veri saklama ve model doğrulama adımları için doğrudan `UserService` (`app/services/user_service.py`) çağrılır.
- **Rotaların Bağımsızlığı:** HTTP rota dosyaları (`app/api/user_routes.py` ve `app/api/web_routes.py`) doğrudan `UserService`'e erişmez; istekleri controller sınıflarına (`UserController` ve `ApiUserController`) devreder.
- **Bağımsızlık & Test Edilebilirlik:** Controller'lar saf Python sınıfları olarak tasarlanmıştır ve herhangi bir veritabanı bağlantısı gerektirmeksizin birim testlerle (`tests/test_user_controller.py` ve `tests/test_api_user_controller.py`) tamamen doğrulanmıştır.

### 4. Rota ve Controller Bağlantıları (Route to Controller Mapping)

FastAPI rota modülleri, ilgili controller sınıflarına bağlanarak katmanlar arası ayrım tam olarak sağlanmıştır:

| Rota (Route) | HTTP Metodu | Sorumlu Controller | Çağrılan Metot | Açıklama |
| :--- | :--- | :--- | :--- | :--- |
| `/` | `GET` | `UserController` | `get_users()` | Ana sayfa (Landing Page) arayüzü ve mezun listesi |
| `/about` | `GET` | - | - | Proje hakkında sayfası |
| `/users` | `GET` | `UserController` | `get_users()` | Web arayüzü kullanıcı listeleme |
| `/users` | `POST` | `UserController` | `create_user()` | Web arayüzü kullanıcı oluşturma |
| `/users/{id}` | `GET` | `UserController` | `get_user(id)` | Web arayüzü kullanıcı detayı |
| `/users/{id}` | `PUT` | `UserController` | `update_user(id, ...)` | Web arayüzü kullanıcı güncelleme |
| `/users/{id}` | `DELETE` | `UserController` | `delete_user(id)` | Web arayüzü kullanıcı silme |
| `/api/users` | `GET` | `ApiUserController` | `get_users()` | REST API: Tüm kullanıcıları listeleme |
| `/api/users` | `POST` | `ApiUserController` | `create_user(...)` | REST API: Yeni kullanıcı oluşturma (201 Created) |
| `/api/users/{id}` | `GET` | `ApiUserController` | `get_user(id)` | REST API: ID ile tekil kullanıcı sorgulama |
| `/api/users/{id}` | `PUT` | `ApiUserController` | `update_user(id, ...)` | REST API: Kullanıcı tam güncelleme |
| `/api/users/{id}` | `PATCH` | `ApiUserController` | `update_user(id, ...)` | REST API: Kullanıcı kısmi güncelleme |
| `/api/users/{id}` | `DELETE` | `ApiUserController` | `delete_user(id)` | REST API: Kullanıcı silme |

### 5. Pydantic İstek/Yanıt Şemaları (`app/schemas/user_schemas.py`)
REST API uç noktalarında tip güvenliği ve otomatik OpenAPI/Swagger dokümantasyonu için özel Pydantic şemaları tanımlanmıştır:
- `UserCreateRequest`: Yeni kullanıcı kaydı için zorunlu alanlar (`name`, `email`, `department`, `graduation_year`).
- `UserUpdateRequest`: PUT uç noktası için tam güncelleme şeması.
- `UserPatchRequest`: PATCH uç noktası için tüm alanların opsiyonel olduğu kısmi güncelleme şeması.
- `UserResponseData`: API yanıtlarında kullanıcı verisinin serileştirilmiş biçimi.
- `UserApiResponse`: Tekil kullanıcı işlemleri için standart JSON zarfı (`status`, `message`, `data`).
- `UserListApiResponse`: Çoklu kullanıcı sorguları için liste zarfı (`status`, `message`, `data`, `count`).
- `UserDeleteApiResponse`: Silme işlemi yanıt şeması (`status`, `message`).

### 6. Bellek İçi Saklama & Veritabanı Durumu
> [!NOTE]
> Proje bu aşamada halen **in-memory (bellek içi)** veri saklama yapısını (`Dict[int, User]`) kullanmaya devam etmektedir. PostgreSQL veya SQLAlchemy veritabanı bağlantısı henüz eklenmemiştir ve sonraki aşamalarda entegre edilecektir.

---

## 🖥 View Katmanı & Kullanıcı Yönetim Sayfaları (View Layer)

MVC mimarisinin **View (Görünüm)** katmanı, sunucu tarafında oluşturulan (server-side rendered) Jinja2 HTML şablonları ve statik varlıklar (CSS/JS) ile hayata geçirilmiştir. Bu aşamada kullanıcıların doğrudan tarayıcı üzerinden mezunları görüntüleyebileceği (**Listings / Read**) ve yeni mezun ekleyebileceği (**Creating / Create**) iki temel web rotası View katmanına bağlanmıştır.

### 🔄 Mimari Veri ve Kontrol Akışı (Route ➔ Controller ➔ Service ➔ View)
Sorumlulukların ayrılması (*Separation of Concerns*) prensibine tam bağlı kalınarak rotalar doğrudan servis veya model ile iletişim kurmaz:

```
İstemci / Tarayıcı (Browser)
       │ (1. HTTP İsteği: GET /users veya POST /users)
       ▼
1. Web Rotaları Katmanı [app/api/web_routes.py]
       │ (2. İstek parametrelerini veya form verisini ayrıştırır)
       ▼
2. Controller Katmanı [UserController - app/controllers/user_controller.py]
       │ (3. İşlemi servis katmanına delege eder)
       ▼
3. İş Mantığı / Servis Katmanı [UserService - app/services/user_service.py]
       │ (4. Bellek içi veriyi işler ve sonucu Controller'a döner)
       ▲ (5. Controller standart sonucu Web Rotasına aktarır)
       ▼
4. View / Sunum Katmanı [Jinja2 Templates - app/templates/users/list.html]
       │ (6. Context verisiyle HTML şablonunu oluşturur)
       ▼
İstemciye Yanıt (Render Edilmiş HTML Sayfası)
```

### 📋 Web View Rotaları

#### 1. `GET /users` ➔ Kullanıcı Listeleme (Listings / Read)
- **Sorumlu Rota:** `app/api/web_routes.py` -> `get_web_users()`
- **Sorumlu Controller:** `UserController.get_users()`
- **Kullanılan Şablon (View):** `app/templates/users/list.html`
- **İşleyiş:**
  - `UserController.get_users()` çağrılarak bellekte saklanan tüm kullanıcılar alınır.
  - Alınan liste `users/list.html` Jinja2 şablonuna context verisi olarak aktarılır.
  - Sayfada mezunların **Ad Soyad**, **E-posta**, **Bölüm** ve **Mezuniyet Yılı** bilgileri temiz ve responsive bir tabloda listelenir.
  - Eğer henüz hiç kullanıcı eklenmemişse, kullanıcıyı bilgilendiren anlaşılır bir **"No users found"** boş durum mesajı görüntülenir.

#### 2. `POST /users` ➔ Kullanıcı Oluşturma (Creating / Create)
- **Sorumlu Rota:** `app/api/web_routes.py` -> `create_web_user()`
- **Sorumlu Controller:** `UserController.create_user(payload)`
- **Kullanılan Şablon (View):** `app/templates/users/list.html`
- **Form Alanları:**
  - `name`: Kullanıcı / mezun tam adı (zorunlu metin alanı).
  - `email`: İletişim e-posta adresi (zorunlu e-posta alanı).
  - `department`: Mezun olunan / kayıtlı bölüm (zorunlu metin alanı).
  - `graduation_year`: Mezuniyet yılı (zorunlu sayısal alan, 1900-2100).
- **İşleyiş:**
  - HTML formundan gönderilen veriler (`application/x-www-form-urlencoded` veya `application/json`) ayrıştırılır.
  - `graduation_year` değeri tamsayıya dönüştürülerek `UserController.create_user(...)` fonksiyonuna iletilir.
  - **Başarılı Durumda:** Yeni kullanıcı oluşturulur, güncel kullanıcı listesi ve yeşil bildirim kutusu (`success_message: "Kullanıcı başarıyla oluşturuldu."`) ile liste sayfasına dönülür (HTTP 200).
  - **Hata Durumunda:** Girdi doğrulaması başarısız olursa kullanıcıya anlaşılır bir hata bildirimi (`error_message`) gösterilerek aynı sayfa render edilir (HTTP 400).

---

## 📂 Project Directory Structure

Projede yer alan gerçek dizin ve dosya yapısı aşağıda gösterilmektedir:

```
alumni-tracking-system/
├── app/
│   ├── __init__.py                # Uygulama paket modülü belirteci
│   ├── main.py                    # FastAPI uygulama örneği ve router kayıtları (Giriş Noktası)
│   ├── api/                       # HTTP rotaları ve uç noktalar
│   │   ├── __init__.py
│   │   ├── health_routes.py       # Sistem sağlık kontrolü rotası (/api/health)
│   │   ├── test_routes.py         # Test ve hesaplama uç noktaları (/hello, /sum)
│   │   ├── user_routes.py         # REST API kullanıcı CRUD rotaları (ApiUserController)
│   │   └── web_routes.py          # Web sayfaları ve arayüz rotaları (UserController)
│   ├── controllers/               # Controller Katmanı: MVC Controller sınıfları
│   │   ├── __init__.py            # Controller paket belirteci ve export listesi
│   │   ├── api_user_controller.py # REST API kullanıcı CRUD controller'ı
│   │   └── user_controller.py     # Web/Genel kullanıcı CRUD controller'ı
│   ├── core/                      # Temel konfigürasyon ve veritabanı altyapısı
│   │   ├── __init__.py
│   │   ├── config.py              # Pydantic BaseSettings ortam ayarları
│   │   └── database.py            # SQLAlchemy engine, SessionLocal ve get_db oturum yönetimi
│   ├── models/                    # Model Katmanı: Veri modelleri
│   │   ├── __init__.py            # Modeller paket belirteci ve export listesi
│   │   └── user.py                # Pydantic User (Mezun/Kullanıcı) modeli
│   ├── schemas/                   # Pydantic veri modelleri ve DTO (Data Transfer Object) şemaları
│   │   ├── __init__.py            # Şemalar paket belirteci ve export listesi
│   │   ├── test_schemas.py        # Test uç noktaları için girdi/çıktı doğrulama şemaları
│   │   └── user_schemas.py        # User CRUD API istek/yanıt Pydantic şemaları
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
│       ├── about.html             # Proje hakkında sayfası
│       └── users/                 # Kullanıcı yönetimi View şablonları
│           └── list.html          # Kullanıcı listeleme ve ekleme formu View şablonu
├── tests/                         # Birim ve entegrasyon test paketi
│   ├── __init__.py                # Test paketi belirteci
│   ├── test_api_user_controller.py # ApiUserController REST API CRUD birim testleri
│   ├── test_routes.py             # Route-to-controller ve HTTP uç nokta entegrasyon testleri
│   ├── test_user_controller.py    # UserController web CRUD birim testleri
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
- **`app/api/` (HTTP Rotaları):**  
  HTTP isteklerini yakalayan ve yönlendiren uç noktaları barındırır.
  - **`app/api/web_routes.py`:** Jinja2 şablon motorunu kullanarak tarayıcıya HTML sayfalarını (`/` açılış sayfası, `/about` hakkında sayfası, `/users` mezunlar listesi ve oluşturma sayfası) sunar ve `/users` web rotalarını `UserController` üzerinden yönetir.
  - **`app/api/test_routes.py`:** Katmanlı mimari işleyişini, Pydantic doğrulamasını ve servis katmanı entegrasyonunu doğrulamak için `/hello`, `/hello/{name}` ve `/sum/{a}/{b}` test uç noktalarını barındırır.
  - **`app/api/health_routes.py`:** Sistemin ve sunucunun ayakta olduğunu denetleyen `/api/health` sağlık kontrolü GET endpoint'ini (`{"status": "ok"}`) sunar.
  - **`app/api/user_routes.py`:** Kullanıcı REST API CRUD işlemlerini (`/api/users`, `/api/users/{id}`) `ApiUserController` üzerinden yönetir, Pydantic şemaları ile istek ve yanıtları doğrular.
- **`app/controllers/` (Controller Katmanı - MVC Controllers):**  
  Sunum/API katmanı ile servis katmanı arasındaki koordinasyonu sağlayan controller sınıflarını barındırır.
  - **`app/controllers/user_controller.py`:** Web ve genel sunum katmanına yönelik kullanıcı CRUD işlemlerini yönetir (`create_user`, `get_user`, `get_users`, `update_user`, `delete_user`).
  - **`app/controllers/api_user_controller.py`:** REST API istemcilerine yönelik kullanıcı CRUD işlemlerini yönetir ve standart JSON yanıtlarını üretir.
- **`app/core/` (Core / Configuration):**  
  Uygulamanın temel ayarlarını ve veritabanı altyapısını yönetir.
  - **`app/core/config.py`:** Pydantic `BaseSettings` ile `.env` dosyasından ve ortam değişkenlerinden uygulama adı, sürüm, port ve veritabanı URL'si gibi yapılandırmaları okur.
  - **`app/core/database.py`:** SQLAlchemy veritabanı motorunu (`create_engine`), oturum fabrikasını (`sessionmaker`) ve FastAPI bağımlılık enjeksiyonunda kullanılan `get_db` fonksiyonunu tanımlar.
- **`app/models/` (Model Katmanı):**  
  Veri modellerini barındırır.
  - **`app/models/user.py`:** Temel mezun/kullanıcı varlığını temsil eden Pydantic modelidir (`id`, `name`, `email`, `department`, `graduation_year`).
- **`app/schemas/` (Data Transfer Objects / Pydantic Schemas):**  
  İstek ve yanıt verilerinin tiplerini, doğrulamalarını ve OpenAPI şemalarını belirleyen Pydantic modellerini içerir (`test_schemas.py` ve `user_schemas.py`).
- **`app/services/` (Service Layer / Business Logic):**  
  İş mantığının yürütüldüğü servis sınıflarını barındırır.
  - **`app/services/calculator_service.py`:** Örnek hesaplama iş mantığını yürütür.
  - **`app/services/user_service.py`:** Bellek içinde geçici olarak saklanan kullanıcılar üzerinde `create_user`, `get_user`, `get_users`, `update_user` ve `delete_user` CRUD işlemlerini gerçekleştirir.
- **`app/static/` (View / Statik Dosyalar):**  
  Arayüzün görsel tasarımını sağlayan CSS stillerini (`css/style.css`) ve sayfa içi dinamik özellikleri yöneten JavaScript dosyalarını (`js/main.js`) barındırır.
- **`app/templates/` (View / Jinja2 Şablonları):**  
  Sunucu taraflı render edilen HTML şablonlarını barındırır:
  - `base.html`: Ortak düzen iskeleti (navigasyon menüsü, footer, genel stiller).
  - `index.html`: Modern ana açılış sayfası (Landing Page).
  - `about.html`: Proje ve katmanlı mimari hakkında sayfası.
  - `users/list.html`: Kullanıcı listesini (`GET /users`) görüntüleyen ve yeni kullanıcı oluşturma formunu (`POST /users`) barındıran View şablonu.

#### 2. Uygulama Giriş Noktası (`app/main.py`)
- **`app/main.py`:**  
  FastAPI uygulamasının ana giriş noktasıdır.
  - `FastAPI(...)` örneğini oluşturur ve OpenAPI/Swagger başlıklarını, açıklamalarını ve etiketlerini (`openapi_tags`) yapılandırır,
  - `/static` dizinini `StaticFiles` ile uygulamaya bağlar (`app.mount("/static", ...)`),
  - Tüm router'ları (`web_router`, `test_router`, `health_router`, `user_router`) `app.include_router(...)` fonksiyonu ile merkezi olarak uygulamaya dahil eder,
  - Doğrudan çalıştırıldığında Uvicorn ASGI sunucusunu başlatır.

#### 3. Test Paketi (`tests/`)
- **`tests/test_routes.py`:** Doğrudan ASGI istekleri ile `user_routes.py`, `web_routes.py`, `health_routes.py` ve `test_routes.py` rotalarının controller bağlantılarını, HTTP durum kodlarını ve JSON yanıtlarını test eder.
- **`tests/test_user_controller.py`:** `UserController` sınıfının web odaklı 5 temel CRUD fonksiyonunu (`create_user`, `get_user`, `get_users`, `update_user`, `delete_user`) ve `UserService` delegasyonunu test eder.
- **`tests/test_api_user_controller.py`:** `ApiUserController` sınıfının REST API formatındaki 5 temel CRUD fonksiyonunu ve serileştirilmiş çıktılarını test eder.
- **`tests/test_user_service.py`:** `User` modelinin Pydantic doğrulamalarını ve `UserService` bellek içi CRUD işlemlerini test eder.
*(Tüm testler harici veritabanı gerektirmeksizin `python -m unittest discover -s tests` ile çalıştırılabilir).*

#### 4. Kök Dizin Yapılandırma Dosyaları
- **`Dockerfile`:** Uygulamanın Python 3.11 tabanlı konteyner ortamında çalışması için gereken adımları tanımlar.
- **`docker-compose.yml`:** FastAPI web uygulaması ile PostgreSQL 16 veritabanı konteynerini birlikte başlatan orkestrasyon dosyasıdır.
- **`requirements.txt`:** FastAPI, Uvicorn, SQLAlchemy, Pydantic, Jinja2 vb. bağımlılıkları listeler.
- **`.env.example`:** Ortam değişkenleri için örnek konfigürasyon şablonudur.
- **`.gitignore`:** `venv/`, `__pycache__/`, `.env` gibi Git tarafından takip edilmemesi gereken dosya ve dizinleri tanımlar.
- **`README.md`:** Projenin mimarisini, dizin yapısını, kurulum ve çalıştırma adımlarını açıklayan kapsamlı kılavuzdur.

---

## 🚀 Uç Noktalar (Endpoints) & Swagger UI

FastAPI, OpenAPI 3.1 standardını kullanarak etkileşimli API dokümantasyonunu otomatik olarak üretir:
- **Swagger UI:** `http://127.0.0.1:8000/docs` adresinden erişilebilir. Swagger UI, FastAPI tarafından otomatik olarak sağlanmaktadır. Bu arayüz üzerinden tüm uç noktalar tarayıcı üzerinden doğrudan test edilebilir, şemalar ve HTTP durum kodları incelenebilir.
- **ReDoc:** `http://127.0.0.1:8000/redoc` adresinden erişilebilen alternatif API dokümantasyonudur.

### 🏷️ Swagger OpenAPI Etiket Grupları (Tags)
OpenAPI dokümantasyonunda uç noktalar mantıksal gruplara ayrılmıştır:
1. **Users (`ApiUserController`):** REST API CRUD uç noktaları (`/api/users`, `/api/users/{id}`). İstek ve yanıtlar Pydantic modelleri (`UserCreateRequest`, `UserUpdateRequest`, `UserPatchRequest`, `UserApiResponse` vb.) ile tip güvenli olarak doğrulanır ve belgelenir.
2. **Web Pages (`UserController`):** HTML şablonları (`/`, `/about`) ve web arayüzü kullanıcı CRUD rotaları (`/users`, `/users/{id}`).
3. **Health:** Sistemin çalışır durumda olduğunu teyit eden `/api/health` uç noktası.
4. **Test Endpoints:** Temel katmanlı mimari test rotaları (`/hello`, `/hello/{name}`, `/sum/{a}/{b}`).

### 📋 Uç Nokta Listesi

| Metot | Yol (Path) | Etiket (Tag) | Sorumlu Controller | Açıklama | Başarılı Yanıt Kodu & Tipi |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Web Pages | `UserController` | Modern Açılış Sayfası (Landing Page) | `200 OK` (HTML) |
| `GET` | `/about` | Web Pages | - | Proje & Mimari Hakkında Sayfası | `200 OK` (HTML) |
| `GET` | `/users` | Web Pages | `UserController` | Web Mezunlar Listesi Sayfası (Listings / Read) | `200 OK` (HTML) |
| `POST` | `/users` | Web Pages | `UserController` | Web Formu ile Kullanıcı Oluşturma (Creating / Create) | `200 OK` (HTML) |
| `GET` | `/users/{id}` | Web Pages | `UserController` | Web Kullanıcı Detayı | `200 OK` (JSON) |
| `PUT` | `/users/{id}` | Web Pages | `UserController` | Web Kullanıcı Güncelleme | `200 OK` (JSON) |
| `DELETE` | `/users/{id}` | Web Pages | `UserController` | Web Kullanıcı Silme | `200 OK` (JSON) |
| `GET` | `/docs` | - | - | Swagger UI Dokümantasyonu (FastAPI otomatik sağlar) | `200 OK` (Swagger UI) |
| `GET` | `/redoc` | - | - | ReDoc API Dokümantasyonu | `200 OK` (ReDoc) |
| `GET` | `/api/health` | Health | - | Servis sağlık durum kontrolü | `200 OK` (`{"status": "ok"}`) |
| `GET` | `/api/users` | Users | `ApiUserController` | Tüm kullanıcıları listeler | `200 OK` (`UserListApiResponse`) |
| `POST` | `/api/users` | Users | `ApiUserController` | Yeni kullanıcı oluşturur | `201 Created` (`UserApiResponse`) |
| `GET` | `/api/users/{id}` | Users | `ApiUserController` | ID ile tekil kullanıcı getirir (Yoksa 404) | `200 OK` / `404 Not Found` |
| `PUT` | `/api/users/{id}` | Users | `ApiUserController` | Kullanıcıyı tam günceller (Yoksa 404) | `200 OK` / `404 Not Found` |
| `PATCH` | `/api/users/{id}` | Users | `ApiUserController` | Kullanıcıyı kısmi günceller (Yoksa 404) | `200 OK` / `404 Not Found` |
| `DELETE` | `/api/users/{id}` | Users | `ApiUserController` | Kullanıcıyı siler (Yoksa 404) | `200 OK` / `404 Not Found` |
| `GET` | `/hello` | Test Endpoints | - | Genel selamlama mesajı | `200 OK` (`{"message": "Hello, World!"}`) |
| `GET` | `/hello/{name}` | Test Endpoints | - | İsme özel kişiselleştirilmiş selamlama | `200 OK` (`{"message": "Hello, ..."}`) |
| `GET` | `/sum/{a}/{b}` | Test Endpoints | - | İki sayının toplamını hesaplar | `200 OK` (`SumResponse`) |

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
