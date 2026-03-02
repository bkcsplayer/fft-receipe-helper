<div align="center">
  <img src="docs/banner.png" alt="Receipt Helper Banner" width="100%">
</div>

# 智能小票管家 (Receipt Helper)

<div align="center">
  <h3>✨ AI-Powered Receipt Management System ✨</h3>
  <p>An elegant, full-stack application built to seamlessly digitize your physical receipts using advanced LLM OCR, securely storing original images in Google Drive, and logging structured financial data directly into Google Sheets.</p>
</div>

---

## 🚀 Key Features

*   **📱 Mobile-First Camera Flow**: Instantly take pictures of receipts or upload from your gallery using a responsive, app-like PWA interface.
*   **🧠 AI OCR Parsing**: Powered by `Claude-3.5-Sonnet` (via OpenRouter), it extracts pixel-perfect line-item data, total costs, taxes, store names, and dates — regardless of receipt wrinkles or lighting.
*   **☁️ Google Ecosystem Native**: Doesn't store data on questionable third-party servers. 
    *   **Google Drive**: Uploads receipt images to your personal Drive, automatically organizing them into `YYYY/MM` folders.
    *   **Google Sheets**: Appends a new row for every single item purchased into a clean, auto-generated `YYYY/MM` spreadsheet tab.
*   **📊 Dynamic Data Visualizations**: View your historical spending through elegant charts and lists without ever leaving the app.
*   **🔒 Secure & Private**: Uses basic authentication for entry and OAuth 2.0 to ensure only your Google account is touched.

## 🛠️ Tech Stack

**Frontend**
*   **Framework**: React 18 / Vite
*   **Styling**: Tailwind CSS v4, Custom CSS (Glassmorphism, Dark Mode)
*   **Components**: shadcn/ui, Lucide Icons
*   **Data Viz**: Recharts

**Backend**
*   **Framework**: FastAPI (Python 3.11)
*   **Cloud Integrations**: Google Drive SDK, Google Sheets API
*   **AI Integrations**: OpenRouter API
*   **Data Validation**: Pydantic

**DevOps & Deployment**
*   **Containerization**: Docker & Docker Compose
*   **Hosting**: Nginx Reverse Proxy (Production Ready)

---

## 📸 Screenshots

*(Add screenshots of your application here)*
- Camera / Upload UI
- Parsing Result Table
- History / Flow Tab
- Data Summary Charts

---

## 🏃‍♂️ Local Development

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional, for full stack run)
- A Google Cloud Project with Drive API and Sheets API enabled, and OAuth 2.0 Desktop credentials.

### 1. Google OAuth Setup
1. Create a Google Cloud Project and enable `Google Drive API` & `Google Sheets API`.
2. Configure OAuth Consent Screen and create desktop app credentials.
3. Download the credentials as `client_secret.json` and place it in the project root.
4. Run the local script to authorize and generate your persistent token:
   ```bash
   pip install google-auth-oauthlib google-api-python-client
   python generate_token.py
   ```
   *This will open your browser to log in to Google. Once authenticated, a `token.json` file will be generated.*

### 2. Environment Variables
Copy `.env.example` to `.env` and fill in the required values:
```env
OPENROUTER_API_KEY="your_openrouter_api_key_here"
GOOGLE_DRIVE_ROOT_FOLDER_ID="your_drive_folder_id_here" # Create a folder in your Drive and copy the ID from the URL
GOOGLE_SHEETS_SPREADSHEET_ID="your_sheets_id_here" # Create an empty Google Sheet and copy the ID from the URL
```

### 3. Running with Docker (Recommended)
You can start the entire stack instantly:
```bash
docker-compose up --build
```
- Frontend: `http://localhost:3000`
- Backend API Docs: `http://localhost:8000/docs`

### 4. Running Manually
**Backend:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 🌐 Production Deployment (VPS)

1. Clone the repository to your VPS.
2. Manually upload your `.env` and `token.json` files to the root directory.
3. Update your Frontend API URL depending on your Nginx setup (e.g. relative `/api` path).
4. Run `docker-compose up --build -d`.
5. Configure your main server's Nginx to reverse proxy traffic to port `3000` (Docker's Nginx).

---
*Built with ❤️ utilizing the power of LLMs and Modern Web Technologies.*
