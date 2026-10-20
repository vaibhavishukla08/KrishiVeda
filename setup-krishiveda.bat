@echo off
REM One-time setup: installs Python and Node packages and trains the crop model.
REM Needs Python 3.11+ and Node.js 20+ installed. Safe to run again.
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creating Python virtual environment...
  python -m venv .venv || goto :error
)

echo Installing backend packages (PyTorch is a large download, please wait)...
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\pip install -r backend\requirements.txt -r backend\requirements-ml.txt || goto :error

echo Installing frontend packages...
pushd frontend
call npm install || (popd & goto :error)
popd

if not exist "ml\models\crop_recommender.joblib" (
  echo Training crop recommendation model...
  .venv\Scripts\python ml\datasets\fetch_crop_dataset.py || goto :error
  .venv\Scripts\python ml\training\train_crop_model.py || goto :error
)

if not exist "ml\models\disease_cnn.pt" (
  echo.
  echo [i] Disease model not found. To create it (about 1 hour on a laptop CPU), run:
  echo     .venv\Scripts\python ml\datasets\fetch_plantvillage_subset.py --per-class 250
  echo     .venv\Scripts\python ml\training\train_disease_cnn.py --head-epochs 1 --finetune-epochs 3
)

echo.
echo Setup complete. Double-click start-krishiveda.bat to run the app.
pause
exit /b 0

:error
echo.
echo [!] Setup failed. Read the message above, fix it, and run this file again.
pause
exit /b 1
