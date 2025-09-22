# DVC Pipeline Troubleshooting Guide

## Quick Commands to Test Pipeline

```bash
# 1. Check pipeline structure
dvc dag

# 2. Check what needs to run
dvc status

# 3. Test without executing
dvc repro --dry

# 4. Run single stage
dvc repro parse

# 5. Run full pipeline
dvc repro
```

## Common Issues and Solutions

### Issue 1: "Stage 'X' is not found"
**Problem**: Stage name in dvc.yaml doesn't match command
**Solution**: Check dvc.yaml for correct stage names

### Issue 2: "Dependency not found"
**Problem**: Script file or input data missing
**Solution**: 
```bash
# Check if files exist
ls src/pdfplumber_tess_extractor.py
ls data/raw/pdf/
```

### Issue 3: "Command failed"
**Problem**: Python script has errors
**Solution**: Test script individually:
```bash
python src/pdfplumber_tess_extractor.py
```

### Issue 4: "Permission denied"
**Problem**: Scripts not executable
**Solution**:
```bash
chmod +x run_pipeline.sh  # Linux/Mac
```

### Issue 5: "Output already exists"
**Problem**: Previous run left files
**Solution**:
```bash
dvc repro --force  # Force rebuild
```

## Step-by-Step Pipeline Testing

### Test Individual Components First:
```bash
# Test basic extractor
python src/pdfplumber_tess_extractor.py

# Test hybrid extractor
python src/hybrid_pdf_extractor.py

# Test metadata generator
python src/metadata_extractor.py
```

### Then Test Pipeline Stages:
```bash
# Test parse stage only
dvc repro parse

# Test up to tables stage
dvc repro tables

# Test full pipeline
dvc repro
```

## What Success Looks Like

After `dvc repro` completes successfully:

1. **Files Created**:
   ```
   data/parsed/pdfplumber_tesseract/
   data/parsed/hybrid/
   data/parsed/layout_parser/
   data/parsed/docling/
   data/metadata/
   data/analysis/
   reports/
   ```

2. **DVC Files**:
   ```
   dvc.lock  # Created after successful run
   ```

3. **Pipeline Status**:
   ```bash
   dvc status  # Should show "Data and pipelines are up to date"
   ```

## Final Commit Commands

```bash
# Add all DVC configuration
git add dvc.yaml dvc.lock .dvc/config

# Add pipeline configuration
git add config/ .github/

# Add data tracking files
git add data/raw.dvc data/staged.dvc

# Add documentation
git add DVC_PIPELINE_GUIDE.md run_pipeline.sh run_pipeline.bat

# Commit everything
git commit -m "Complete DVC pipeline setup with all stages"

# Push to remote
git push
```

## Verification Checklist

- [ ] `dvc dag` shows complete pipeline graph
- [ ] `dvc status` reports pipeline is up to date
- [ ] All output directories contain expected files
- [ ] `dvc.lock` file exists and is committed
- [ ] GitHub Actions workflow passes smoke tests
- [ ] Pipeline can be reproduced with `dvc repro --force`