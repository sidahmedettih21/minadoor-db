#!/bin/bash
OUTPUT="minadoor_super_report.md"
echo "# MINADOOR TRAVEL DB – FULL STATE REPORT" > $OUTPUT
echo "Generated: $(date)" >> $OUTPUT
echo "" >> $OUTPUT

echo "## 1. Project Structure" >> $OUTPUT
echo '```' >> $OUTPUT
find . -not -path '*/\.*' -not -path '*/node_modules/*' -not -path '*/__pycache__/*' -not -path '*/backup_*' | sort >> $OUTPUT
echo '```' >> $OUTPUT
echo "" >> $OUTPUT

echo "## 2. Docker Environment" >> $OUTPUT
echo "### docker-compose.yml" >> $OUTPUT
echo '```yaml' >> $OUTPUT
cat docker-compose.yml >> $OUTPUT
echo '```' >> $OUTPUT
echo "" >> $OUTPUT
echo "### .env (sanitised)" >> $OUTPUT
echo '```' >> $OUTPUT
cat .env | sed 's/=.*/=***REDACTED***/' >> $OUTPUT
echo '```' >> $OUTPUT
echo "" >> $OUTPUT

echo "## 3. Backend Core Files" >> $OUTPUT
for f in backend/app/main.py backend/app/config.py backend/app/database.py backend/app/models.py backend/app/schemas.py backend/app/auth.py backend/app/dependencies.py; do
  if [ -f "$f" ]; then
    echo "### $(basename $f)" >> $OUTPUT
    echo '```python' >> $OUTPUT
    cat $f >> $OUTPUT
    echo '```' >> $OUTPUT
    echo "" >> $OUTPUT
  fi
done

echo "## 4. Routers" >> $OUTPUT
for f in backend/app/routers/*.py; do
  echo "### $(basename $f)" >> $OUTPUT
  echo '```python' >> $OUTPUT
  cat $f >> $OUTPUT
  echo '```' >> $OUTPUT
  echo "" >> $OUTPUT
done

echo "## 5. Services & Utils" >> $OUTPUT
for f in backend/app/services/*.py backend/app/utils/*.py; do
  if [ -f "$f" ]; then
    echo "### $(basename $f)" >> $OUTPUT
    echo '```python' >> $OUTPUT
    cat $f >> $OUTPUT
    echo '```' >> $OUTPUT
    echo "" >> $OUTPUT
  fi
done

echo "## 6. Migration" >> $OUTPUT
echo "### alembic/versions/001_initial.py" >> $OUTPUT
echo '```python' >> $OUTPUT
cat backend/alembic/versions/001_initial.py >> $OUTPUT 2>/dev/null || echo "File not found" >> $OUTPUT
echo '```' >> $OUTPUT
echo "" >> $OUTPUT

echo "## 7. Frontend" >> $OUTPUT
echo "### index.html" >> $OUTPUT
echo '```html' >> $OUTPUT
cat frontend/index.html >> $OUTPUT
echo '```' >> $OUTPUT
echo "" >> $OUTPUT
echo "### app.js" >> $OUTPUT
echo '```javascript' >> $OUTPUT
cat frontend/js/app.js >> $OUTPUT
echo '```' >> $OUTPUT
echo "" >> $OUTPUT
echo "### app.css" >> $OUTPUT
echo '```css' >> $OUTPUT
cat frontend/css/app.css >> $OUTPUT
echo '```' >> $OUTPUT
echo "" >> $OUTPUT
echo "### Locales" >> $OUTPUT
for f in frontend/locales/*.json; do
  echo "#### $(basename $f)" >> $OUTPUT
  echo '```json' >> $OUTPUT
  cat $f >> $OUTPUT
  echo '```' >> $OUTPUT
  echo "" >> $OUTPUT
done

echo "## 8. Docker & Deployment" >> $OUTPUT
echo "### Dockerfile (backend)" >> $OUTPUT
echo '```dockerfile' >> $OUTPUT
cat backend/Dockerfile >> $OUTPUT
echo '```' >> $OUTPUT
echo "" >> $OUTPUT
echo "### entrypoint.sh" >> $OUTPUT
echo '```bash' >> $OUTPUT
cat backend/entrypoint.sh >> $OUTPUT
echo '```' >> $OUTPUT
echo "" >> $OUTPUT

echo "## 9. Live System State" >> $OUTPUT
echo "### Running Containers" >> $OUTPUT
echo '```' >> $OUTPUT
sudo docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null >> $OUTPUT || echo "Docker not accessible" >> $OUTPUT
echo '```' >> $OUTPUT
echo "" >> $OUTPUT
echo "### API Container Logs (last 30 lines)" >> $OUTPUT
echo '```' >> $OUTPUT
sudo docker logs minadoordb_api_1 --tail 30 2>/dev/null >> $OUTPUT || echo "API container not running" >> $OUTPUT
echo '```' >> $OUTPUT
echo "" >> $OUTPUT
echo "### Frontend Container Logs (last 10 lines)" >> $OUTPUT
echo '```' >> $OUTPUT
sudo docker logs minadoordb_frontend_1 --tail 10 2>/dev/null >> $OUTPUT || echo "Frontend container not running" >> $OUTPUT
echo '```' >> $OUTPUT
echo "" >> $OUTPUT
echo "## 10. API Quick Test" >> $OUTPUT
echo '```' >> $OUTPUT
curl -s http://localhost:8000/health 2>/dev/null || echo "API unreachable" >> $OUTPUT
echo "" >> $OUTPUT
curl -s http://localhost:8000/api/v1/travel-types/ 2>/dev/null || echo "Travel types endpoint unreachable" >> $OUTPUT
echo '```' >> $OUTPUT
echo "" >> $OUTPUT

echo "## 11. Known Issues" >> $OUTPUT
echo "1. API container currently exits because entrypoint.sh references 'gunicorn' which is not installed. Fix: replace with 'uvicorn app.main:app --host 0.0.0.0 --port 8000'."
echo "2. Frontend Content Security Policy blocks external CDN scripts (Tailwind, Alpine, HTMX, Google Fonts). Fixed with permissive CSP header."
echo "3. Auth disabled via dependencies.py – get_current_user returns hardcoded admin. This must be re-enabled for production."
echo "4. Sidebar toggle button missing on mobile in some languages due to logic error in index.html (fixed)."
echo "5. Import/export backend not yet implemented; endpoints are stubs." >> $OUTPUT

echo "" >> $OUTPUT
echo "## 12. Enhancement Requests" >> $OUTPUT
echo "- Build a complete, production-ready frontend that communicates with the existing API."
echo "- Frontend should include: dashboard, client CRUD, Excel import with Arabic header detection, export with logo and A4 PDF, multi-language UI (EN/FR/AR)."
echo "- All existing API endpoints must be fully utilized."
echo "- The frontend should be self-contained, using Alpine.js + HTMX + Tailwind CSS, and served via Nginx."
echo "- Ensure CSP headers allow external CDN scripts and fonts."
echo "- Provide clear instructions to replace the current frontend folder with the new build." >> $OUTPUT

echo "Report saved to $OUTPUT"
