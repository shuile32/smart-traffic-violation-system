def test_get_media_returns_stored_file(client, tmp_path, monkeypatch):
    image = b"\xff\xd8\xff\xd9"
    filename = "evidence.jpg"
    (tmp_path / filename).write_bytes(image)
    monkeypatch.setattr("app.core.config.settings.MEDIA_STORAGE_DIR", str(tmp_path))

    response = client.get(f"/media/{filename}")

    assert response.status_code == 200
    assert response.content == image
    assert response.headers["content-type"] == "image/jpeg"


def test_get_media_returns_404_for_missing_file(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.MEDIA_STORAGE_DIR", str(tmp_path))

    response = client.get("/media/missing.jpg")

    assert response.status_code == 404


def test_get_media_rejects_path_traversal(client, tmp_path, monkeypatch):
    outside_file = tmp_path.parent / f"outside-{tmp_path.name}.jpg"
    outside_file.write_bytes(b"outside storage root")
    monkeypatch.setattr("app.core.config.settings.MEDIA_STORAGE_DIR", str(tmp_path))

    response = client.get(f"/media/%2E%2E%5C{outside_file.name}")

    assert response.status_code == 404
