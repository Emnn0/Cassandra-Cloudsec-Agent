# LogLens — Production Notes & Deployment Guide

## Production Checklist

### Infrastructure
- [ ] Hetzner CX31 (or higher) provisioned, Ubuntu 22.04
- [ ] Run `infra/server-setup.sh` as root on fresh server
- [ ] Copy SSH public key to server (`~/.ssh/authorized_keys`)
- [ ] Domain DNS A record pointing to server IP
- [ ] GitHub secrets set (see CI/Deploy section below)

### HTTPS / Caddy
- [ ] `DOMAIN` env var set in `.env` on server (e.g. `api.yourdomain.com`)
- [ ] Caddy auto-provisions Let's Encrypt cert on first start
- [ ] HTTPS smoke test: `curl -I https://api.yourdomain.com/api/v1/health`

### Clerk (Auth)
- [ ] Create production instance at [dashboard.clerk.com](https://dashboard.clerk.com)
- [ ] Set `CLERK_SECRET_KEY=sk_live_...` and `CLERK_PUBLISHABLE_KEY=pk_live_...` in server `.env`
- [ ] Set same keys in Vercel environment variables for frontend
- [ ] Configure allowed origins in Clerk dashboard to include your Vercel URL

### AWS S3
- [ ] Create bucket `loglens-uploads-prod` in your AWS region
- [ ] Create bucket `loglens-backups-prod` (private, versioning on)
- [ ] Apply CORS policy from `infra/s3-cors.json` to uploads bucket:
  ```bash
  aws s3api put-bucket-cors \
    --bucket loglens-uploads-prod \
    --cors-configuration file://infra/s3-cors.json
  ```
- [ ] Create IAM user with policy:
  - `s3:PutObject`, `s3:GetObject` on `loglens-uploads-prod/*`
  - `s3:PutObject`, `s3:ListBucket` on `loglens-backups-prod/*`
- [ ] Block public access on both buckets

### Anthropic
- [ ] `ANTHROPIC_API_KEY=sk-ant-...` set in server `.env` and Celery env
- [ ] Set spend limit in Anthropic console to avoid surprise bills

### Database
- [ ] Migrations run automatically on deploy (`alembic upgrade head`)
- [ ] Daily backup cron installed via `server-setup.sh`
- [ ] Test restore: `aws s3 cp s3://loglens-backups-prod/postgres/latest.sql.gz - | gunzip | psql ...`

### Sentry
- [ ] Create project at [sentry.io](https://sentry.io)
- [ ] Set `SENTRY_DSN` in server `.env`
- [ ] Set `NEXT_PUBLIC_SENTRY_DSN` in Vercel environment variables
- [ ] Configure alert rules: error rate > 5/min → email + Slack

### Rate Limiting
- [ ] `slowapi` configured: 200 req/min default per IP
- [ ] Upload endpoint: 10 uploads/hour per IP (add `@limiter.limit("10/hour")` to uploads router)
- [ ] Analysis endpoint: 20 analyses/day per user

### Vercel (Frontend)
- [ ] Import repo at [vercel.com/import](https://vercel.com/import)
- [ ] Set root directory to `frontend/`
- [ ] Environment variables in Vercel dashboard:
  - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...`
  - `NEXT_PUBLIC_API_URL=https://api.yourdomain.com`
  - `NEXT_PUBLIC_SENTRY_DSN=https://...`
  - `CLERK_SECRET_KEY=sk_live_...` (for SSR auth)

---

## GitHub Secrets Required

| Secret | Description |
|---|---|
| `PROD_SSH_HOST` | Server IP or hostname |
| `PROD_SSH_USER` | SSH user (e.g. `ubuntu`) |
| `PROD_SSH_KEY` | Private SSH key (PEM format) |
| `PROD_ENV_FILE` | Full contents of server `.env` file |

---

## Local → Production Deploy Flow

```bash
# 1. Provision server (one-time)
ssh root@YOUR_IP "curl -sL https://raw.githubusercontent.com/.../server-setup.sh | bash"

# 2. Create .env on server
scp .env.production ubuntu@YOUR_IP:/opt/loglens/.env

# 3. First deploy
ssh ubuntu@YOUR_IP "cd /opt/loglens && docker compose -f docker-compose.prod.yml up -d"

# 4. Subsequent deploys happen automatically via GitHub Actions on push to main
```

---

## Smoke Test — Full Flow

After deployment, verify the entire pipeline end-to-end:

1. **Sign up**: `https://app.yourdomain.com/sign-up` → create account
2. **Upload**: Upload a real Cloudflare NDJSON log file (at least 100 events)
3. **Monitor**: Watch analysis status at `/analyses/[id]` — should reach `completed` in ~60–90 seconds
4. **PDF**: Click "Download PDF" — verify it opens with all 5 sections
5. **API health**: `curl https://api.yourdomain.com/api/v1/health` → `{"status": "ok"}`

---

## Known Rough Edges & TODO

### Performance
- **Large files (>50MB)**: Celery task can be slow. Consider chunked streaming parser instead of loading entire file.
- **PDF generation on Playwright**: WeasyPrint is preferred in production (GTK available in Docker). Playwright fallback adds ~3s.
- **No pagination on analysis list**: Dashboard loads only first 20 analyses; add infinite scroll for power users.

### Security
- **S3 presigned URL expiry**: Currently 1 hour. Reduce to 15 minutes for production uploads.
- **No file type validation**: Only size checked client-side. Add server-side MIME sniffing on S3 trigger.
- **Admin endpoints**: None exist yet. Needed for support/ops to inspect analyses.

### Reliability
- **Celery retry**: Max 2 retries with 30s delay. If Anthropic API is down, analyses fail. Add longer backoff.
- **No dead letter queue**: Failed Celery tasks are silently dropped after retries. Add Flower dashboard for visibility.
- **Database connection pool**: Default asyncpg pool size is 5. Under load, increase to 20 in `config.py`.

### UX
- **No email notifications**: User doesn't know when analysis is done. Add Clerk webhook → email via SendGrid.
- **No analysis deletion**: Users can't delete past analyses or log files (or their S3 objects).
- **Mobile**: Dashboard and analysis detail are not optimised for screens < 375px.

### Cost Optimisation
- **Anthropic token usage**: Large log files send large statistical summaries to Claude. Add token budget limiting.
- **S3 lifecycle rules**: Add 30-day expiry on raw log files to reduce storage costs.

---

## Useful Commands

```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f celery_worker

# Manual backup
docker compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U loglens loglens | gzip > backup_manual.sql.gz

# Run migrations
docker compose -f docker-compose.prod.yml run --rm backend \
  python -m alembic upgrade head

# Scale Celery workers
docker compose -f docker-compose.prod.yml up -d --scale celery_worker=3

# Caddy reload (after Caddyfile change)
docker compose -f docker-compose.prod.yml exec caddy caddy reload --config /etc/caddy/Caddyfile
```