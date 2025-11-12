# =====================================================================
# 🚀 Quick Launcher: Run Backend (FastAPI) + Frontend (Vite) together
# =====================================================================

# 🧠 Change these paths according to your folder locations
$backendPath = "C:\Users\aryan\Downloads\mini-project-main\Backend"
$frontendPath = "C:\Users\aryan\Downloads\mini-project-main\chatbot"

# ===============================================================
# 🟢 Start Backend (FastAPI) in NEW PowerShell window
# ===============================================================
Write-Host "`n🚀 Starting FastAPI backend server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "
cd `"$backendPath`";
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force;
.\venv\Scripts\Activate.ps1;
python -m uvicorn main:app --reload
" -WindowStyle Normal

# ===============================================================
# 🔵 Start Frontend (Vite + React) in NEW PowerShell window
# ===============================================================
Write-Host "`n🌐 Starting Vite frontend server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "
cd `"$frontendPath`";
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force;
npm run dev
" -WindowStyle Normal

# ===============================================================
# ✅ Final message
# ===============================================================
Write-Host "`n✨ Both servers launched successfully!" -ForegroundColor Green
Write-Host "👉 Backend:  http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "👉 Frontend: http://localhost:5173" -ForegroundColor Yellow
Write-Host "`nYou can close either window independently when done." -ForegroundColor DarkGray
