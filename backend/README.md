Backend setup and environment

Required environment variables (.env):

- MONGO_URI — MongoDB connection string. To use MongoDB Compass, copy the connection string from Compass and paste it here (e.g. mongodb://127.0.0.1:27017/mossip_ocr or your Atlas URI).
- JWT_SECRET — A long random string used to sign JSON Web Tokens (keep secret)
- PORT — optional server port (default 5000)

Install dependencies and run:

```ps
cd backend
npm install
npm run dev
```

Endpoints added:
- POST /api/auth/register — register with { email, password, name }
- POST /api/auth/login — login with { email, password }
- GET /api/auth/me — get current user (pass Authorization: Bearer <token>)
- POST /api/documents/save — save OCR result as PDF (Authorization required)
- GET /api/documents — list user's documents (Authorization required)
- DELETE /api/documents/:id — delete user's document (Authorization required)
