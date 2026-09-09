# Stage 2 ML Environment

## Purpose
This environment prepares the ML infrastructure for Stage 2 of the SIH26162 project:
- AI-Based Detection and Classification of Industrial Fires and Persistent Thermal Sources
- Uses NASA FIRMS, OSM & Satellite Data
- Focus: Tabular ML with GPU acceleration (XGBoost/CatBoost)

## Python Version
- Python 3.11.9

## Environment Activation
```bash
# From project root:
ml_env\Scripts\activate
```

## GPU Verification
Run the verification script:
```bash
python ml_service/check_gpu.py
```

## Installed ML Frameworks
See `ml_service/requirements.txt` for exact versions.

## GPU Support Status
- PyTorch: CUDA-enabled (v2.4.1+cu121)
- XGBoost: GPU support via `device='cuda'` or `tree_method='gpu_hist'`
- CatBoost: GPU support via `task_type='GPU'`
- LightGBm: GPU support available (may require special build)

## Important Notes
1. **NO REAL MODEL TRAINING YET** - This is environment preparation only
2. **DO NOT MODIFY STAGE 1/1B** - Existing ingestion/enrichment pipeline preserved
3. **DO NOT USE REAL DATASET** - Save for Stage 2B+
4. **ENVIRONMENT ISOLATION** - Uses separate `ml_env/` to avoid disturbing backend `venv/`

## Deactivation
```bash
deactivate
```