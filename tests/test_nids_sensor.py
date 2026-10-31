import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import pandas as pd
import pytest
from nids_sensor import extract, send, to_records

BASE_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def feature_cols():
    with open(BASE_DIR / "models" / "feature_cols.json") as f:
        return json.load(f)


@pytest.fixture
def sample_df(feature_cols):
    extra_cols = [
        "bidirectional_first_seen_ms",
        "src_ip",
        "src_mac",
        "src_port",
        "dst_ip",
        "dst_port",
    ]
    all_cols = feature_cols + extra_cols
    data = {c: [1.0, 2.0, np.nan, np.inf, -np.inf] for c in all_cols}
    data["src_ip"] = ["192.168.1.1", "192.168.1.2", "192.168.1.3", "192.168.1.4", "192.168.1.5"]
    data["dst_ip"] = ["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4", "10.0.0.5"]
    data["src_port"] = [1234, 1235, 1236, 1237, 1238]
    data["dst_port"] = [80, 443, 8080, 22, 53]
    data["src_mac"] = ["00:11:22:33:44:55"] * 5
    data["protocol"] = [6, 17, 6, 6, 17]
    data["bidirectional_first_seen_ms"] = [1600000000000 + i * 1000 for i in range(5)]
    return pd.DataFrame(data)


def test_to_records_converts_nan_and_inf_to_none(sample_df, feature_cols):
    records = to_records(sample_df, feature_cols)
    assert len(records) == 5
    assert isinstance(records, list)

    # Vérification que le JSON est sérialisable et que NaN/inf sont devenus null (None)
    json_str = json.dumps(records)
    assert json_str is not None

    rec_nan = records[2]
    # feature_cols[1] (bidirectional_duration_ms) contient NaN -> converti en None
    assert rec_nan[feature_cols[1]] is None

    # Lignes 3 et 4 contiennent inf et -inf -> convertis en None
    assert records[3][feature_cols[1]] is None
    assert records[4][feature_cols[1]] is None


def test_send_batches_and_aggregates_predictions(sample_df, feature_cols):
    mock_response_1 = MagicMock()
    mock_response_1.raise_for_status.return_value = None
    mock_response_1.json.return_value = {"preds": ["BENIGN", "BENIGN"]}

    mock_response_2 = MagicMock()
    mock_response_2.raise_for_status.return_value = None
    mock_response_2.json.return_value = {"preds": ["PortScan", "BENIGN"]}

    mock_response_3 = MagicMock()
    mock_response_3.raise_for_status.return_value = None
    mock_response_3.json.return_value = {"preds": ["DDoS"]}

    with patch("requests.post", side_effect=[mock_response_1, mock_response_2, mock_response_3]) as mock_post:
        preds = send(
            df=sample_df,
            feature_cols=feature_cols,
            url="http://localhost:8000",
            key="test-api-key",
            sensor_id="sensor-alpha",
            batch=2,
        )

        assert mock_post.call_count == 3
        # Vérification du premier appel
        first_call = mock_post.call_args_list[0]
        assert first_call[0][0] == "http://localhost:8000/ingest"
        assert first_call[1]["headers"]["x-api-key"] == "test-api-key"
        assert first_call[1]["headers"]["Content-Type"] == "application/json"

        body = json.loads(first_call[1]["data"])
        assert body["sensor_id"] == "sensor-alpha"
        assert len(body["flows"]) == 2

        # Vérification du résultat agrégé
        assert preds == ["BENIGN", "BENIGN", "PortScan", "BENIGN", "DDoS"]


def test_extract_pcap_sample():
    pcap_file = BASE_DIR / "pcap" / "dos(1).pcap"
    if not pcap_file.exists():
        pytest.skip("Fichier pcap de test absent.")

    df = extract(str(pcap_file))
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "src_ip" in df.columns
    assert "dst_ip" in df.columns
    assert "protocol" in df.columns
