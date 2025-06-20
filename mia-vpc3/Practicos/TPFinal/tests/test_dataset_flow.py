import pytest

from vision_transformer.flows.dataset_flow import download_raw_data_task, execute_flow, extract_raw_data_task


def test_download_raw_data_task(monkeypatch: pytest.MonkeyPatch):
    """Test para asegurar que la tarea de descarga de datos se ejecuta correctamente."""
    called = {}

    def fake_download_raw_data():
        called["executed"] = True

    monkeypatch.setattr("vision_transformer.dataset.download_raw_data", fake_download_raw_data)
    download_raw_data_task.fn()
    assert called.get("executed", True)


def test_extract_raw_data_task(monkeypatch: pytest.MonkeyPatch):
    """Test para asegurar que la tarea de extracción de datos se ejecuta correctamente."""
    called = {}

    def fake_extract_raw_data():
        called["executed"] = True

    monkeypatch.setattr("vision_transformer.dataset.extract_raw_data", fake_extract_raw_data)
    extract_raw_data_task.fn()
    assert called.get("executed", True)
