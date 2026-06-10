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
DEFAULT_MAX_CONTENT_LENGTH = 10 * 1024 * 1024
DEFAULT_MAX_UPLOAD_FILES = 8


def create_app(sample_dir: Path | None = None, upload_dir: Path | None = None) -> Flask:
    static_dir = Path(__file__).with_name("web_static")
    app = Flask(__name__, static_folder=static_dir, static_url_path="")
    app.config["SAMPLE_DIR"] = Path(sample_dir or "samples").resolve()
    app.config["UPLOAD_DIR"] = Path(upload_dir or Path("worktmp") / "web_uploads").resolve()
    app.config["MAX_CONTENT_LENGTH"] = DEFAULT_MAX_CONTENT_LENGTH
    app.config["MAX_UPLOAD_FILES"] = DEFAULT_MAX_UPLOAD_FILES
    app.config["ANALYSIS_RESULTS"] = {}

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
        uploads = [upload for upload in request.files.getlist("files") if upload.filename]
        if len(uploads) > app.config["MAX_UPLOAD_FILES"]:
            return jsonify({"error": "Too many uploaded local log files."}), 400
        paths = _selected_sample_paths(Path(app.config["SAMPLE_DIR"]), request.form.getlist("sample_ids"))
        uploaded_paths = _save_uploads(Path(app.config["UPLOAD_DIR"]), uploads)
        paths.extend(uploaded_paths)
        try:
            if not paths:
                return jsonify({"error": "Select at least one local log file or sample log."}), 400
            result = analyze_logs(paths)
        except (OSError, FileNotFoundError) as exc:
            return jsonify({"error": f"Could not analyze local input: {exc}"}), 400
        finally:
            _cleanup_uploads(uploaded_paths)
        analysis_id = uuid4().hex
        app.config["ANALYSIS_RESULTS"][analysis_id] = result
        payload = serialize_result(result)
        payload["analysis_id"] = analysis_id
        return jsonify(payload)

    @app.get("/api/exports/<fmt>")
    def export(fmt: str):
        if fmt not in EXPORTERS:
            return jsonify({"error": "Unsupported export format."}), 404
        analysis_id = request.args.get("analysis_id")
        if not analysis_id:
            return jsonify({"error": "Analysis must run and analysis id is required before exporting."}), 400
        result: AnalysisResult | None = app.config["ANALYSIS_RESULTS"].get(analysis_id)
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


def _save_uploads(upload_dir: Path, uploads: list[object]) -> list[Path]:
    upload_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for upload in uploads:
        filename = secure_filename(upload.filename)
        if not filename:
            continue
        path = upload_dir / f"{uuid4().hex}-{filename}"
        upload.save(path)
        paths.append(path)
    return paths


def _cleanup_uploads(paths: list[Path]) -> None:
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            continue


def main() -> None:
    upload_root = Path("worktmp") / "web_uploads"
    upload_root.mkdir(parents=True, exist_ok=True)
    app = create_app(upload_dir=upload_root)
    app.run(host="127.0.0.1", port=8765, debug=False)
