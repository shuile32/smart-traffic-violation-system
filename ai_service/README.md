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
- `red_light.pt`: traffic-light state detection, including `Traffic Light - Red`
- `zebra_crossing.pt`: zebra-crossing detection, class `zebra crossing`

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
- traffic-light and zebra-crossing detections
- suspected red-light violation evidence, including the contact and overlap boxes
- license plate region detections, only when a supported violation exists
- annotated image path, when at least one target is detected
- OCR result
- rule result
- suggested review conclusion

## Current Detection Flow

```text
manual upload -> reported_violation_type
              -> vehicle YOLO -> stable vehicle IDs
              -> illegal_stop: illegal-stop YOLO -> vehicle association
              -> red_light_violation: red-light + zebra-crossing YOLO
                                      -> OpenCV overlap rule
              -> select one strongest primary offending vehicle
              -> license-plate YOLO
              -> keep only a plate belonging to the primary vehicle
              -> crop matched plate -> OCR -> rule/vision-LLM review
```

Manual citizen, reviewer, and administrator uploads must send
`reported_violation_type=illegal_stop` or
`reported_violation_type=red_light_violation`. Only the selected workflow's
models run. Camera capture keeps the compatible automatic mode until a
separate camera-routing policy is defined.

All vehicles receive stable labels such as `小汽车1` and `小汽车2`. One image
still creates one case; if several vehicles satisfy the selected rule, only
the strongest target is primary. Plate localization and OCR never fall back
to a plate on another vehicle.

The red-light rule works on a single image. It takes the bottom 20% of a
vehicle box, narrows that contact area by 15% on both sides, and uses OpenCV to
measure its overlap with a detected zebra crossing. An overlap of at least 25%,
or a vehicle bottom-center point inside the crossing box, produces a
`red_light_violation` candidate under rule `red_light_zebra_overlap`. This is a
suspected violation for vision-LLM and human review; it does not claim to prove
motion across a stop line.

## OCR Status

PaddleOCR is supported through `PaddleOcrEngine`. The adapter is configured for
Chinese OCR (`lang="ch"`), normalizes plate text, and recognizes Chinese
province prefixes such as `京`, `沪`, `粤`, `浙`, `苏`, `川`, etc.

The backend stores a machine-readable plate status:

- `recognized`: OCR returned a plate
- `skipped_no_violation`: the selected rule produced no primary target
- `yolo_not_detected`: a primary target exists but plate YOLO found no plate on it
- `ocr_failed`: the target plate was localized but OCR could not read it

Failure messages are display fields only. They are never written into
`Case.plate_no`.

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
