from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, request, send_file
from werkzeug.utils import secure_filename

from .analysis import analyze_logs
from .exporters import export_csv, export_json, export_markdown
from .models import AnalysisResult
from .web_serialization import serialize_result


EXPORTERS = {
    "json": ("analysis.json", "application/json", export_json),
    "csv": ("analysis.csv", "text/csv", export_csv),
    "markdown": ("analysis.md", "text/markdown", export_markdown),
}


def create_app(sample_dir: Path | None = None, upload_dir: Path | None = None) -> Flask:
    static_dir = Path(__file__).with_name("web_static")
    app = Flask(__name__, static_folder=static_dir, static_url_path="")
    app.config["SAMPLE_DIR"] = sample_dir or Path("samples")
    app.config["UPLOAD_DIR"] = upload_dir or Path("worktmp") / "web_uploads"
    app.config["LATEST_RESULT"] = None

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/api/samples")
    def samples():
        root = Path(app.config["SAMPLE_DIR"])
        entries = []
        if root.exists():
            entries = [
                {"id": path.name, "name": path.name}
                for path in sorted(root.iterdir())
                if path.is_file()
            ]
        return jsonify({"samples": entries})

    @app.post("/api/analyze")
    def analyze():
        paths = _selected_sample_paths(Path(app.config["SAMPLE_DIR"]), request.form.getlist("sample_ids"))
        paths.extend(_save_uploads(Path(app.config["UPLOAD_DIR"])))
        if not paths:
            return jsonify({"error": "Select at least one local log file or sample log."}), 400
        try:
            result = analyze_logs(paths)
        except (OSError, FileNotFoundError) as exc:
            return jsonify({"error": f"Could not analyze local input: {exc}"}), 400
        app.config["LATEST_RESULT"] = result
        return jsonify(serialize_result(result))

    @app.get("/api/exports/<fmt>")
    def export(fmt: str):
        if fmt not in EXPORTERS:
            return jsonify({"error": "Unsupported export format."}), 404
        result: AnalysisResult | None = app.config.get("LATEST_RESULT")
        if result is None:
            return jsonify({"error": "Analysis must run before exporting."}), 400
        filename, mimetype, exporter = EXPORTERS[fmt]
        export_root = Path(app.config["UPLOAD_DIR"]) / "exports"
        export_path = export_root / f"{uuid4().hex}-{filename}"
        exporter(result, export_path)
        return send_file(export_path, mimetype=mimetype, as_attachment=True, download_name=filename)

    return app


def _selected_sample_paths(sample_dir: Path, sample_ids: list[str]) -> list[Path]:
    paths = []
    for sample_id in sample_ids:
        safe_name = Path(sample_id).name
        path = sample_dir / safe_name
        if path.is_file():
            paths.append(path)
    return paths


def _save_uploads(upload_dir: Path) -> list[Path]:
    upload_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for upload in request.files.getlist("files"):
        if not upload.filename:
            continue
        filename = secure_filename(upload.filename)
        if not filename:
            continue
        path = upload_dir / f"{uuid4().hex}-{filename}"
        upload.save(path)
        paths.append(path)
    return paths


def main() -> None:
    upload_root = Path("worktmp") / "web_uploads"
    upload_root.mkdir(parents=True, exist_ok=True)
    app = create_app(upload_dir=upload_root)
    app.run(host="127.0.0.1", port=8765, debug=False)
