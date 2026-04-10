# Diagnosing AI

AI-powered diagnostic web application.

## Project Structure

```
diagnosing-ai/
├── backend/          Flask REST API + AI engine
│   ├── app.py        Entry point
│   ├── ai_engine.py  NER, resolver, RF model
│   ├── routes/
│   │   ├── auth.py       Register, login, logout, /me
│   │   └── diagnosis.py  Symptoms, note, history, confirm
│   ├── migration.sql     Run once in SQL Server
│   ├── requirements.txt
│   └── .env.example  → copy to .env and fill in
│
└── frontend/         React SPA
    ├── src/
    │   ├── App.js          Router + protected routes
    │   ├── api/
    │   │   ├── client.js       Axios + JWT interceptor
    │   │   └── AuthContext.js  Global auth state
    │   ├── pages/
    │   │   ├── Auth.js      Login + Register
    │   │   ├── Dashboard.js
    │   │   ├── Diagnose.js  Symptom checklist
    │   │   ├── Note.js      Clinical note NER
    │   │   └── History.js   Diagnosis history
    │   └── styles/
    └── public/
```

---

## Local Setup

### 1. Database
Run `backend/migration.sql` in SQL Server Management Studio.

### 2. Backend

```bash
cd backend

# Copy env template
copy .env.example .env
# Edit .env — add HF_TOKEN, JWT_SECRET_KEY, DB_CONNECTION

# Install dependencies
pip install -r requirements.txt

# Install gunicorn for production
pip install gunicorn

# Run
python app.py
# Server starts at http://localhost:5000
```

### 3. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local with backend URL
echo "REACT_APP_API_URL=http://localhost:5000/api" > .env.local

# Run
npm start
# App opens at http://localhost:3000
```

---

## Deployment (Railway)

### Backend
1. Push `backend/` folder to a GitHub repo
2. Go to railway.app → New Project → Deploy from GitHub
3. Select the repo
4. Add environment variables in Railway dashboard:
   - `HF_TOKEN`
   - `JWT_SECRET_KEY`  (generate a long random string)
   - `DB_CONNECTION`   (your SQL Server connection string)
5. Railway auto-deploys on every push

### Frontend (Vercel)
1. Push `frontend/` folder to a GitHub repo
2. Go to vercel.com → New Project → Import repo
3. Add environment variable:
   - `REACT_APP_API_URL` = your Railway backend URL (e.g. `https://your-app.railway.app/api`)
4. Deploy

---

## API Endpoints

| Method | Endpoint                          | Auth | Description                  |
|--------|-----------------------------------|------|------------------------------|
| POST   | /api/auth/register                | —    | Create account               |
| POST   | /api/auth/login                   | —    | Login, returns JWT token     |
| POST   | /api/auth/logout                  | JWT  | Logout                       |
| GET    | /api/auth/me                      | JWT  | Get current user             |
| GET    | /api/diagnosis/symptoms           | JWT  | List all symptoms            |
| POST   | /api/diagnosis/symptoms           | JWT  | Predict from symptom list    |
| POST   | /api/diagnosis/note               | JWT  | Predict from clinical note   |
| GET    | /api/diagnosis/history            | JWT  | Patient's diagnosis history  |
| PATCH  | /api/diagnosis/<id>/confirm       | JWT  | Confirm/reject a diagnosis   |
| GET    | /api/health                       | —    | Health check                 |
