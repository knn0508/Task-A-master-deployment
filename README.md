# RAG Chatbot System v2.0

Modern, təhlükəsiz və modulyar RAG (Retrieval-Augmented Generation) chatbot sistemi. Flask backend və React frontend ilə qurulub.

## 🛠️ Quraşdırma

### Backend Setup

1. **Python mühitini yaradın:**
```bash
cd backend
#python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Dependencies quraşdırın:**
```bash
pip install -r requirements.txt
```

3. **AI env dəyişənlərini təyin edin (`backend/.env`):**
- `OPENAI_API_KEY=...`
- `LLM_MODEL=gpt-5.2`

4. **Backend-i başladın:**
```bash
python simple_app.py
```

### Frontend Setup

1. **Dependencies quraşdırın:**
```bash
cd frontend
npm install
```
2. **Frontend-i başladın:**
```bash
npm run start
```

## 📝 API Documentation

### Authentication Endpoints

- `POST /api/auth/register` - Yeni istifadəçi qeydiyyatı
- `POST /api/auth/login` - İstifadəçi girişi
- `POST /api/auth/refresh` - Access token yeniləmə
- `POST /api/auth/logout` - Çıxış
- `GET /api/auth/me` - Cari istifadəçi məlumatı

### Document Endpoints

- `GET /api/documents` - Sənədlərin siyahısı
- `POST /api/documents` - Yeni sənəd yükləmə (admin only)
- `GET /api/documents/:id` - Sənəd detalları
- `DELETE /api/documents/:id` - Sənəd silmə (admin only)
- `GET /api/documents/:id/download` - Sənəd endirmə
- `POST /api/documents/:id/reprocess` - Sənədi yenidən işləmə

### Chat Endpoints

- `POST /api/chat/ask` - Sual vermə
- `GET /api/chat/conversations` - Söhbətlərin siyahısı
- `GET /api/chat/conversations/:id` - Söhbət mesajları
- `DELETE /api/chat/conversations/:id` - Söhbət silmə
- `PUT /api/chat/conversations/:id/rename` - Söhbət adını dəyişmə

## 🎯 İstifadə

1. **Sistemə giriş:** Default admin hesabı - `admin / admin123`
2. **Sənəd yüklə:** Admin panel vasitəsilə sənəd yükləyin
3. **Sual verin:** Yüklənmiş sənəd haqqında suallar verin
4. **Cavab alın:** AI sizin suallarınıza sənəd məzmunu əsasında cavab verir

## 📄 License

MIT License

## 👥 Author

RAG Chatbot Team

## 🆘 Support

Hər hansı problem və ya sual üçün issue açın və ya əlaqə saxlayın.

## ▲ Vercel Deployment

Bu repo `frontend` (Vite) + `backend` (Flask API) üçün Vercel-ə uyğunlaşdırılıb.

### 1) Project import
- Repo-nu Vercel-ə import edin (root: layihə kökü).
- `vercel.json` avtomatik olaraq frontend build + Python API route-larını idarə edir.

### 2) Vercel Environment Variables
Vercel Dashboard → Project Settings → Environment Variables bölməsində əlavə edin:

- `OPENAI_API_KEY`
- `LLM_MODEL` (məs: `gpt-5.2`)
- `EMBEDDING_MODEL` (məs: `text-embedding-3-small`)
- `SECRET_KEY`
- `CORS_ORIGINS` (məs: `https://your-project.vercel.app`)

### 3) Deploy
- `main` branch push etdikdə Vercel avtomatik deploy edəcək.

### 4) Vacib qeydlər
- Vercel Python funksiyaları serverless və ephemeral-dir; lokal fayl sistemi (`documents`, `chroma_db`, sqlite) qalıcı deyil.
- Production üçün qalıcı storage/database (məs: Postgres + object storage) tövsiyə olunur.