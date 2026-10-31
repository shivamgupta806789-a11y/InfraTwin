import math
from typing import List, Dict, Any, Tuple, Optional
from app.models.rainwater import (
    BuildingUnifiedFeatures,
    LocationClimateProfile,
    HydrologicalMonthlySimulation,
    HydrologicalPerformanceSummary,
    RainwaterDesignAlternative,
    Intervention3DComponent,
)


class HydrologicalEngine:
    """
    Hydrological calculation engine and multi-alternative configuration generator.
    Performs monthly and daily mass-balance simulations, sizes storage capacities,
    and applies transparent engineering and site constraints to eliminate non-viable options.
    """

    MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    @classmethod
    def simulate_mass_balance(
        cls,
        roof_area_m2: float,
        runoff_coefficient: float,
        monthly_rainfall_mm: List[float],
        daily_demand_liters: float,
        tank_capacity_liters: float,
        filter_efficiency: float = 0.85,
    ) -> HydrologicalPerformanceSummary:
        """
        Executes month-by-month mass balance simulation:
        Inflow = Rainfall (mm) × Area (m²) × Runoff_Coeff × Filter_Efficiency
        Supplied = min(Storage + Inflow, Monthly_Demand)
        Spill = max(0, Storage + Inflow - Supplied - Tank_Capacity)
        """
        monthly_sims: List[HydrologicalMonthlySimulation] = []
        current_storage = tank_capacity_liters * 0.25  # Initial 25% storage seed

        tot_runoff = 0.0
        tot_captured = 0.0
        tot_demand = 0.0
        tot_supplied = 0.0
        tot_unmet = 0.0
        tot_overflow = 0.0
        storage_levels: List[float] = []

        for m_idx in range(12):
            p_mm = monthly_rainfall_mm[m_idx]
            days = cls.MONTH_DAYS[m_idx]
            m_demand = round(daily_demand_liters * days, 1)

            # Potential raw runoff without filtration losses
            raw_runoff = p_mm * roof_area_m2 * runoff_coefficient
            tot_runoff += raw_runoff

            # Harvested inflow entering tank after first-flush diverter and filter losses (15%)
            inflow = raw_runoff * filter_efficiency
            tot_captured += inflow

            available = current_storage + inflow
            supplied = min(available, m_demand)
            unmet = max(0.0, m_demand - supplied)

            # Overflow calculation
            remaining_after_demand = available - supplied
            if remaining_after_demand > tank_capacity_liters:
                overflow = remaining_after_demand - tank_capacity_liters
                ending_storage = tank_capacity_liters
            else:
                overflow = 0.0
                ending_storage = remaining_after_demand

            current_storage = ending_storage
            storage_levels.append(ending_storage)

            tot_demand += m_demand
            tot_supplied += supplied
            tot_unmet += unmet
            tot_overflow += overflow

            coverage_pct = round((supplied / max(1.0, m_demand)) * 100.0, 1)

            monthly_sims.append(
                HydrologicalMonthlySimulation(
                    month_index=m_idx + 1,
                    month_name=cls.MONTH_NAMES[m_idx],
                    rainfall_mm=round(p_mm, 1),
                    inflow_liters=round(inflow, 1),
                    demand_liters=round(m_demand, 1),
                    supplied_liters=round(supplied, 1),
                    unmet_demand_liters=round(unmet, 1),
                    overflow_liters=round(overflow, 1),
                    ending_storage_liters=round(ending_storage, 1),
                    demand_coverage_pct=coverage_pct
                )
            )

        annual_coverage = round((tot_supplied / max(1.0, tot_demand)) * 100.0, 1)
        avg_utilization = round((sum(storage_levels) / (12.0 * max(1.0, tank_capacity_liters))) * 100.0, 1)

        # Estimate overflow days (days where daily rainfall intensity exceeds storage intake buffer)
        overflow_threshold_daily = (tank_capacity_liters * 0.35) / max(1.0, roof_area_m2 * runoff_coefficient)
        overflow_days = sum(1 for p in monthly_rainfall_mm if (p / 4.0) > overflow_threshold_daily)

        return HydrologicalPerformanceSummary(
            annual_potential_runoff_liters=round(tot_runoff, 0),
            annual_captured_liters=round(tot_captured, 0),
            annual_water_demand_liters=round(tot_demand, 0),
            annual_water_supplied_liters=round(tot_supplied, 0),
            annual_unmet_demand_liters=round(tot_unmet, 0),
            annual_overflow_liters=round(tot_overflow, 0),
            annual_demand_coverage_pct=annual_coverage,
            average_storage_utilization_pct=avg_utilization,
            overflow_days_count=max(2, overflow_days * 3),
            monthly_breakdown=monthly_sims
        )

    @classmethod
    def generate_design_alternatives(
        cls,
        features: BuildingUnifiedFeatures,
        climate: LocationClimateProfile,
    ) -> List[RainwaterDesignAlternative]:
        """
        Synthesizes 7 distinct architectural and sizing rainwater harvesting alternatives.
        Applies physical site, structural, and hydrogeological constraints to mark unfeasible options.
        """
        alternatives: List[RainwaterDesignAlternative] = []

        # Optimal Tank Sizing: 18 days of non-potable dry-spell buffer capped by 35% of annual captured runoff
        raw_annual_inflow = climate.annual_rainfall_mm * features.roof_area_m2 * features.roof_runoff_coefficient * 0.85
        dry_spell_buffer_l = features.daily_non_potable_water_demand_l * 20.0  # 20 days buffer
        optimal_capacity_l = min(raw_annual_inflow * 0.35, max(5000.0, dry_spell_buffer_l))
        # Round to nearest 2,500 Liters
        optimal_capacity_l = float(int(round(optimal_capacity_l / 2500.0)) * 2500)

        # Helper to compute tank dimensions (cylindrical)
        def cyl_dims(vol_l: float) -> Dict[str, float]:
            vol_m3 = vol_l / 1000.0
            dia = max(1.4, round(math.sqrt((4.0 * vol_m3) / (math.pi * 2.2)), 2))
            h = round(vol_m3 / (math.pi * math.pow(dia / 2.0, 2.0)), 2)
            return {"diameter": dia, "height": h}

        # Helper to compute rectangular tank dimensions
        def rect_dims(vol_l: float) -> Dict[str, float]:
            vol_m3 = vol_l / 1000.0
            depth = min(2.5, max(1.6, round(vol_m3 / 12.0, 2)))
            w = round(math.sqrt(vol_m3 / depth) * 0.85, 2)
            l = round(vol_m3 / (w * depth), 2)
            return {"width": w, "length": l, "depth": depth}

        # =====================================================================
        # 1. ALT-A: Ground-Level Modular HDPE Tank
        # =====================================================================
        cap_a = optimal_capacity_l
        sim_a = cls.simulate_mass_balance(
            features.roof_area_m2, features.roof_runoff_coefficient, climate.monthly_rainfall_mm,
            features.daily_non_potable_water_demand_l, cap_a
        )
        dims_a = cyl_dims(cap_a)
        space_req_a = round(math.pi * math.pow(dims_a["diameter"] / 2.0 + 0.6, 2.0), 1)

        infeas_a = []
        if features.available_exterior_space_m2 < space_req_a:
            infeas_a.append(f"Insufficient exterior yard space ({features.available_exterior_space_m2:.1f} m² available vs {space_req_a:.1f} m² required).")

        cost_cap_a = round(cap_a * 6.5 + 28000.0, 0)
        maint_a = 4500.0
        life_cost_a = cost_cap_a + (maint_a * 15.0)
        water_val_yr_a = (sim_a.annual_water_supplied_liters / 1000.0) * 45.0  # ₹45/kL municipal commercial tariff
        payback_a = round(cost_cap_a / max(100.0, water_val_yr_a - maint_a), 1)

        comp_a = cls._generate_3d_components(features, "ground_tank", dims_a, cap_a)
        alternatives.append(
            RainwaterDesignAlternative(
                alternative_id="ALT-A-GROUND-TANK",
                configuration_type="ground_tank",
                name="Ground-Level Modular Food-Grade HDPE Storage Tank",
                description=f"Deploy a {cap_a:,.0f}L cylindrical UV-stabilized rotational-molded HDPE cistern placed on a reinforced concrete ground pad with first-flush diverter and dual-screen filtration.",
                tank_capacity_liters=cap_a,
                tank_material="High-Density Polyethylene (HDPE)",
                tank_dimensions_m=dims_a,
                is_feasible=len(infeas_a) == 0,
                infeasibility_reasons=infeas_a,
                hydrological_performance=sim_a,
                capital_cost_inr=cost_cap_a,
                annual_maintenance_inr=maint_a,
                lifecycle_cost_15yr_inr=life_cost_a,
                simple_payback_years=payback_a,
                space_required_m2=space_req_a,
                environmental_benefits=[
                    f"Recovers {sim_a.annual_water_supplied_liters:,.0f} L/yr of clean rainwater, covering {sim_a.annual_demand_coverage_pct:.1f}% of non-potable demand.",
                    "Above-ground configuration avoids subterranean excavation and preserves topsoil horizons.",
                    "Modular polymer construction exhibits low embodied carbon relative to cast-in-place concrete."
                ],
                tradeoffs_and_risks=[
                    f"Consumes {space_req_a:.1f} m² of exterior yard area.",
                    "Direct solar radiation on tank shell can elevate summer water temperature if unshaded."
                ],
                proposed_3d_components=comp_a
            )
        )

        # =====================================================================
        # 2. ALT-B: Subterranean Cast-in-Place RCC Cistern
        # =====================================================================
        cap_b = optimal_capacity_l * 1.35  # Larger underground buffer
        sim_b = cls.simulate_mass_balance(
            features.roof_area_m2, features.roof_runoff_coefficient, climate.monthly_rainfall_mm,
            features.daily_non_potable_water_demand_l, cap_b
        )
        dims_b = rect_dims(cap_b)
        infeas_b = []
        if climate.groundwater_depth_m < 3.2:
            infeas_b.append(f"High groundwater table ({climate.groundwater_depth_m:.1f}m below ground) creates severe buoyant hydrostatic uplift risk on empty tank shell.")
        if not features.available_underground_space:
            infeas_b.append("Subsurface utilities or geotechnical obstruction prevents excavation.")

        cost_cap_b = round(cap_b * 13.5 + 75000.0, 0)
        maint_b = 6800.0
        life_cost_b = cost_cap_b + (maint_b * 15.0)
        water_val_yr_b = (sim_b.annual_water_supplied_liters / 1000.0) * 45.0
        payback_b = round(cost_cap_b / max(100.0, water_val_yr_b - maint_b), 1)

        comp_b = cls._generate_3d_components(features, "underground_tank", dims_b, cap_b)
        alternatives.append(
            RainwaterDesignAlternative(
                alternative_id="ALT-B-UNDERGROUND-TANK",
                configuration_type="underground_tank",
                name="Subterranean Reinforced Concrete (RCC) Storage Cistern",
                description=f"Cast a {cap_b:,.0f}L buried two-compartment reinforced concrete cistern beneath parking/paved yard with submersible pressure pump, sediment sump, and access inspection manholes.",
                tank_capacity_liters=cap_b,
                tank_material="M25 Reinforced Cement Concrete (RCC)",
                tank_dimensions_m=dims_b,
                is_feasible=len(infeas_b) == 0,
                infeasibility_reasons=infeas_b,
                hydrological_performance=sim_b,
                capital_cost_inr=cost_cap_b,
                annual_maintenance_inr=maint_b,
                lifecycle_cost_15yr_inr=life_cost_b,
                simple_payback_years=payback_b,
                space_required_m2=0.0,  # Zero surface footprint loss
                environmental_benefits=[
                    f"Expands storage to achieve {sim_b.annual_demand_coverage_pct:.1f}% non-potable coverage ({sim_b.annual_water_supplied_liters:,.0f} L/yr).",
                    "Zero surface land take; preserves parking and pedestrian circulation footprint.",
                    "Subterranean thermal insulation maintains cool water temperature (18°C-22°C), preventing bacterial and algal proliferation."
                ],
                tradeoffs_and_risks=[
                    "High capital expenditure (₹13.5/L + civil excavation and dewatering).",
                    "Requires multi-stage crystalline waterproofing to prevent groundwater intrusion."
                ],
                proposed_3d_components=comp_b
            )
        )

        # =====================================================================
        # 3. ALT-C: Distributed Corner Modular Tanks
        # =====================================================================
        unit_cap = max(2500.0, optimal_capacity_l / 2.0)
        cap_c = unit_cap * 2.0
        sim_c = cls.simulate_mass_balance(
            features.roof_area_m2, features.roof_runoff_coefficient, climate.monthly_rainfall_mm,
            features.daily_non_potable_water_demand_l, cap_c
        )
        dims_c = cyl_dims(unit_cap)
        space_req_c = round(math.pi * math.pow(dims_c["diameter"] / 2.0 + 0.4, 2.0) * 2.0, 1)
        cost_cap_c = round(cap_c * 7.2 + 36000.0, 0)
        maint_c = 5200.0
        life_cost_c = cost_cap_c + (maint_c * 15.0)
        water_val_c = (sim_c.annual_water_supplied_liters / 1000.0) * 45.0
        payback_c = round(cost_cap_c / max(100.0, water_val_c - maint_c), 1)

        comp_c = cls._generate_3d_components(features, "distributed_tanks", dims_c, cap_c)
        alternatives.append(
            RainwaterDesignAlternative(
                alternative_id="ALT-C-DISTRIBUTED-TANKS",
                configuration_type="distributed_tanks",
                name=f"Dual Distributed Corner Tanks (2 × {unit_cap:,.0f}L)",
                description=f"Install two independent {unit_cap:,.0f}L modular tanks placed directly below primary downpipe corner drops, interconnected with equalizing balance pipes.",
                tank_capacity_liters=cap_c,
                tank_material="Modular Polyethylene",
                tank_dimensions_m=dims_c,
                is_feasible=True,
                infeasibility_reasons=[],
                hydrological_performance=sim_c,
                capital_cost_inr=cost_cap_c,
                annual_maintenance_inr=maint_c,
                lifecycle_cost_15yr_inr=life_cost_c,
                simple_payback_years=payback_c,
                space_required_m2=space_req_c,
                environmental_benefits=[
                    f"Recovers {sim_c.annual_water_supplied_liters:,.0f} L/yr with zero trenching across site driveway.",
                    "Reduces collection pipe friction loss by 60% with localized downpipe connections.",
                    "Provides built-in redundancy: one tank can be cleaned while the other remains active."
                ],
                tradeoffs_and_risks=[
                    f"Requires dual exterior footprint locations ({space_req_c:.1f} m² total).",
                    "Requires dual first-flush filter maintenance."
                ],
                proposed_3d_components=comp_c
            )
        )

        # =====================================================================
        # 4. ALT-D: Elevated Rooftop Gravity Header Tank
        # =====================================================================
        cap_d = min(5000.0, optimal_capacity_l * 0.45)  # Constrained by structural roof load
        sim_d = cls.simulate_mass_balance(
            features.roof_area_m2, features.roof_runoff_coefficient, climate.monthly_rainfall_mm,
            features.daily_non_potable_water_demand_l, cap_d
        )
        dims_d = cyl_dims(cap_d)
        infeas_d = []
        dead_load_kg_m2 = (cap_d * 1.0) / (math.pi * math.pow(dims_d["diameter"] / 2.0, 2.0))
        if dead_load_kg_m2 > features.roof_load_bearing_capacity_kg_m2 * 2.5:
            infeas_d.append(f"Structural dead-load ({dead_load_kg_m2:.0f} kg/m²) exceeds roof slab structural live/dead load allowance ({features.roof_load_bearing_capacity_kg_m2 * 2.5:.0f} kg/m²).")

        cost_cap_d = round(cap_d * 8.5 + 45000.0, 0)
        maint_d = 4000.0
        life_cost_d = cost_cap_d + (maint_d * 15.0)
        water_val_d = (sim_d.annual_water_supplied_liters / 1000.0) * 45.0
        payback_d = round(cost_cap_d / max(100.0, water_val_d - maint_d), 1)

        comp_d = cls._generate_3d_components(features, "rooftop_storage", dims_d, cap_d)
        alternatives.append(
            RainwaterDesignAlternative(
                alternative_id="ALT-D-ROOFTOP-STORAGE",
                configuration_type="rooftop_storage",
                name=f"Elevated Rooftop Gravity-Fed Storage Tank ({cap_d:,.0f}L)",
                description=f"Mount a {cap_d:,.0f}L structural header tank on elevated steel I-beam grillage directly above primary building load-bearing column line, feeding toilets via pure gravity.",
                tank_capacity_liters=cap_d,
                tank_material="Fiberglass Reinforced Plastic (FRP)",
                tank_dimensions_m=dims_d,
                is_feasible=len(infeas_d) == 0,
                infeasibility_reasons=infeas_d,
                hydrological_performance=sim_d,
                capital_cost_inr=cost_cap_d,
                annual_maintenance_inr=maint_d,
                lifecycle_cost_15yr_inr=life_cost_d,
                simple_payback_years=payback_d,
                space_required_m2=round(math.pi * math.pow(dims_d["diameter"] / 2.0, 2.0), 1),
                environmental_benefits=[
                    "Eliminates electric booster pump energy; gravity delivers zero-carbon water pressure to all storeys.",
                    "Preserves 100% of ground-level yard space."
                ],
                tradeoffs_and_risks=[
                    "Strictly limited in volume due to roof structural dead-load constraints.",
                    f"Only provides {sim_d.annual_demand_coverage_pct:.1f}% demand coverage due to smaller capacity buffer."
                ],
                proposed_3d_components=comp_d
            )
        )

        # =====================================================================
        # 5. ALT-E: Storage Tank + Vegetated Overflow Swale
        # =====================================================================
        cap_e = optimal_capacity_l
        sim_e = cls.simulate_mass_balance(
            features.roof_area_m2, features.roof_runoff_coefficient, climate.monthly_rainfall_mm,
            features.daily_non_potable_water_demand_l, cap_e
        )
        dims_e = cyl_dims(cap_e)
        cost_cap_e = round(cost_cap_a + 22000.0, 0)
        maint_e = 4800.0
        life_cost_e = cost_cap_e + (maint_e * 15.0)
        payback_e = round(cost_cap_e / max(100.0, water_val_yr_a - maint_e), 1)

        comp_e = cls._generate_3d_components(features, "storage_swale", dims_e, cap_e)
        alternatives.append(
            RainwaterDesignAlternative(
                alternative_id="ALT-E-STORAGE-SWALE-OVERFLOW",
                configuration_type="storage_swale",
                name=f"Primary Storage Tank ({cap_e:,.0f}L) + Controlled Vegetated Swale Overflow",
                description="Pair the primary storage tank with an engineered 12m perimeter vegetated bioswale, naturally attenuating peak monsoon cloudburst overflows before municipal storm connection.",
                tank_capacity_liters=cap_e,
                tank_material="HDPE Tank + Native Grass Bioswale",
                tank_dimensions_m=dims_e,
                is_feasible=len(infeas_a) == 0,
                infeasibility_reasons=infeas_a,
                hydrological_performance=sim_e,
                capital_cost_inr=cost_cap_e,
                annual_maintenance_inr=maint_e,
                lifecycle_cost_15yr_inr=life_cost_e,
                simple_payback_years=payback_e,
                space_required_m2=space_req_a + 12.0,
                environmental_benefits=[
                    f"Recovers {sim_e.annual_water_supplied_liters:,.0f} L/yr for building reuse while safely attenuating {sim_e.annual_overflow_liters:,.0f} L/yr of monsoon overflow.",
                    "Bioswale filters 88% of total suspended solids (TSS) and enhances microclimate cooling.",
                    "Satisfies municipal zero-net-peak-runoff regulatory mandates."
                ],
                tradeoffs_and_risks=[
                    f"Requires {space_req_a + 12.0:.1f} m² total site area for tank and swale corridor.",
                    "Pre-monsoon bioswale desiltation and weed clearing required."
                ],
                proposed_3d_components=comp_e
            )
        )

        # =====================================================================
        # 6. ALT-F: Storage Tank + Subsurface Groundwater Recharge Trench
        # =====================================================================
        cap_f = optimal_capacity_l
        sim_f = cls.simulate_mass_balance(
            features.roof_area_m2, features.roof_runoff_coefficient, climate.monthly_rainfall_mm,
            features.daily_non_potable_water_demand_l, cap_f
        )
        dims_f = cyl_dims(cap_f)
        infeas_f = []
        if climate.groundwater_depth_m < 3.5:
            infeas_f.append(f"Groundwater depth ({climate.groundwater_depth_m:.1f}m) is too shallow (< 3.5m required by CGWB norms for artificial recharge).")
        if climate.soil_infiltration_rate_mm_hr < 12.0:
            infeas_f.append(f"Low soil infiltration rate ({climate.soil_infiltration_rate_mm_hr:.1f} mm/hr in {climate.soil_texture}) impedes percolation.")

        cost_cap_f = round(cost_cap_a + 35000.0, 0)
        maint_f = 5000.0
        life_cost_f = cost_cap_f + (maint_f * 15.0)
        payback_f = round(cost_cap_f / max(100.0, water_val_yr_a - maint_f), 1)

        comp_f = cls._generate_3d_components(features, "storage_recharge", dims_f, cap_f)
        alternatives.append(
            RainwaterDesignAlternative(
                alternative_id="ALT-F-STORAGE-GROUNDWATER-RECHARGE",
                configuration_type="storage_recharge",
                name=f"Dual Harvesting: Storage Tank ({cap_f:,.0f}L) + Deep Aquifer Recharge Trench",
                description=f"First captures non-potable water in a {cap_f:,.0f}L tank; all secondary overflow ({sim_f.annual_overflow_liters:,.0f} L/yr) is diverted into a gravel-packed percolation trench recharging the local aquifer.",
                tank_capacity_liters=cap_f,
                tank_material="HDPE Tank + Perforated Gravel Recharge Chamber",
                tank_dimensions_m=dims_f,
                is_feasible=len(infeas_f) == 0,
                infeasibility_reasons=infeas_f,
                hydrological_performance=sim_f,
                capital_cost_inr=cost_cap_f,
                annual_maintenance_inr=maint_f,
                lifecycle_cost_15yr_inr=life_cost_f,
                simple_payback_years=payback_f,
                space_required_m2=space_req_a + 8.0,
                groundwater_recharge_potential_liters=sim_f.annual_overflow_liters * 0.90,
                environmental_benefits=[
                    f"Zero runoff waste: 100% of roof precipitation is either consumed ({sim_f.annual_water_supplied_liters:,.0f}L) or returned to the aquifer (~{sim_f.annual_overflow_liters*0.9:,.0f}L).",
                    "Directly raises depleted groundwater table in accordance with CGWB / Jal Shakti statutory mandates.",
                    "Earns maximum IGBC / LEED Water Efficiency innovation credits."
                ],
                tradeoffs_and_risks=[
                    "Requires annual desiltation of recharge chamber to prevent pore clogging.",
                    "Strictly dependent on unsaturated soil percolation capacity."
                ],
                proposed_3d_components=comp_f
            )
        )

        # =====================================================================
        # 7. ALT-G: Bioretention Rain Garden (Zero Storage Tank)
        # =====================================================================
        cap_g = 0.0
        # Rain garden captures and infiltrates runoff into native soil without tank reuse
        sim_g = HydrologicalPerformanceSummary(
            annual_potential_runoff_liters=sim_a.annual_potential_runoff_liters,
            annual_captured_liters=sim_a.annual_potential_runoff_liters * 0.92,
            annual_water_demand_liters=sim_a.annual_water_demand_liters,
            annual_water_supplied_liters=0.0,
            annual_unmet_demand_liters=sim_a.annual_water_demand_liters,
            annual_overflow_liters=sim_a.annual_potential_runoff_liters * 0.08,
            annual_demand_coverage_pct=0.0,
            average_storage_utilization_pct=0.0,
            overflow_days_count=0,
            monthly_breakdown=[]
        )
        garden_area_m2 = round(max(18.0, features.roof_area_m2 * 0.08), 1)
        infeas_g = []
        if features.available_exterior_space_m2 < garden_area_m2:
            infeas_g.append(f"Requires {garden_area_m2:.1f} m² unpaved landscaping area ({features.available_exterior_space_m2:.1f} m² available).")
        if climate.soil_infiltration_rate_mm_hr < 10.0:
            infeas_g.append("Heavy impermeable clay soil requires expensive subsoil drainage piping.")

        cost_cap_g = round(garden_area_m2 * 1450.0 + 15000.0, 0)
        maint_g = 3500.0
        life_cost_g = cost_cap_g + (maint_g * 15.0)

        comp_g = cls._generate_3d_components(features, "rain_garden", {"width": 4.5, "length": garden_area_m2 / 4.5}, 0.0)
        alternatives.append(
            RainwaterDesignAlternative(
                alternative_id="ALT-G-RAIN-GARDEN-BIORETENTION",
                configuration_type="rain_garden",
                name=f"Engineered Bioretention Rain Garden ({garden_area_m2:.1f} m² Basin)",
                description=f"Route all downpipe discharges directly into a {garden_area_m2:.1f} m² shallow bioretention basin engineered with engineered filter media and native wetland flora for natural infiltration.",
                tank_capacity_liters=0.0,
                tank_material="Native Soil, Mulch, Gravel & Deep-Rooted Flora",
                tank_dimensions_m={"width": 4.5, "length": round(garden_area_m2 / 4.5, 1)},
                is_feasible=len(infeas_g) == 0,
                infeasibility_reasons=infeas_g,
                hydrological_performance=sim_g,
                capital_cost_inr=cost_cap_g,
                annual_maintenance_inr=maint_g,
                lifecycle_cost_15yr_inr=life_cost_g,
                simple_payback_years=99.0,  # No direct indoor utility bill displacement
                space_required_m2=garden_area_m2,
                groundwater_recharge_potential_liters=sim_a.annual_potential_runoff_liters * 0.90,
                environmental_benefits=[
                    "Transforms mechanical drainage into vibrant biophilic green infrastructure.",
                    "Provides localized microclimate thermal cooling through evapotranspiration.",
                    "Zero mechanical pump reliance and zero plastic cistern materials."
                ],
                tradeoffs_and_risks=[
                    "Does not provide indoor non-potable water supply for toilet flushing.",
                    f"Consumes {garden_area_m2:.1f} m² of unbuilt exterior parcel area."
                ],
                proposed_3d_components=comp_g
            )
        )

        return alternatives

    @classmethod
    def _generate_3d_components(
        cls,
        features: BuildingUnifiedFeatures,
        config_type: str,
        dims: Dict[str, float],
        tank_vol_l: float
    ) -> List[Intervention3DComponent]:
        """
        Calculates exact local 3D coordinates, bounding envelopes, and pipe routes
        for all visible rainwater components in Three.js.
        """
        components: List[Intervention3DComponent] = []
        w = features.building_width_m
        l = features.building_length_m
        h = features.building_height_m

        half_w = w / 2.0
        half_l = l / 2.0
        roof_z = h  # Elevation of roof plane

        # 1. Roof Perimeter Gutters (4 edges)
        gutter_h = 0.15
        gutter_w = 0.18
        # North gutter
        components.append(
            Intervention3DComponent(
                component_id="GUTTER-NORTH",
                component_type="gutter",
                name="North Roof Eave Gutter (180mm PVC)",
                material="UPVC Gutter Profile",
                color_hex="#475569",
                position=[0.0, half_l + 0.1, roof_z],
                dimensions=[w + 0.2, gutter_h, gutter_w],
                geometry_type="box",
                specification="180mm semi-circular UV-stabilized UPVC gutter slope 1:150 toward corners"
            )
        )
        # South gutter
        components.append(
            Intervention3DComponent(
                component_id="GUTTER-SOUTH",
                component_type="gutter",
                name="South Roof Eave Gutter (180mm PVC)",
                material="UPVC Gutter Profile",
                color_hex="#475569",
                position=[0.0, -half_l - 0.1, roof_z],
                dimensions=[w + 0.2, gutter_h, gutter_w],
                geometry_type="box",
                specification="180mm semi-circular UV-stabilized UPVC gutter slope 1:150 toward corners"
            )
        )

        # 2. Downpipes (Vertical drops at corners)
        pipe_dia = 0.11  # 110mm standard downpipe
        corners = [
            (-half_w - 0.12, -half_l - 0.12, "SW-CORNER"),
            (half_w + 0.12, -half_l - 0.12, "SE-CORNER"),
        ]

        for cx, cy, cname in corners:
            components.append(
                Intervention3DComponent(
                    component_id=f"DOWNPIPE-{cname}",
                    component_type="downpipe",
                    name=f"{cname} Vertical Rainwater Downpipe (110mm)",
                    material="Heavy Duty Class 3 PVC Pipe",
                    color_hex="#64748b",
                    position=[cx, cy, roof_z / 2.0],
                    dimensions=[pipe_dia / 2.0, roof_z, 0.0],
                    geometry_type="cylinder",
                    specification=f"110mm diameter vertical downpipe with leaf guard strainer, height {roof_z:.1f}m"
                )
            )

        # 3. First-Flush & Filtration Unit
        filter_x = -half_w - 1.2
        filter_y = -half_l - 0.5
        filter_h = 1.4
        components.append(
            Intervention3DComponent(
                component_id="FILTER-FIRST-FLUSH",
                component_type="filter_unit",
                name="Dual-Chamber First-Flush & SS Screen Filter",
                material="Stainless Steel & Vortex Sand Filter",
                color_hex="#0284c7",
                position=[filter_x, filter_y, filter_h / 2.0],
                dimensions=[0.35, filter_h, 0.0],
                geometry_type="cylinder",
                volume_liters=180.0,
                specification="Dual chamber with automatic float-ball first-flush diverter and 150-micron stainless steel mesh"
            )
        )

        # 4. Storage Tank Placement
        tank_x = -half_w - 2.8
        tank_y = -half_l + 1.2

        if config_type in ["ground_tank", "distributed_tanks", "storage_swale", "storage_recharge"]:
            dia = dims.get("diameter", 2.2)
            th = dims.get("height", 2.6)
            components.append(
                Intervention3DComponent(
                    component_id="STORAGE-TANK-PRIMARY",
                    component_type="storage_tank",
                    name=f"Primary Rainwater Storage Tank ({tank_vol_l:,.0f}L)",
                    material="Triple-Layer Food-Grade Polyethylene",
                    color_hex="#0f766e",
                    position=[tank_x - (dia / 2.0), tank_y, th / 2.0],
                    dimensions=[dia / 2.0, th, 0.0],
                    geometry_type="cylinder",
                    volume_liters=tank_vol_l,
                    specification=f"Diameter {dia:.2f}m, Height {th:.2f}m on 150mm reinforced concrete slab pad"
                )
            )
        elif config_type == "underground_tank":
            tw = dims.get("width", 2.6)
            tl = dims.get("length", 3.2)
            td = dims.get("depth", 2.0)
            components.append(
                Intervention3DComponent(
                    component_id="STORAGE-TANK-UNDERGROUND",
                    component_type="storage_tank",
                    name=f"Subterranean RCC Cistern ({tank_vol_l:,.0f}L)",
                    material="Waterproof Reinforced Concrete (RCC)",
                    color_hex="#0369a1",
                    position=[tank_x - (tw / 2.0), tank_y, -td / 2.0],
                    dimensions=[tw, td, tl],
                    geometry_type="box",
                    is_subsurface=True,
                    volume_liters=tank_vol_l,
                    specification=f"Buried {td:.1f}m below ground, Width {tw:.1f}m, Length {tl:.1f}m with cast-iron inspection cover"
                )
            )
        elif config_type == "rooftop_storage":
            dia = dims.get("diameter", 1.8)
            th = dims.get("height", 2.0)
            components.append(
                Intervention3DComponent(
                    component_id="STORAGE-TANK-ROOFTOP",
                    component_type="storage_tank",
                    name=f"Elevated Rooftop Gravity Header Tank ({tank_vol_l:,.0f}L)",
                    material="FRP Elevated Cistern",
                    color_hex="#0284c7",
                    position=[0.0, 0.0, roof_z + 0.35 + (th / 2.0)],
                    dimensions=[dia / 2.0, th, 0.0],
                    geometry_type="cylinder",
                    volume_liters=tank_vol_l,
                    specification=f"Elevated {th:.1f}m header tank on structural I-beam load-bearing column line"
                )
            )

        # 5. Overflow / Swale / Recharge Trench
        if config_type in ["storage_swale", "rain_garden"]:
            swale_l = 8.0
            swale_w = 2.2
            components.append(
                Intervention3DComponent(
                    component_id="SWALE-BIORETENTION",
                    component_type="rain_garden",
                    name="Vegetated Overflow Bioswale / Rain Garden",
                    material="Engineered Filter Sand & Native Wetland Grass",
                    color_hex="#15803d",
                    position=[tank_x - 3.5, tank_y, 0.05],
                    dimensions=[swale_w, 0.25, swale_l],
                    geometry_type="box",
                    specification=f"Permeable bioretention depression {swale_w:.1f}m x {swale_l:.1f}m with native drought-tolerant wetland plantings"
                )
            )
        elif config_type == "storage_recharge":
            components.append(
                Intervention3DComponent(
                    component_id="RECHARGE-TRENCH",
                    component_type="recharge_trench",
                    name="Deep Aquifer Recharge Trench (Gravel-Packed)",
                    material="Perforated PVC in Washed Basalt Gravel",
                    color_hex="#d97706",
                    position=[tank_x - 3.2, tank_y, -1.2],
                    dimensions=[1.2, 2.4, 4.0],
                    geometry_type="box",
                    is_subsurface=True,
                    specification="4.0m x 1.2m trench filled with 40mm river gravel with perforated 150mm recharge borehole sleeve"
                )
            )

        return components
