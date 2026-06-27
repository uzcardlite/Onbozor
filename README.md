# 🛍 OnBozor

O'zbekiston uchun Telegram Web App marketplace — e'lonlar, do'konlar, to'lov, xabarlar va gamification tizimi.

**Version:** 1.0.0

## 📋 Loyiha haqida

OnBozor — Telegram ichida ishlaydigan mahalliy e'lonlar platformasi:
- 📢 E'lon berish (uy-joy, texnika, avto, moto, kiyim)
- 🏪 Rasmiy do'konlar (oylik obuna)
- 💬 Xaridor-sotuvchi xabarlashuvi
- 🔗 Referral tizimi (5% bonus)
- ❤️ Sevimlilar
- ⭐ Reyting va izohlar
- 🚀 Premium promosiyalar (TOP/Featured/Urgent)
- 🏆 Gamification (ball, daraja, medallar)
- 💳 Payme / Click to'lov

## 🏗 Texnik stack

| Qism | Texnologiya |
|------|-------------|
| Bot | python-telegram-bot v20 (async, polling) |
| Backend | FastAPI + SQLAlchemy 2.0 (async) |
| Database | PostgreSQL + asyncpg |
| Frontend | React 18 + Vite + Tailwind CSS |
| State | Zustand + React Query |
| Media | Cloudinary |
| Deploy | Railway (backend+bot) + Vercel (frontend) |
| Monitoring | Sentry |

## 📁 Struktura

```
Onbozor/
├── app/
│   ├── main.py            # FastAPI app
│   ├── bot_runner.py      # Telegram bot (polling)
│   ├── config.py          # Settings
│   ├── database.py        # Async engine
│   ├── dependencies.py    # JWT auth
│   ├── cache.py           # In-memory cache
│   ├── models/            # SQLAlchemy modellar
│   ├── routers/           # API endpointlar
│   ├── services/          # Biznes logika
│   └── handlers/          # Bot handlerlari
├── frontend/
│   └── src/
│       ├── pages/         # Sahifalar (lazy loaded)
│       ├── components/    # Komponentlar
│       ├── api/           # API client
│       ├── store/         # Zustand
│       └── hooks/         # Custom hooks
└── alembic/versions/      # DB migrationlar
```

## 🚀 O'rnatish

### Backend
```bash
pip install -r requirements.txt
cp .env.example .env   # qiymatlarni to'ldiring
alembic upgrade head
uvicorn app.main:app --reload   # API
python -m app.bot_runner        # Bot
```

### Frontend
```bash
cd frontend
npm install
npm run dev      # dev
npm run build    # production
```

## 🔑 Environment variables

`.env.example` ga qarang. Asosiy:
- `BOT_TOKEN`, `DATABASE_URL`, `JWT_SECRET`
- `CHANNEL_ID`, `ADMIN_IDS`
- `PAYME_*`, `CLICK_*`, `CLOUDINARY_*`
- `CORS_ORIGINS`, `SENTRY_DSN`

## 📡 API

To'liq API docs: `/docs` (faqat DEBUG=True da).

Asosiy endpointlar:
- `POST /auth/telegram` — Telegram initData auth → JWT
- `GET/POST /listings` — e'lonlar
- `GET/POST /shops` — do'konlar
- `GET /search` — qidiruv (sort, filter)
- `POST /conversations` — xabarlar
- `POST /payments/initiate` — to'lov
- `GET /gamification/leaderboard` — reyting
- `GET /admin/*` — admin panel (himoyalangan)
- `GET /health` — health check

## 🚢 Deploy

- **Backend**: Railway (`railway.toml`) — bot+API bir process da
- **Frontend**: Vercel (`vercel.json`) — `frontend/` root
- **DB**: Railway PostgreSQL plugin

## 🔒 Xavfsizlik

- JWT auth (30 kun), Telegram initData HMAC tekshiruv
- Rate limiting (auth 5/min, listings 10/hour, search 60/min)
- CORS faqat ruxsat etilgan originlarga
- Admin endpointlar `tg_id` bo'yicha himoyalangan
- Input validation + XSS sanitize (Pydantic)
- SQL injection himoyasi (SQLAlchemy ORM)
