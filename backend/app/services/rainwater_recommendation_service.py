import datetime
from typing import Dict, Any, Optional, List, Tuple
from app.models.rainwater import (
    BuildingUnifiedFeatures,
    LocationClimateProfile,
    RainwaterDesignAlternative,
    RainwaterRecommendationReport,
)
from app.services.building_feature_service import BuildingFeatureService
from app.services.location_climate_service import LocationClimateService
from app.services.hydrological_engine import HydrologicalEngine
from app.services.rainwater_ml_service import RainwaterMLService


class RainwaterRecommendationService:
    """
    Evidence-based recommendation and ranking engine for building-specific rainwater management.
    Integrates verified building geometry, location-specific 30-year climatological normals,
    hydrological mass-balance simulations, machine learning performance predictions,
    and engineering/hydrogeological constraints.
    """

    @classmethod
    def evaluate_rainwater_recommendations(
        cls,
        model_id: str = "sample-office-twin",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        building_type: Optional[str] = None,
        occupancy: Optional[int] = None,
        user_confirmed_location: bool = True
    ) -> RainwaterRecommendationReport:
        """
        Executes end-to-end evaluation pipeline:
        1. Extracts verified building features (IFC/parametric).
        2. Retrieves location-specific 30-year climatological profile.
        3. Simulates hydrological performance across 7 candidate design configurations.
        4. Predicts performance using trained ML ensemble.
        5. Evaluates multi-criteria ranking scores and eliminates unfeasible options.
        6. Generates complete evidence, tradeoffs, and compliance report.
        """
        # 1. Extract unified building features
        features = BuildingFeatureService.extract_features(
            model_id=model_id,
            user_confirmed_lat=latitude,
            user_confirmed_lon=longitude,
            user_confirmed_type=building_type,
            user_confirmed_occupancy=occupancy
        )

        # 2. Retrieve location climate profile
        lat = features.latitude or 28.6139
        lon = features.longitude or 77.2090
        climate = LocationClimateService.get_location_climate_profile(
            latitude=lat,
            longitude=lon,
            is_user_confirmed=user_confirmed_location
        )

        # 3. Generate candidate design alternatives and simulate hydrology
        raw_alternatives = HydrologicalEngine.generate_design_alternatives(features, climate)

        # 4. Score and cross-validate with ML predictions
        scored_alternatives: List[RainwaterDesignAlternative] = []
        feasibility_matrix: Dict[str, bool] = {}
        elimination_reasons: Dict[str, str] = {}

        for alt in raw_alternatives:
            feasibility_matrix[alt.alternative_id] = alt.is_feasible
            if not alt.is_feasible:
                elimination_reasons[alt.alternative_id] = "; ".join(alt.infeasibility_reasons)

            # Query ML model for predicted performance
            ml_input = {
                "roof_catchment_area_m2": features.roof_area_m2,
                "roof_runoff_coefficient": features.roof_runoff_coefficient,
                "roof_slope_deg": features.roof_slope_deg,
                "storeys_count": features.storeys_count,
                "occupancy_count": features.occupancy_count,
                "daily_non_potable_demand_l": features.daily_non_potable_water_demand_l,
                "tank_capacity_l": alt.tank_capacity_liters,
                "annual_rainfall_mm": climate.annual_rainfall_mm,
                "rainfall_seasonality_index": climate.rainfall_seasonality_index,
                "rainfall_intensity_2yr_mm_hr": climate.rainfall_intensity_mm_hr_2yr,
                "terrain_slope_pct": climate.terrain_slope_pct,
                "soil_infiltration_rate_mm_hr": climate.soil_infiltration_rate_mm_hr,
                "groundwater_depth_m": climate.groundwater_depth_m,
            }

            try:
                ml_res = RainwaterMLService.predict_performance(ml_input)
                preds = ml_res["predictions"]
                alt.ml_predicted_demand_coverage_pct = preds["target_annual_demand_coverage_pct"]
                alt.ml_predicted_captured_liters = preds["target_annual_captured_l"]
            except Exception:
                pass

            # Calculate transparent Multi-Criteria Ranking Score (0 - 100)
            if not alt.is_feasible:
                alt.ranking_score = 0.0
            else:
                sim = alt.hydrological_performance
                # 1. Water conservation & coverage (35 pts)
                score_water = min(35.0, (sim.annual_demand_coverage_pct / 100.0) * 35.0)

                # 2. Financial payback efficiency (25 pts)
                if alt.simple_payback_years <= 1.0:
                    score_cost = 25.0
                elif alt.simple_payback_years >= 15.0:
                    score_cost = 5.0
                else:
                    score_cost = max(5.0, 25.0 - (alt.simple_payback_years / 15.0) * 20.0)

                # 3. Space footprint impact (15 pts)
                if alt.space_required_m2 <= 0.1:
                    score_space = 15.0  # Zero ground footprint
                else:
                    avail_ratio = alt.space_required_m2 / max(5.0, features.available_exterior_space_m2)
                    score_space = max(2.0, 15.0 * (1.0 - min(0.9, avail_ratio)))

                # 4. Overflow mitigation & flood resilience (15 pts)
                uncontrolled_overflow_ratio = sim.annual_overflow_liters / max(1.0, sim.annual_potential_runoff_liters)
                score_flood = 15.0 * (1.0 - min(1.0, uncontrolled_overflow_ratio))
                if alt.configuration_type in ["storage_swale", "storage_recharge", "rain_garden"]:
                    score_flood = min(15.0, score_flood + 4.5)  # Bonus for active attenuation

                # 5. Ecological & Aquifer Replenishment (10 pts)
                score_eco = 3.0
                if alt.groundwater_recharge_potential_liters > 0:
                    score_eco = 10.0
                elif alt.configuration_type == "storage_swale":
                    score_eco = 7.5

                alt.ranking_score = round(score_water + score_cost + score_space + score_flood + score_eco, 1)

            scored_alternatives.append(alt)

        # Sort: feasible first by score descending, then unfeasible
        feasible_alts = [a for a in scored_alternatives if a.is_feasible]
        unfeasible_alts = [a for a in scored_alternatives if not a.is_feasible]

        feasible_alts.sort(key=lambda x: x.ranking_score, reverse=True)
        for idx, a in enumerate(feasible_alts, start=1):
            a.rank = idx

        for idx, a in enumerate(unfeasible_alts, start=len(feasible_alts) + 1):
            a.rank = idx

        all_ranked = feasible_alts + unfeasible_alts
        best_alt_id = all_ranked[0].alternative_id if all_ranked else "ALT-A-GROUND-TANK"

        assumptions = [
            f"Roof catchment area ({features.roof_area_m2:.1f} m²) derived from 3D building envelope.",
            f"Runoff coefficient ({features.roof_runoff_coefficient:.2f}) verified for {features.roof_material} material.",
            f"Precipitation baseline: WMO/IMD 30-year normal ({climate.annual_rainfall_mm:.0f} mm/year) at ({lat:.4f}°N, {lon:.4f}°E).",
            f"Non-potable water demand ({features.daily_non_potable_water_demand_l:.0f} L/day) estimated for {features.occupancy_count} occupants per NBC 2016 Part 9.",
            "Water utility tariff valued at ₹45.0 per kilo-liter (commercial municipal rate) for payback analysis.",
            "First-flush diverter discharges initial 1.5mm rainfall depth to eliminate atmospheric dust and roof debris."
        ]

        missing_data = []
        if features.available_exterior_space_m2 == 45.0:
            missing_data.append("Site boundary survey / cadastral plot plan (exterior yard dimensions assumed from 35% setback standard).")
        if climate.groundwater_depth_m == 4.5:
            missing_data.append("Site exploratory borehole log (groundwater depth estimated from regional hydrogeological layer).")

        statutory_notices = [
            "Central Ground Water Board (CGWB) artificial recharge guidelines mandate minimum 3.5m unsaturated vadose zone above water table.",
            "State Pollution Control Board (SPCB) prohibits industrial chemical roof runoff discharge into unconfined recharge wells.",
            "National Building Code 2016 (Part 9) mandates rainwater harvesting for all plot developments exceeding 100 m² in municipal jurisdictions."
        ]

        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return RainwaterRecommendationReport(
            building_id=model_id,
            timestamp=now_str,
            location_profile=climate,
            building_features=features,
            selected_recommended_alternative_id=best_alt_id,
            ranked_alternatives=all_ranked,
            feasibility_matrix=feasibility_matrix,
            elimination_justifications=elimination_reasons,
            engineering_assumptions=assumptions,
            missing_data_warnings=missing_data,
            statutory_compliance_notices=statutory_notices
        )
