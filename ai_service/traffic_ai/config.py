from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def ai_service_root() -> Path:
    return Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ModelPaths:
    vehicle: Path
    license_plate: Path
    illegal_stop: Path
    red_light: Path
    zebra_crossing: Path

    @classmethod
    def default(cls) -> "ModelPaths":
        model_dir = ai_service_root() / "models"
        return cls(
            vehicle=model_dir / "car_yolov8s.pt",
            license_plate=model_dir / "license.pt",
            illegal_stop=model_dir / "illegal_stop.pt",
            red_light=model_dir / "red_light.pt",
            zebra_crossing=model_dir / "zebra_crossing.pt",
        )


@dataclass(frozen=True)
class RuntimePaths:
    root: Path
    use_external_paddlex_cache: bool = False

    @property
    def tmp_dir(self) -> Path:
        return self.root / ".tmp"

    @property
    def yolo_config_dir(self) -> Path:
        return self.root / ".yolo_config"

    @property
    def paddlex_cache_dir(self) -> Path:
        if self.use_external_paddlex_cache and not _is_ascii_path(self.root):
            return _external_paddlex_cache_dir()
        return self.root / ".paddlex"

    @property
    def matplotlib_config_dir(self) -> Path:
        return self.root / ".matplotlib"

    @classmethod
    def default(cls) -> "RuntimePaths":
        return cls(root=project_root(), use_external_paddlex_cache=True)


def _is_ascii_path(path: Path) -> bool:
    try:
        str(path).encode("ascii")
    except UnicodeEncodeError:
        return False
    return True


def _external_paddlex_cache_dir() -> Path:
    configured = os.environ.get("TRAFFIC_AI_PADDLEX_CACHE_DIR")
    if configured:
        return Path(configured)
    system_drive = os.environ.get("SystemDrive", "C:")
    if os.name == "nt":
        return Path(system_drive + "\\tmp") / "smart_traffic_violation_paddlex"
    return Path(tempfile.gettempdir()) / "smart_traffic_violation_paddlex"


def ensure_runtime_environment(runtime: RuntimePaths | None = None, *, include_paddlex: bool = True) -> RuntimePaths:
    runtime = runtime or RuntimePaths.default()
    runtime.tmp_dir.mkdir(parents=True, exist_ok=True)
    runtime.yolo_config_dir.mkdir(parents=True, exist_ok=True)
    if include_paddlex:
        runtime.paddlex_cache_dir.mkdir(parents=True, exist_ok=True)
    runtime.matplotlib_config_dir.mkdir(parents=True, exist_ok=True)

    os.environ["TMP"] = str(runtime.tmp_dir)
    os.environ["TEMP"] = str(runtime.tmp_dir)
    os.environ["YOLO_CONFIG_DIR"] = str(runtime.yolo_config_dir)
    os.environ["XDG_CONFIG_HOME"] = str(runtime.yolo_config_dir)
    if include_paddlex:
        os.environ["PADDLE_PDX_CACHE_HOME"] = str(runtime.paddlex_cache_dir)
        os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
    os.environ["MPLCONFIGDIR"] = str(runtime.matplotlib_config_dir)
    return runtime
