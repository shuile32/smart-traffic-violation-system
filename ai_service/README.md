# AI Service

This folder contains the data-processing and algorithm code for the traffic
violation project. It is intentionally independent from the frontend and
backend so those layers can keep changing while the YOLO/OCR pipeline remains
easy to test and integrate.

## Current Models

Trained weights are stored under `ai_service/models/`:

- `car_yolov8s.pt`: vehicle detection, classes `bus`, `cars`, `truck`, `van`
- `license.pt`: license plate region detection, class `chinese-plate-license`
- `illegal_stop.pt`: illegal parking/stop detection, class `illegal`

The code loads these files through repository-relative paths. It does not need
the original training directory at runtime.

## Runtime Environment

Use the YOLO conda environment, then run commands from the repository root:

```powershell
conda activate yolo
```

The runtime creates local ignored folders for temporary data:

- `.tmp/`
- `.yolo_config/`
- `.matplotlib/`
- `ai_service/outputs/`

PaddleOCR model cache is stored outside the repository by default through the
system temporary directory. If a machine needs a custom cache location, set:

```powershell
$env:TRAFFIC_AI_PADDLEX_CACHE_DIR = "D:\some_ascii_cache_dir\paddlex"
```

Do not commit PaddleOCR cache files.

## Run Tests

```powershell
python -m unittest discover -s ai_service\tests -v
```

## Run Detection

```powershell
python -m ai_service.traffic_ai.cli path\to\image.jpg --pretty
```

The command prints JSON with:

- vehicle detections
- illegal-stop detections
- license plate region detections, only when an illegal-stop target exists
- annotated image path, when at least one target is detected
- OCR result
- rule result
- suggested review conclusion

## Current Detection Flow

```text
vehicle YOLO -> illegal-stop YOLO -> if no violation, stop
             -> if violation exists, license-plate YOLO
             -> crop detected plate region
             -> OCR reads the cropped plate image
             -> rule/LLM review uses structured evidence
```

Only illegal parking/stop is implemented now. Other violation types such as
solid-line crossing or wrong-way driving should be added later as additional
violation detectors and rule evaluators.

## OCR Status

PaddleOCR is supported through `PaddleOcrEngine`. The adapter is configured for
Chinese OCR (`lang="ch"`), normalizes plate text, and recognizes Chinese
province prefixes such as `京`, `沪`, `粤`, `浙`, `苏`, `川`, etc.

If PaddleOCR is unavailable on another machine, `create_default_ocr_engine()`
falls back safely to:

```json
{ "text": null, "engine": "none", "status": "unavailable" }
```

## LLM Review

The LLM adapter uses an OpenAI-compatible `/chat/completions` endpoint. Runtime
configuration should come from environment variables or a local ignored
`backend/.env` file:

```env
LLM_PROVIDER=zhipu
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_TEXT_MODEL=glm-5.1
LLM_VISION_MODEL=glm-5v-turbo
LLM_MODE=vision
LLM_API_KEY=your_key_here
```

Never commit real API keys.

## Backend Contract

Use `ai_service.traffic_ai.backend_contract` to convert algorithm dataclasses
into backend route-compatible dictionaries. This keeps the algorithm package
separate while the backend continues to change.
