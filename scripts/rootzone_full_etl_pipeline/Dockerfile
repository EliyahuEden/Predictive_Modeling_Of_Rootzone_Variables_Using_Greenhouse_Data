FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=7860

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY rootzone_full_etl.py ./
COPY rootzone_web_app.py ./
COPY dashboard_template.html ./
COPY fertilizer_dose_presets.json ./
COPY micro_climate_3day_unified_model.joblib ./
COPY v8_unified_model_48h_no_rh_shared_model.joblib ./
COPY v8_unified_model_48h_no_rh_model_meta.json ./

EXPOSE 7860

CMD ["python", "rootzone_web_app.py"]
