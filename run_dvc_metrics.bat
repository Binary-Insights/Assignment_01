@echo off
REM DVC Metrics Validation Pipeline Runner
REM Windows Batch Script for automated metrics testing
REM Date: September 25, 2025

echo ======================================
echo DVC METRICS VALIDATION PIPELINE
echo ======================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    exit /b 1
)

REM Check if we're in the right directory
if not exist "scripts\dvc_metrics_pipeline.py" (
    echo ERROR: dvc_metrics_pipeline.py not found. Make sure you're in the project root directory.
    exit /b 1
)

REM Parse command line arguments
set COMMIT_FLAG=
set QUIET_FLAG=
set THRESHOLDS_ONLY=
set REGRESSION_ONLY=

:parse_args
if "%1"=="" goto run_pipeline
if "%1"=="--commit" set COMMIT_FLAG=--commit
if "%1"=="--quiet" set QUIET_FLAG=--quiet
if "%1"=="--thresholds-only" set THRESHOLDS_ONLY=--thresholds-only
if "%1"=="--regression-only" set REGRESSION_ONLY=--regression-only
if "%1"=="--help" goto show_help
shift
goto parse_args

:show_help
echo Usage: run_dvc_metrics.bat [OPTIONS]
echo.
echo OPTIONS:
echo   --commit              Commit current metrics as new baseline
echo   --quiet               Reduce output verbosity
echo   --thresholds-only     Run only threshold validation tests
echo   --regression-only     Run only regression detection tests
echo   --help                Show this help message
echo.
echo Examples:
echo   run_dvc_metrics.bat                    # Run full pipeline
echo   run_dvc_metrics.bat --thresholds-only # Only validate thresholds
echo   run_dvc_metrics.bat --commit          # Run pipeline and commit baseline
exit /b 0

:run_pipeline
echo Running DVC Metrics Pipeline...
echo.

REM Run the pipeline
python scripts\dvc_metrics_pipeline.py %COMMIT_FLAG% %QUIET_FLAG% %THRESHOLDS_ONLY% %REGRESSION_ONLY%

REM Check exit code
if errorlevel 1 (
    echo.
    echo ======================================
    echo PIPELINE FAILED
    echo ======================================
    exit /b 1
) else (
    echo.
    echo ======================================
    echo PIPELINE COMPLETED SUCCESSFULLY
    echo ======================================
    exit /b 0
)