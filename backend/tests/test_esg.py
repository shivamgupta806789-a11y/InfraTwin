import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_model_quality_report():
    response = client.get("/api/v1/models/sample-office-twin/quality")
    assert response.status_code == 200
    report = response.json()
    assert report["model_id"] == "sample-office-twin"
    assert "findings" in report
    assert "data_completeness_ratio" in report
    assert report["data_completeness_ratio"] > 0
    assert "by_severity" in report
    # Findings must include stable finding_ids
    for finding in report["findings"]:
        assert finding["finding_id"].startswith("QUAL-")
        assert finding["severity"] in ["info", "warning", "error", "critical"]
        assert len(finding["recommended_action"]) > 0

def test_model_esg_assessment_with_missing_electricity():
    response = client.get("/api/v1/models/sample-office-twin/esg")
    assert response.status_code == 200
    esg = response.json()
    assert esg["model_id"] == "sample-office-twin"
    assert "environmental" in esg
    assert "social" in esg
    assert "governance" in esg

    # Without electricity, Operational emissions must be marked 'insufficient_data'
    op_item = next(
        item for item in esg["environmental"]
        if item["criterion_id"] == "ENV-02"
    )
    assert op_item["result_status"] == "insufficient_data"
    assert op_item["metric_value"] is None
    assert len(op_item["missing_inputs"]) > 0

    # Universal accessibility door check
    door_item = next(
        item for item in esg["social"]
        if item["criterion_id"] == "SOC-01"
    )
    assert door_item["result_status"] in ["assessed", "potential_concern"]

    # Governance BIM lineage check
    gov_item = next(
        item for item in esg["governance"]
        if item["criterion_id"] == "GOV-01"
    )
    assert gov_item["result_status"] == "assessed"

def test_model_esg_assessment_with_supplied_electricity():
    # Pass 24,000 kWh annual electricity
    response = client.get("/api/v1/models/sample-office-twin/esg?annual_kwh=24000")
    assert response.status_code == 200
    esg = response.json()

    op_item = next(
        item for item in esg["environmental"]
        if item["criterion_id"] == "ENV-02"
    )
    # 24,000 * 0.716 / 1000 = 17.18 tonnes CO2e
    assert op_item["result_status"] == "assessed"
    assert op_item["metric_value"] == 17.18
    assert op_item["unit"] == "tCO2e / year"
    assert "CEA" in op_item["source_or_provenance"]
