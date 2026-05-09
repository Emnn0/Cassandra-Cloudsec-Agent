# Cassandra CloudSec Agent

<p align="center">
     <strong>AI-powered firewall log analysis platform</strong><br/>
     Upload your WAF logs. Get actionable threat intelligence in 60 seconds.
   </p>

   <p align="center">
     <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white" alt="Python"/>
     <img src="https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi&logoColor=white" alt="FastAPI"/>
     <img src="https://img.shields.io/badge/Next.js-14-black?logo=nextdotjs&logoColor=white" alt="Next.js"/>
     <img src="https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white" alt="PostgreSQL"/>
     <img src="https://img.shields.io/badge/Claude-Sonnet%204.5-D4A27F?logo=anthropic&logoColor=white" alt="Claude"/>
     <img src="https://img.shields.io/badge/License-MIT-green" alt="License"/>
   </p>

   ---

Yapay zeka destekli güvenlik log analiz platformu. WAF ve sunucu loglarını yükle, otomatik tehdit analizi al, PDF raporu indir.

## Ekran Görüntüleri

### Ana Sayfa
![Cassandra Landing Page](docs/screenshots/01-landing-page.png)

### Tehdit Analiz Paneli
![Analiz Detay Sayfası](docs/screenshots/02-analysis-detail.png)

### PDF Tehdit Raporu
![PDF Threat Analysis Report](docs/screenshots/03-pdf-report.png)

---
## Özellikler

- **Çoklu log formatı desteği** — Cloudflare WAF, Cloudflare HTTP, LiteSpeed, Apache, Nginx ve genel metin logları
- **Otomatik heuristik analiz** — IP dominansı, anormal trafik, eylem dağılımı
- **Yapay zeka tehdit raporu** — Claude ile OWASP kategorize edilmiş tehdit tespiti (Türkçe)
- **PDF raporu** — Profesyonel tehdit raporu indirme
- **Gerçek zamanlı ilerleme** — Analiz adımları canlı takip
- **Karanlık tema** — Siber güvenlik odaklı UI

## Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| Backend | Python 3.11, FastAPI, Celery, SQLAlchemy 2.0 |
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Veritabanı | PostgreSQL 16 |
| Kuyruk | Redis 7 |
| LLM | Anthropic Claude (claude-sonnet-4-5) |
| PDF | WeasyPrint |
| Altyapı | Docker Compose |

## Kurulum

### Gereksinimler

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/macOS/Linux)
- Anthropic API anahtarı → [console.anthropic.com](https://console.anthropic.com)

### Adım 1: Depoyu klonla

```bash
git clone https://github.com/kullanici-adi/cassandra-cloudsec-agent.git
cd cassandra-cloudsec-agent
```

### Adım 2: Ortam değişkenlerini ayarla

```bash
cp .env.example .env.dev
```

`.env.dev` dosyasını aç ve en az şu alanı doldur:

```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxx
```

> **Not:** Clerk ve AWS S3 olmadan da çalışır. Clerk boş bırakılırsa kimlik doğrulama devre dışı kalır. S3 boş bırakılırsa dosyalar lokal olarak `/tmp` altında saklanır.

### Adım 3: Docker ile başlat

```bash
docker compose --env-file .env.dev up --build
```

İlk seferinde image'lar indirildiği için 3-5 dakika sürebilir.

### Adım 4: Tarayıcıda aç

| Servis | URL |
|--------|-----|
| Uygulama | http://localhost:3000 |
| API Docs | http://localhost:8000/docs |
| DB Yönetimi | http://localhost:8080 |

---

## Kullanım

1. **http://localhost:3000** adresine git
2. **"Log Dosyası Yükle"** butonuna tıkla
3. Desteklenen bir log dosyası seç (`.ndjson`, `.log`, `.txt`)
4. Analiz otomatik başlar — adımları canlı izleyebilirsin
5. Tamamlanınca **tehdit raporu** ve **PDF** indir

### Desteklenen Log Formatları

| Format | Örnek Dosya |
|--------|-------------|
| Cloudflare WAF | `firewall_events.ndjson` |
| Cloudflare HTTP | `http_logs.ndjson` |
| LiteSpeed / Apache | `access.log`, `error.log` |
| Genel metin | `server.log`, `app.log` |

---

## Geliştirme

### Servisleri ayrı başlatma

```bash
# Sadece altyapı (DB + Redis)
docker compose --env-file .env.dev up postgres redis -d

# Backend geliştirme (hot-reload)
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload

# Frontend geliştirme (hot-reload)
cd frontend
npm install
npm run dev
```

### Veritabanı migration

```bash
docker exec loglens_backend alembic upgrade head
```

### Logları izle

```bash
# Tüm servisler
docker compose --env-file .env.dev logs -f

# Sadece Celery (analiz işçisi)
docker logs loglens_celery -f

# Sadece backend
docker logs loglens_backend -f
```

---

## Proje Yapısı

```
cassandra-cloudsec-agent/
├── backend/                    # FastAPI + Celery uygulaması
│   ├── app/
│   │   ├── api/v1/             # REST endpoint'leri
│   │   ├── services/
│   │   │   ├── parsers/        # Log format parser'ları
│   │   │   ├── llm/            # LLM provider katmanı
│   │   │   ├── heuristics.py   # İstatistiksel analiz
│   │   │   └── reasoning.py    # LLM tehdit analizi
│   │   ├── tasks/analyze.py    # Celery analiz görevi
│   │   └── templates/          # Jinja2 + PDF şablonları
│   └── alembic/                # DB migration'ları
├── frontend/                   # Next.js 14 uygulaması
│   └── src/app/
│       ├── dashboard/          # Ana panel
│       └── analyses/[id]/      # Analiz detay sayfası
├── docker-compose.yml
├── .env.example                # Ortam değişkenleri şablonu
└── README.md
```

---

## Katkı

1. Fork et
2. Feature branch oluştur: `git checkout -b feature/yeni-ozellik`
3. Commit at: `git commit -m "feat: yeni özellik açıklaması"`
4. Push et: `git push origin feature/yeni-ozellik`
5. Pull request aç

---
## Bu Proje Hakkında

Bu proje **tek başına bir öğrenme projesi olarak** geliştirildi. Modern bir SaaS uygulamasının uçtan uca nasıl kurulduğunu, hangi parçalardan oluştuğunu ve nasıl deploy edildiğini öğrenmek için yapıldı.

### Bu projede öğrenilenler

- Üç katmanlı async mimari (FastAPI + Celery + Next.js)
- LLM provider abstraction ve `tool_use` ile structured output
- PII redaction ve KVKK/GDPR uyumlu veri işleme
- Streaming parser pattern (büyük dosyaları belleğe yüklemeden işleme)
- Docker Compose ile multi-service orchestration (healthcheck, migration, networks)
- SQLAlchemy 2.0 async syntax + Alembic migration
- Caddy ile otomatik TLS sertifikası
- WeasyPrint ile profesyonel PDF rapor üretimi

### Mimari kararlar

| Karar | Sebep |
|-------|-------|
| Celery + Redis | LLM çağrıları 30-90 saniye sürebilir, HTTP request bunu bekleyemez |
| LLM Provider Abstraction | Vendor lock-in'den kaçınmak; Claude/GPT/Gemini arası geçiş |
| PII Redaction | Müşteri loglarındaki IP/email LLM'e gitmeden önce maskelenmeli |
| Async SQLAlchemy 2.0 | I/O-bound DB operasyonlarında thread'ler bloklanmasın |
| Caddy yerine Nginx değil | Otomatik Let's Encrypt, çok daha az config |

---
## Lisans

MIT License — Muhammed Emin Berberoğlu
---

<p align="center">
  <strong>Muhammed Emin Berberoğlu</strong> tarafından geliştirildi<br/>
  <a href="https://github.com/Emnn0">GitHub</a> · <a href="https://www.linkedin.com/in/muhammed-emin-berbero%C4%9Flu-88210b388">LinkedIn</a>
</p>
