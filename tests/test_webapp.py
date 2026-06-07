from __future__ import annotations

from io import BytesIO
from pathlib import Path

from logcheck.webapp import create_app


def make_app(tmp_path: Path):
    sample_dir = tmp_path / "samples"
    sample_dir.mkdir()
    (sample_dir / "auth.log").write_text(
        "Jun  1 10:00:00 host sshd[1]: Failed password for root from 192.0.2.10 port 22 ssh2\n",
        encoding="utf-8",
    )
    return create_app(sample_dir=sample_dir, upload_dir=tmp_path / "uploads").test_client()


def test_health_endpoint(tmp_path):
    client = make_app(tmp_path)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_samples_endpoint_lists_local_samples(tmp_path):
    client = make_app(tmp_path)

    response = client.get("/api/samples")

    assert response.status_code == 200
    assert response.get_json()["samples"] == [{"id": "auth.log", "name": "auth.log"}]


def test_dashboard_renders_local_investigation_regions(tmp_path):
    client = make_app(tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    for region in [
        "Logcheck",
        "Source intake",
        "Analysis summary",
        "Finding queue",
        "Evidence detail",
        "Investigation insights",
        "Exports",
    ]:
        assert region in html


def test_dashboard_excludes_forbidden_remote_control_terms(tmp_path):
    client = make_app(tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True).lower()
    for forbidden in [
        "url",
        "domain",
        "remote upload",
        "network scan",
        "scan target",
        "exploit",
        "block ip",
        "external report",
    ]:
        assert forbidden not in html


def test_analyze_uploaded_file(tmp_path):
    client = make_app(tmp_path)

    response = client.post(
        "/api/analyze",
        data={
            "files": (
                BytesIO(
                    b"Jun  1 10:00:00 host sshd[1]: Failed password for admin from 192.0.2.11 port 22 ssh2\n"
                ),
                "upload.log",
            )
        },
        content_type="multipart/form-data",
    )

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["summary"]["total_events"] == 1
    assert payload["summary"]["total_findings"] >= 1
    assert payload["findings"][0]["source_file"].endswith("upload.log")


def test_analyze_sample_and_uploaded_file_together(tmp_path):
    client = make_app(tmp_path)

    response = client.post(
        "/api/analyze",
        data={
            "sample_ids": "auth.log",
            "files": (BytesIO(b"generic suspicious malware line\n"), "extra.log"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert response.get_json()["summary"]["total_events"] >= 2


def test_analyze_requires_local_input(tmp_path):
    client = make_app(tmp_path)

    response = client.post("/api/analyze", data={}, content_type="multipart/form-data")

    assert response.status_code == 400
    assert "local log" in response.get_json()["error"].lower()


def test_export_requires_analysis_first(tmp_path):
    client = make_app(tmp_path)

    response = client.get("/api/exports/json")

    assert response.status_code == 400
    assert "analysis must run" in response.get_json()["error"].lower()


def test_export_json_after_analysis(tmp_path):
    client = make_app(tmp_path)
    analyze = client.post("/api/analyze", data={"sample_ids": "auth.log"}, content_type="multipart/form-data")
    analysis_id = analyze.get_json()["analysis_id"]

    response = client.get(f"/api/exports/json?analysis_id={analysis_id}")

    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert b"findings" in response.data


def test_export_requires_analysis_id_after_analysis(tmp_path):
    client = make_app(tmp_path)
    client.post("/api/analyze", data={"sample_ids": "auth.log"}, content_type="multipart/form-data")

    export = client.get("/api/exports/json")

    assert export.status_code == 400
    assert "analysis id" in export.get_json()["error"].lower()


def test_export_rejects_unknown_analysis_id(tmp_path):
    client = make_app(tmp_path)

    response = client.get("/api/exports/json?analysis_id=missing")

    assert response.status_code == 400
    assert "analysis must run" in response.get_json()["error"].lower()


def test_analyze_rejects_more_than_configured_uploaded_files(tmp_path):
    client = make_app(tmp_path)
    client.application.config["MAX_UPLOAD_FILES"] = 1

    response = client.post(
        "/api/analyze",
        data={
            "files": [
                (BytesIO(b"first failed password line\n"), "first.log"),
                (BytesIO(b"second failed password line\n"), "second.log"),
            ]
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert "too many" in response.get_json()["error"].lower()


def test_uploaded_files_are_cleaned_after_analysis(tmp_path):
    upload_dir = tmp_path / "uploads"
    client = create_app(sample_dir=tmp_path / "samples", upload_dir=upload_dir).test_client()

    response = client.post(
        "/api/analyze",
        data={
            "files": (
                BytesIO(
                    b"Jun  1 10:00:00 host sshd[1]: Failed password for admin from 192.0.2.11 port 22 ssh2\n"
                ),
                "upload.log",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert not list(upload_dir.glob("*upload.log"))
