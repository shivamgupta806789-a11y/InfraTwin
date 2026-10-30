from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_zero_budget_produces_no_positive_cost_feasible_recommendations():
    payload = {
        "width_m": 12.0,
        "length_m": 16.0,
        "floor_height_m": 3.0,
        "floors": 2,
        "window_count": 16,
        "budget_inr": 0.0,
        "selected_interventions": []
    }
    response = client.post("/api/v1/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["budget_inr"] == 0.0
    assert len(data["ranked_recommendations"]) == 0
    for item in data["available_interventions"]:
        assert item["fits_budget"] is False
    assert any("₹0" in w for w in data["warnings"])

def test_recommendation_exceeding_budget_not_marked_feasible():
    # Budget of ₹20,000 is enough for reflective roof (192 m² * 250 = ₹48,000? No, 48k exceeds 20k!)
    # But for external shading (4 windows * 4500 = ₹18,000 <= 20,000)
    payload = {
        "width_m": 10.0,
        "length_m": 10.0,
        "floor_height_m": 3.0,
        "floors": 1,
        "window_count": 4,
        "budget_inr": 20000.0,  # 20k
        "selected_interventions": []
    }
    response = client.post("/api/v1/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    items = {item["id"]: item for item in data["available_interventions"]}
    
    # External shading cost = 4 * 4500 = 18,000 <= 20,000 -> fits_budget = True
    assert items["external_shading"]["fits_budget"] is True
    assert items["external_shading"]["estimated_cost_inr"] == 18000.0

    # Reflective roof cost = 100 * 250 = 25,000 > 20,000 -> fits_budget = False
    assert items["reflective_roof"]["fits_budget"] is False
    assert items["reflective_roof"]["estimated_cost_inr"] == 25000.0

    # Solar PV cost for 100m2 (60m2 usable = 6kWp = 6*48,000 = 288,000) > 20,000 -> fits_budget = False
    assert items["solar_pv"]["fits_budget"] is False

def test_combined_recommended_cost_never_exceeds_budget():
    payload = {
        "width_m": 12.0,
        "length_m": 16.0,
        "floor_height_m": 3.0,
        "floors": 2,
        "window_count": 16,
        "budget_inr": 150000.0,  # ₹1.5 Lakh
        "selected_interventions": []
    }
    response = client.post("/api/v1/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    total_cost = data["total_recommended_cost_inr"]
    budget = data["budget_inr"]
    assert total_cost <= budget
    assert data["remaining_budget_inr"] >= 0
    assert data["remaining_budget_inr"] == budget - total_cost

    # Sum of items in ranked_recommendations matches total_recommended_cost_inr
    computed_sum = sum(item["estimated_cost_inr"] for item in data["ranked_recommendations"])
    assert round(computed_sum, 2) == round(total_cost, 2)

def test_malformed_requests_return_clean_error():
    # String for numeric field
    bad_payload = {
        "width_m": "non-numeric",
        "length_m": 10.0,
        "floors": 2,
        "window_count": 4,
        "budget_inr": 10000.0
    }
    response = client.post("/api/v1/recommendations", json=bad_payload)
    assert response.status_code == 422
    data = response.json()
    assert "errors" in data or "detail" in data

def test_estimate_includes_assumptions_and_does_not_fabricate_unsupported_savings():
    # When no electricity kWh is provided
    payload = {
        "width_m": 12.0,
        "length_m": 16.0,
        "floor_height_m": 3.0,
        "floors": 2,
        "window_count": 16,
        "budget_inr": 500000.0,
        "selected_interventions": ["reflective_roof", "external_shading"]
    }
    response = client.post("/api/v1/estimate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert len(data["assumptions"]) > 0
    # Baseline emissions must NOT be estimated when kWh is None
    baseline_items = [i for i in data["impact_estimates"] if i["estimate_type"] == "baseline_operational_emissions"]
    assert len(baseline_items) == 1
    assert baseline_items[0]["is_estimated"] is False
    assert baseline_items[0]["value"] is None

    # Passive envelope savings must NOT fabricate fixed % or kWh
    passive_items = [i for i in data["impact_estimates"] if i["estimate_type"] == "thermal_envelope_savings"]
    assert len(passive_items) == 1
    assert passive_items[0]["is_estimated"] is False
    assert passive_items[0]["value"] is None
    assert "EnergyPlus" in passive_items[0]["calculation_method"] or "weather file" in passive_items[0]["evidence_limitations"].lower()

def test_estimate_with_electricity_calculates_transparent_baseline():
    payload = {
        "width_m": 12.0,
        "length_m": 16.0,
        "floor_height_m": 3.0,
        "floors": 2,
        "window_count": 16,
        "budget_inr": 500000.0,
        "selected_interventions": ["solar_pv"],
        "annual_electricity_kwh": 10000.0,
        "grid_emission_factor_kg_per_kwh": 0.716
    }
    response = client.post("/api/v1/estimate", json=payload)
    assert response.status_code == 200
    data = response.json()

    # 10,000 kWh * 0.716 kg = 7,160 kg = 7.16 tonnes
    baseline_items = [i for i in data["impact_estimates"] if i["estimate_type"] == "baseline_operational_emissions"]
    assert len(baseline_items) == 1
    assert baseline_items[0]["is_estimated"] is True
    assert baseline_items[0]["value"] == 7.16

    # Solar PV yield and avoided emissions calculated
    solar_items = [i for i in data["impact_estimates"] if i["estimate_type"] == "solar_generation_potential"]
    assert len(solar_items) == 1
    assert solar_items[0]["is_estimated"] is True
    assert solar_items[0]["value"] > 0
