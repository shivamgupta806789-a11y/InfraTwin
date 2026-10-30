from typing import List, Dict, Any, Optional
from app.models.building import BuildingInput
from app.models.recommendations import (
    EstimateRequest,
    EstimateResponse,
    CostBreakdownItem,
    ImpactEstimateItem,
)
from app.services.cost_engine import CostEngine, INTERVENTION_CATALOG

class ImpactEstimator:
    @classmethod
    def estimate_impacts(cls, request: EstimateRequest) -> EstimateResponse:
        building = request
        selected_ids = request.selected_interventions
        annual_kwh = request.annual_electricity_kwh
        grid_ef = request.grid_emission_factor_kg_per_kwh or 0.716

        cost_breakdowns: List[CostBreakdownItem] = []
        total_cost = 0.0

        for int_id in selected_ids:
            if int_id in INTERVENTION_CATALOG:
                meta = INTERVENTION_CATALOG[int_id]
                is_eligible, reason, qty, unit, cost = CostEngine.calculate_intervention_cost(
                    int_id, building
                )
                if is_eligible:
                    total_cost += cost
                    rate = cost / qty if qty > 0 else 0.0
                    cost_breakdowns.append(
                        CostBreakdownItem(
                            id=int_id,
                            name=meta["name"],
                            quantity=qty,
                            quantity_unit=unit,
                            unit_rate_inr=rate,
                            total_cost_inr=round(cost, 2),
                            formula=f"{qty} {unit} × ₹{rate:,.0f}/{unit} = ₹{cost:,.0f}",
                            assumptions=f"Standard unit cost rate: {meta['unit_cost_description']}"
                        )
                    )
                else:
                    cost_breakdowns.append(
                        CostBreakdownItem(
                            id=int_id,
                            name=meta["name"],
                            quantity=0.0,
                            quantity_unit=unit,
                            unit_rate_inr=0.0,
                            total_cost_inr=0.0,
                            formula="0 (Ineligible)",
                            assumptions=reason or "Ineligible"
                        )
                    )

        fits_budget = (total_cost <= building.budget_inr) if building.budget_inr > 0 else (total_cost == 0)

        impact_estimates: List[ImpactEstimateItem] = []
        missing_inputs: List[str] = []

        # 1. Baseline operational emissions calculation
        if annual_kwh is not None and annual_kwh > 0:
            baseline_emissions_kg = annual_kwh * grid_ef
            baseline_emissions_tonnes = baseline_emissions_kg / 1000.0
            impact_estimates.append(
                ImpactEstimateItem(
                    estimate_type="baseline_operational_emissions",
                    metric="Annual Grid Operational Emissions (Baseline)",
                    value=round(baseline_emissions_tonnes, 2),
                    unit="tCO2e / year",
                    is_estimated=True,
                    calculation_method="Operational Emissions = Annual Electricity (kWh) × Central Electricity Authority (CEA) Grid Factor (kg CO2e/kWh)",
                    assumptions=[
                        f"Reported annual electricity consumption: {annual_kwh:,.0f} kWh",
                        f"Indian National Grid Emission Factor: {grid_ef:.3f} kg CO2e/kWh (CEA Baseline Database Version 19, 2023)",
                        "Assumes zero direct Scope 1 on-site fossil fuel combustion (diesel generators/LPG)."
                    ],
                    source_provenance="Central Electricity Authority (CEA), Ministry of Power, Govt of India",
                    evidence_limitations="Scope 2 electricity grid average; does not account for marginal grid displacement or time-of-use variations.",
                    missing_inputs=[]
                )
            )
        else:
            missing_inputs.append("Utility electricity consumption data (annual kWh) not provided")
            impact_estimates.append(
                ImpactEstimateItem(
                    estimate_type="baseline_operational_emissions",
                    metric="Annual Grid Operational Emissions (Baseline)",
                    value=None,
                    unit="tCO2e / year",
                    is_estimated=False,
                    calculation_method="Operational Emissions = Annual Electricity (kWh) × CEA Grid Factor",
                    assumptions=[
                        "Cannot fabricate baseline emissions without real utility electricity billing data."
                    ],
                    source_provenance="Requires actual utility electricity bills or smart-meter telemetry",
                    evidence_limitations="Not estimated because annual electricity consumption is unknown.",
                    missing_inputs=["Annual electricity billing history in kWh"]
                )
            )

        # 2. Solar PV Yield and Avoided Emissions (only if solar_pv is selected)
        if "solar_pv" in selected_ids:
            roof_area = building.width_m * building.length_m
            usable_roof_area = roof_area * 0.60
            calculated_kwp = usable_roof_area / 10.0
            if calculated_kwp >= 1.0:
                system_kwp = max(1.0, (calculated_kwp * 2.0 // 1) / 2.0)
                # Standard India benchmark yield: ~1,450 kWh / kWp / year (4.0 peak sun hours/day * 365 * 0.75 PR)
                solar_yield_kwh_yr = round(system_kwp * 1450.0, 1)
                avoided_co2_kg_yr = round(solar_yield_kwh_yr * grid_ef, 1)
                avoided_co2_tonnes_yr = round(avoided_co2_kg_yr / 1000.0, 2)

                impact_estimates.append(
                    ImpactEstimateItem(
                        estimate_type="solar_generation_potential",
                        metric="Estimated On-Site Solar Generation",
                        value=solar_yield_kwh_yr,
                        unit="kWh / year",
                        is_estimated=True,
                        calculation_method="Capacity (kWp) × Benchmark Specific Yield (1,450 kWh/kWp/yr)",
                        assumptions=[
                            f"System size: {system_kwp:.1f} kWp DC",
                            "Specific yield benchmark: 1,450 kWh/kWp/year (representative for composite/warm-humid Indian climates with 75% performance ratio)",
                            "Assumes optimal southward tilt (15-20°) with unobstructed solar horizon."
                        ],
                        source_provenance="MNRE / National Institute of Solar Energy (NISE) solar resource data",
                        evidence_limitations="Preliminary geometric estimate. Does not replace site shading analysis (SunEye/LiDAR) or 8760-hour PVsyst simulation.",
                        missing_inputs=["Site specific tilt/azimuth angles", "Near-shading obstruction map"]
                    )
                )

                impact_estimates.append(
                    ImpactEstimateItem(
                        estimate_type="solar_avoided_emissions",
                        metric="Estimated Avoided Grid Emissions (Solar PV)",
                        value=avoided_co2_tonnes_yr,
                        unit="tCO2e / year",
                        is_estimated=True,
                        calculation_method="Estimated Solar Generation (kWh/yr) × Grid Factor (kg CO2e/kWh) / 1,000",
                        assumptions=[
                            f"Avoided generation: {solar_yield_kwh_yr:,.0f} kWh/year",
                            f"Grid factor: {grid_ef:.3f} kg CO2e/kWh"
                        ],
                        source_provenance="Calculated from MNRE yield benchmark and CEA grid emission factor",
                        evidence_limitations="Assumes 100% of generated solar electricity displaces grid electricity without curtailment.",
                        missing_inputs=[]
                    )
                )

        # 3. Passive thermal envelope measures (Cool roof, insulation, shading)
        passive_interventions = [
            i for i in selected_ids if i in ["reflective_roof", "roof_insulation", "external_shading"]
        ]
        if passive_interventions:
            missing_inputs.extend([
                "Hourly local weather file (TMY / EPW format)",
                "HVAC system type, COP, and cooling setpoints",
                "Internal plug loads and occupant scheduling profile"
            ])
            impact_estimates.append(
                ImpactEstimateItem(
                    estimate_type="thermal_envelope_savings",
                    metric="Thermal Cooling Energy Reduction",
                    value=None,
                    unit="kWh / year (requires EnergyPlus)",
                    is_estimated=False,
                    calculation_method="Dynamic transient heat transfer simulation (ISO 52016-1 / EnergyPlus)",
                    assumptions=[
                        f"Active envelope measures: {', '.join(passive_interventions)}.",
                        "Thermal cooling energy savings depend heavily on building thermal mass, HVAC efficiency (COP), thermostat setpoint (e.g. 24°C vs 26°C), and microclimate temperatures.",
                        "Fabricating a single fixed percentage or arbitrary kWh savings without 8,760-hour hourly thermodynamic balance would be scientifically inaccurate."
                    ],
                    source_provenance="Bureau of Energy Efficiency (BEE) Energy Conservation Building Code (ECBC 2017) methodology",
                    evidence_limitations="Scientific honesty: Not estimated in this MVP to prevent misleading claims. Requires dynamic thermal simulation with calibrated local weather data (EPW).",
                    missing_inputs=[
                        "Local weather file (EPW)",
                        "HVAC cooling efficiency (COP / ISEER)",
                        "Thermostat cooling setpoint & operating hours"
                    ]
                )
            )

        assumptions_summary = [
            "All unit rates and emission factors are explicitly referenced to Indian national standards (CEA 2023, MNRE 2023, BEE ECBC).",
            "No unverified carbon credits or offset claims are produced.",
            "Visual 3D modifications demonstrate geometric placement; thermal interaction requires dynamic energy simulation."
        ]

        return EstimateResponse(
            selected_interventions=selected_ids,
            total_cost_inr=round(total_cost, 2),
            budget_inr=building.budget_inr,
            fits_budget=fits_budget,
            cost_breakdown=cost_breakdowns,
            impact_estimates=impact_estimates,
            assumptions=assumptions_summary,
            missing_inputs=list(dict.fromkeys(missing_inputs))
        )
