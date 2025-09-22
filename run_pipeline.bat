@echo off
REM DVC Pipeline Execution Script for Windows

echo 🚀 Starting PDF Extraction Pipeline
echo ==================================

REM Check if DVC is installed
dvc --version >nul 2>&1
if errorlevel 1 (
    echo ❌ DVC is not installed. Please install with: pip install dvc dvc-s3
    pause
    exit /b 1
)

REM Activate virtual environment if not already active
if "%VIRTUAL_ENV%"=="" (
    echo ⚠️  Virtual environment not detected. Activating...
    call .venv\Scripts\activate.bat
)

REM Validate configuration
echo 📋 Validating configuration...
python -c "import yaml; config = yaml.safe_load(open('config/extraction_config.yaml', 'r')); print('✅ Configuration file is valid')"
if errorlevel 1 (
    echo ❌ Configuration validation failed
    pause
    exit /b 1
)

REM Check for input data
if not exist "data\raw\pdf" (
    echo ⚠️  Directory data\raw\pdf does not exist
    echo    Run the download stage first or add PDF files manually
    pause
)

REM Show pipeline structure
echo 📊 Pipeline Structure:
dvc dag

REM Check pipeline status
echo 🔍 Checking pipeline status...
dvc status

echo.
echo Choose execution mode:
echo 1) Run full pipeline (dvc repro)
echo 2) Run specific stage
echo 3) Force rebuild all stages
echo 4) Show pipeline metrics
echo 5) Exit

set /p choice="Enter choice (1-5): "

if "%choice%"=="1" (
    echo 🔄 Running full pipeline...
    dvc repro
    if errorlevel 1 (
        echo ❌ Pipeline failed
        pause
        exit /b 1
    )
    echo ✅ Pipeline completed successfully!
) else if "%choice%"=="2" (
    echo Available stages:
    echo - download
    echo - parse
    echo - tables
    echo - layout
    echo - docling
    echo - metadata
    echo - compare
    echo - export
    set /p stage="Enter stage name: "
    echo 🔄 Running stage: %stage%
    dvc repro %stage%
) else if "%choice%"=="3" (
    echo 🔄 Force rebuilding all stages...
    dvc repro --force
    echo ✅ Pipeline rebuilt successfully!
) else if "%choice%"=="4" (
    echo 📈 Pipeline Metrics:
    if exist "data\analysis\extraction_metrics.json" (
        dvc metrics show
        dvc plots show
    ) else (
        echo No metrics available yet. Run the pipeline first.
    )
) else if "%choice%"=="5" (
    echo 👋 Goodbye!
    exit /b 0
) else (
    echo ❌ Invalid choice
    pause
    exit /b 1
)

REM Show final status
echo.
echo 📊 Final Pipeline Status:
dvc status

echo.
echo 🎉 Pipeline execution completed!
echo Check data\parsed\ for extraction results
echo Check reports\ for final documentation

pause