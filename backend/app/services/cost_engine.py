import math
from typing import Dict, Any, Tuple
from app.models.building import BuildingInput

INTERVENTION_CATALOG = {
    "external_shading": {
        "name": "External Window Shading Louvers",
        "category": "Facade & Glazing",
        "description": "Adjustable or fixed architectural louvers/fins mounted externally on glazed openings to block direct solar radiation while admitting diffuse daylight.",
        "unit_cost_description": "₹4,500 per window aperture (anodized aluminum or treated timber fins with structural brackets)",
        "quantity_unit": "windows",
        "evidence_status": "Standard Indian architectural engineering benchmark (CPWD DSR 2023 derived)",
        "limitations": [
            "Assumes standard window aperture ~2 m² (1.2m x 1.6m). Larger openings require bespoke structural supports.",
            "Visual model does not reflect local window orientation (north vs south solar path)."
        ]
    },
    "reflective_roof": {
        "name": "High-Albedo Reflective Cool Roof Coating",
        "category": "Roof & Envelope",
        "description": "Multi-coat elastomeric high-reflectance white polyurethane or acrylic waterproofing membrane (SRI >= 100) applied directly over terrace slab.",
        "unit_cost_description": "₹250 per m² of exposed flat terrace area (primer + 2 elastomeric coats with primer)",
        "quantity_unit": "m²",
        "evidence_status": "Empirical municipal cool roof program benchmark (Ahmedabad/Telangana Cool Roof Policy)",
        "limitations": [
            "Simplified flat roof area with zero slope or parapet height deductions.",
            "Requires recoating or regular washing every 3-5 years to preserve solar reflectance."
        ]
    },
    "roof_insulation": {
        "name": "Over-Deck Rigid Roof Insulation (50mm XPS)",
        "category": "Thermal Envelope",
        "description": "Extruded polystyrene (XPS) closed-cell thermal insulation boards laid over waterproofing membrane with protective screed/tile topping.",
        "unit_cost_description": "₹850 per m² (50mm high-density XPS boards + geotextile filter layer + protective mortar screed)",
        "quantity_unit": "m²",
        "evidence_status": "Standard Bureau of Energy Efficiency (BEE) ECBC / NBC 2016 envelope specifications",
        "limitations": [
            "Assumes accessible flat roof with sufficient load-bearing structural capacity for protective screed.",
            "Does not account for penetrations, water tanks, HVAC condensing units, or skylight curbs."
        ]
    },
    "solar_pv": {
        "name": "Grid-Tied Rooftop Solar PV System",
        "category": "On-Site Renewable Energy",
        "description": "Tier-1 monocrystalline photovoltaic array with string inverter, elevated galvanized mounting structures, AC/DC distribution boxes, and net metering provision.",
        "unit_cost_description": "₹48,000 per kWp installed DC capacity (excluding state/central subsidies)",
        "quantity_unit": "kWp DC",
        "evidence_status": "Ministry of New and Renewable Energy (MNRE) benchmark capital cost framework",
        "limitations": [
            "Assumes 60% usable terrace area after mandatory parapet setbacks, access corridors, and shadow casting zones.",
            "Assumes 10 m² roof area per 1 kWp installed capacity.",
            "Minimum feasible residential system size is 1.0 kWp DC.",
            "Does not include battery energy storage systems (BESS) or local distribution transformer upgrade charges."
        ]
    }
}


class CostEngine:
    @staticmethod
    def calculate_intervention_cost(
        intervention_id: str,
        building: BuildingInput
    ) -> Tuple[bool, Optional[str], float, str, float]:
        """
        Returns:
            (is_eligible, ineligibility_reason, quantity, quantity_unit, total_cost_inr)
        """
        roof_area = building.width_m * building.length_m

        if intervention_id == "external_shading":
            if building.window_count <= 0:
                return (
                    False,
                    "No windows detected in building model. External shading requires at least 1 window aperture.",
                    0.0,
                    "windows",
                    0.0
                )
            quantity = float(building.window_count)
            unit_rate = 4500.0
            total_cost = quantity * unit_rate
            return (True, None, quantity, "windows", total_cost)

        elif intervention_id == "reflective_roof":
            if roof_area <= 0:
                return (False, "Roof area must be greater than zero.", 0.0, "m²", 0.0)
            quantity = round(roof_area, 2)
            unit_rate = 250.0
            total_cost = quantity * unit_rate
            return (True, None, quantity, "m²", total_cost)

        elif intervention_id == "roof_insulation":
            if roof_area <= 0:
                return (False, "Roof area must be greater than zero.", 0.0, "m²", 0.0)
            quantity = round(roof_area, 2)
            unit_rate = 850.0
            total_cost = quantity * unit_rate
            return (True, None, quantity, "m²", total_cost)

        elif intervention_id == "solar_pv":
            # 60% usable rooftop area
            usable_roof_area = roof_area * 0.60
            # 10 m2 per kWp
            calculated_kwp = usable_roof_area / 10.0
            if calculated_kwp < 1.0:
                return (
                    False,
                    f"Rooftop area ({roof_area:.1f} m² with {usable_roof_area:.1f} m² usable space) is below minimum 1.0 kWp system threshold (~16.7 m² required).",
                    0.0,
                    "kWp DC",
                    0.0
                )
            # Round down to nearest 0.5 kWp for standard inverter sizing
            system_size_kwp = math.floor(calculated_kwp * 2.0) / 2.0
            if system_size_kwp < 1.0:
                system_size_kwp = 1.0
            unit_rate = 48000.0
            total_cost = system_size_kwp * unit_rate
            return (True, None, system_size_kwp, "kWp DC", total_cost)

        else:
            return (False, f"Unrecognized intervention identifier '{intervention_id}'.", 0.0, "unit", 0.0)
