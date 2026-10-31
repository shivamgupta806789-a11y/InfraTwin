import os
import csv
import random
import math
from typing import List, Dict, Any, Tuple
from app.services.location_climate_service import LocationClimateService


class RainwaterDatasetGenerator:
    """
    Reproducible dataset generation pipeline for building-specific rainwater harvesting.
    Generates 1,200 diverse building records across 6 major climatological archetypes,
    varying roof geometry, building occupancy, materials, and storage capacities.
    Every record carries transparent physical mass-balance labels and provenance metadata.
    """

    OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    CSV_PATH = os.path.join(OUTPUT_DIR, "rainwater_dataset.csv")

    RUNOFF_COEFFS = {
        "metal_sheet": 0.90,
        "polycarbonate": 0.90,
        "concrete_slab": 0.80,
        "asphalt_shingle": 0.78,
        "clay_tile": 0.75,
        "green_roof": 0.40,
    }

    BUILDING_TYPES = ["Commercial", "Residential", "Mixed-Use", "Educational", "Civic"]

    @classmethod
    def generate_and_save_dataset(cls, num_samples: int = 1200, random_seed: int = 42) -> str:
        """
        Generates and saves the dataset to CSV.
        Returns the absolute filepath of the generated CSV.
        """
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        random.seed(random_seed)

        archetypes = list(LocationClimateService.REGIONAL_CLIMATE_NORMALS.keys())

        headers = [
            "record_id",
            "building_type",
            "climate_archetype",
            "roof_catchment_area_m2",
            "roof_material",
            "roof_slope_deg",
            "roof_orientation_deg",
            "roof_runoff_coefficient",
            "storeys_count",
            "occupancy_count",
            "daily_non_potable_demand_l",
            "tank_capacity_l",
            "annual_rainfall_mm",
            "rainfall_seasonality_index",
            "rainfall_intensity_2yr_mm_hr",
            "terrain_slope_pct",
            "soil_infiltration_rate_mm_hr",
            "groundwater_depth_m",
            # TARGETS (Ground Truth from Physical Mass Balance Simulation)
            "target_annual_captured_l",
            "target_annual_demand_coverage_pct",
            "target_storage_utilization_pct",
            "target_annual_overflow_l",
            "target_overflow_days_count",
            "target_lifecycle_cost_inr",
            # Metadata
            "label_type",
            "generation_method",
            "provenance"
        ]

        rows = []

        for i in range(num_samples):
            rec_id = f"RWH-SYN-{i+1:04d}"
            b_type = random.choice(cls.BUILDING_TYPES)
            archetype = archetypes[i % len(archetypes)]
            clim = LocationClimateService.REGIONAL_CLIMATE_NORMALS[archetype]

            # Features
            roof_area = round(random.uniform(80.0, 3500.0), 1)
            mat = random.choice(list(cls.RUNOFF_COEFFS.keys()))
            c = cls.RUNOFF_COEFFS[mat]
            slope = round(random.uniform(1.0, 30.0), 1)
            orientation = round(random.choice([0.0, 90.0, 180.0, 270.0]), 1)
            storeys = random.randint(1, 10)

            # Occupancy & Demand
            if b_type == "Commercial":
                occ = max(10, int(roof_area * storeys / random.uniform(10.0, 16.0)))
                daily_demand = round(occ * 25.0, 1)  # 25 lpcd non-potable
            elif b_type == "Residential":
                occ = max(4, int(roof_area * storeys / random.uniform(25.0, 40.0)))
                daily_demand = round(occ * 55.0, 1)  # 55 lpcd non-potable
            else:
                occ = max(8, int(roof_area * storeys / random.uniform(12.0, 22.0)))
                daily_demand = round(occ * 35.0, 1)

            # Tank capacity: range from 2,000L to 80,000L
            tank_cap = float(random.choice([2500, 5000, 7500, 10000, 15000, 20000, 30000, 40000, 50000, 75000]))

            annual_rain = clim["annual_rainfall_mm"]
            monthly_rain = clim["monthly_rainfall_mm"]
            wettest_4 = sum(sorted(monthly_rain, reverse=True)[:4])
            seasonality = round(wettest_4 / max(1.0, annual_rain), 2)

            terrain_slope = round(random.uniform(0.5, 6.0), 1)
            soil_infilt = clim["infiltration_rate_mm_hr"] * random.uniform(0.85, 1.15)
            gw_depth = clim["groundwater_m"] * random.uniform(0.8, 1.25)

            # Physical mass-balance monthly simulation
            month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            current_storage = tank_cap * 0.20
            tot_captured = 0.0
            tot_demand = 0.0
            tot_supplied = 0.0
            tot_overflow = 0.0
            storage_tracker = []

            for m in range(12):
                p = monthly_rain[m]
                m_demand = daily_demand * month_days[m]
                inflow = p * roof_area * c * 0.85  # 85% collection efficiency after first flush
                tot_captured += inflow

                available = current_storage + inflow
                supplied = min(available, m_demand)
                rem = available - supplied
                if rem > tank_cap:
                    overflow = rem - tank_cap
                    end_store = tank_cap
                else:
                    overflow = 0.0
                    end_store = rem

                current_storage = end_store
                storage_tracker.append(end_store)
                tot_demand += m_demand
                tot_supplied += supplied
                tot_overflow += overflow

            coverage_pct = round((tot_supplied / max(1.0, tot_demand)) * 100.0, 1)
            utilization_pct = round((sum(storage_tracker) / (12.0 * max(1.0, tank_cap))) * 100.0, 1)

            # Overflow days
            overflow_threshold_daily = (tank_cap * 0.35) / max(1.0, roof_area * c)
            of_days = max(1, sum(3 for p in monthly_rain if (p / 4.0) > overflow_threshold_daily))

            # Lifecycle cost (CapEx + 15-yr OpEx)
            cap_cost = tank_cap * 7.5 + (roof_area * 15.0) + 30000.0
            lifecycle_cost = round(cap_cost + (4500.0 * 15.0), 0)

            rows.append([
                rec_id,
                b_type,
                archetype,
                roof_area,
                mat,
                slope,
                orientation,
                round(c, 2),
                storeys,
                occ,
                daily_demand,
                tank_cap,
                round(annual_rain, 1),
                seasonality,
                clim["intensity_2yr_mm_hr"],
                terrain_slope,
                round(soil_infilt, 1),
                round(gw_depth, 1),
                round(tot_captured, 0),
                coverage_pct,
                utilization_pct,
                round(tot_overflow, 0),
                of_days,
                lifecycle_cost,
                "SIMULATED_PHYSICAL_GROUND_TRUTH",
                "PHYSICAL_MASS_BALANCE_SIMULATION_V1",
                "InfraTwinAI Synthetic Climatological Archetypes (WMO/IMD 1991-2020 Normals)"
            ])

        with open(cls.CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

        return cls.CSV_PATH
