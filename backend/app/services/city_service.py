from typing import List, Dict, Any, Optional
import math
from app.models.digital_twin import BoundingBox3D
from app.models.city import (
    CityModel,
    DistrictModel,
    SiteModel,
    CityBuildingSummary,
    InfrastructureNetwork,
)


class CityService:
    """
    Manages city-scale spatial datasets, district hierarchies,
    infrastructure networks, and spatial indexing for LOD rendering.
    """

    _cached_city: Optional[CityModel] = None

    @classmethod
    def get_default_city_model(cls) -> CityModel:
        if cls._cached_city is not None:
            return cls._cached_city

        # TechCity Innovation District — 2 Districts, 4 Sites, 8 Buildings, Roads & Networks
        buildings_district_1_site_1 = [
            CityBuildingSummary(
                building_id="BLD-HQ-01",
                name="NetZero Innovation Center (Detailed BIM)",
                typology="Commercial",
                footprint_area_m2=254.0,
                gross_floor_area_m2=508.0,
                storeys_count=2,
                height_m=10.24,
                center_x=0.0,
                center_y=0.0,
                center_z=0.0,
                width_m=14.43,
                length_m=17.60,
                has_detailed_bim=True,
                bim_model_id="sample-office-twin",
                operational_energy_intensity_kwh_m2=82.5,
                embodied_carbon_kg_co2e_m2=412.0,
                solar_pv_capacity_kw=38.4,
                occupancy_capacity=180
            ),
            CityBuildingSummary(
                building_id="BLD-TECH-02",
                name="AI & Robotics Lab Block B",
                typology="Commercial",
                footprint_area_m2=480.0,
                gross_floor_area_m2=1920.0,
                storeys_count=4,
                height_m=16.8,
                center_x=45.0,
                center_y=12.0,
                center_z=0.0,
                width_m=20.0,
                length_m=24.0,
                has_detailed_bim=False,
                bim_model_id=None,
                operational_energy_intensity_kwh_m2=96.0,
                embodied_carbon_kg_co2e_m2=485.0,
                solar_pv_capacity_kw=62.0,
                occupancy_capacity=420
            ),
        ]

        buildings_district_1_site_2 = [
            CityBuildingSummary(
                building_id="BLD-TRANSIT-03",
                name="Central Metro Mobility Hub",
                typology="Transit",
                footprint_area_m2=750.0,
                gross_floor_area_m2=1500.0,
                storeys_count=2,
                height_m=12.5,
                center_x=-48.0,
                center_y=-25.0,
                center_z=0.0,
                width_m=25.0,
                length_m=30.0,
                has_detailed_bim=False,
                bim_model_id=None,
                operational_energy_intensity_kwh_m2=65.0,
                embodied_carbon_kg_co2e_m2=520.0,
                solar_pv_capacity_kw=110.0,
                occupancy_capacity=2500
            ),
            CityBuildingSummary(
                building_id="BLD-CIVIC-04",
                name="Public Auditorium & Community Library",
                typology="Civic",
                footprint_area_m2=560.0,
                gross_floor_area_m2=1120.0,
                storeys_count=2,
                height_m=11.2,
                center_x=-25.0,
                center_y=38.0,
                center_z=0.0,
                width_m=28.0,
                length_m=20.0,
                has_detailed_bim=False,
                bim_model_id=None,
                operational_energy_intensity_kwh_m2=74.0,
                embodied_carbon_kg_co2e_m2=390.0,
                solar_pv_capacity_kw=55.0,
                occupancy_capacity=600
            ),
        ]

        buildings_district_2_site_3 = [
            CityBuildingSummary(
                building_id="BLD-RES-05",
                name="Eco-Residential Tower Alpha",
                typology="Residential",
                footprint_area_m2=420.0,
                gross_floor_area_m2=3360.0,
                storeys_count=8,
                height_m=27.5,
                center_x=95.0,
                center_y=-40.0,
                center_z=0.0,
                width_m=21.0,
                length_m=20.0,
                has_detailed_bim=False,
                bim_model_id=None,
                operational_energy_intensity_kwh_m2=58.0,
                embodied_carbon_kg_co2e_m2=370.0,
                solar_pv_capacity_kw=45.0,
                occupancy_capacity=380
            ),
            CityBuildingSummary(
                building_id="BLD-RES-06",
                name="Eco-Residential Tower Beta",
                typology="Residential",
                footprint_area_m2=420.0,
                gross_floor_area_m2=3360.0,
                storeys_count=8,
                height_m=27.5,
                center_x=130.0,
                center_y=-40.0,
                center_z=0.0,
                width_m=21.0,
                length_m=20.0,
                has_detailed_bim=False,
                bim_model_id=None,
                operational_energy_intensity_kwh_m2=56.5,
                embodied_carbon_kg_co2e_m2=365.0,
                solar_pv_capacity_kw=45.0,
                occupancy_capacity=380
            ),
        ]

        buildings_district_2_site_4 = [
            CityBuildingSummary(
                building_id="BLD-MIX-07",
                name="Sustainable Commercial Plaza & Retail Arcade",
                typology="Mixed-Use",
                footprint_area_m2=680.0,
                gross_floor_area_m2=2040.0,
                storeys_count=3,
                height_m=13.8,
                center_x=110.0,
                center_y=25.0,
                center_z=0.0,
                width_m=34.0,
                length_m=20.0,
                has_detailed_bim=False,
                bim_model_id=None,
                operational_energy_intensity_kwh_m2=88.0,
                embodied_carbon_kg_co2e_m2=440.0,
                solar_pv_capacity_kw=75.0,
                occupancy_capacity=850
            ),
            CityBuildingSummary(
                building_id="BLD-UTILITY-08",
                name="Microgrid Energy Substation & Water Treatment",
                typology="Civic",
                footprint_area_m2=320.0,
                gross_floor_area_m2=320.0,
                storeys_count=1,
                height_m=5.5,
                center_x=150.0,
                center_y=45.0,
                center_z=0.0,
                width_m=16.0,
                length_m=20.0,
                has_detailed_bim=False,
                bim_model_id=None,
                operational_energy_intensity_kwh_m2=42.0,
                embodied_carbon_kg_co2e_m2=310.0,
                solar_pv_capacity_kw=30.0,
                occupancy_capacity=15
            ),
        ]

        sites_district_1 = [
            SiteModel(
                site_id="SITE-NORTH-TECH",
                name="North Technology Campus & Innovation Core",
                boundary_polygon=[[-60.0, -20.0], [70.0, -20.0], [70.0, 50.0], [-60.0, 50.0]],
                area_m2=9100.0,
                ground_elevation_m=218.2,
                buildings=buildings_district_1_site_1,
                open_space_ratio=0.42,
                tree_canopy_coverage_pct=28.5
            ),
            SiteModel(
                site_id="SITE-CIVIC-TRANSIT",
                name="West Transit Gateway & Civic Plaza",
                boundary_polygon=[[-75.0, -50.0], [-10.0, -50.0], [-10.0, 55.0], [-75.0, 55.0]],
                area_m2=6825.0,
                ground_elevation_m=218.0,
                buildings=buildings_district_1_site_2,
                open_space_ratio=0.38,
                tree_canopy_coverage_pct=21.0
            ),
        ]

        sites_district_2 = [
            SiteModel(
                site_id="SITE-EAST-RESIDENTIAL",
                name="East Eco-Living Residential Enclave",
                boundary_polygon=[[75.0, -65.0], [160.0, -65.0], [160.0, -10.0], [75.0, -10.0]],
                area_m2=4675.0,
                ground_elevation_m=218.4,
                buildings=buildings_district_2_site_3,
                open_space_ratio=0.48,
                tree_canopy_coverage_pct=34.0
            ),
            SiteModel(
                site_id="SITE-COMMERCIAL-PLAZA",
                name="East Retail Arcade & Utility Infrastructure",
                boundary_polygon=[[80.0, 0.0], [175.0, 0.0], [175.0, 70.0], [80.0, 70.0]],
                area_m2=6650.0,
                ground_elevation_m=218.3,
                buildings=buildings_district_2_site_4,
                open_space_ratio=0.28,
                tree_canopy_coverage_pct=16.5
            ),
        ]

        districts = [
            DistrictModel(
                district_id="DIST-INNOVATION",
                name="TechCity Innovation Core District",
                district_type="Innovation Hub",
                boundary_polygon=[[-80.0, -60.0], [75.0, -60.0], [75.0, 60.0], [-80.0, 60.0]],
                total_area_hectares=1.86,
                sites=sites_district_1,
                total_buildings_count=4,
                total_population_estimate=3700,
                infrastructure_types=["Roads", "District Cooling", "Smart Power Grid", "Stormwater Swales"]
            ),
            DistrictModel(
                district_id="DIST-ECO-RESIDENTIAL",
                name="East Eco-Living & Mixed-Use District",
                district_type="Residential Quarter",
                boundary_polygon=[[75.0, -70.0], [180.0, -70.0], [180.0, 75.0], [75.0, 75.0]],
                total_area_hectares=1.52,
                sites=sites_district_2,
                total_buildings_count=4,
                total_population_estimate=1625,
                infrastructure_types=["Roads", "Microgrid Solar", "Rainwater Harvesting Network", "Bicycle Corridors"]
            ),
        ]

        # Polyline networks: Spine Road, East Access Avenue, North Transit Link
        infrastructure_networks = [
            InfrastructureNetwork(
                network_id="NET-ROAD-PRIMARY",
                name="Grand TechCity Spine Boulevard",
                network_type="Roads",
                line_segments=[
                    [[-90.0, -5.0, 0.05], [185.0, -5.0, 0.05]],
                    [[72.0, -70.0, 0.05], [72.0, 75.0, 0.05]],
                ],
                color_hex="#334155"
            ),
            InfrastructureNetwork(
                network_id="NET-POWER-MICROGRID",
                name="11kV Subsurface Microgrid Ring",
                network_type="Power Grid",
                line_segments=[
                    [[-45.0, -20.0, -1.2], [45.0, 10.0, -1.2]],
                    [[45.0, 10.0, -1.2], [110.0, 25.0, -1.2]],
                    [[110.0, 25.0, -1.2], [150.0, 45.0, -1.2]],
                ],
                color_hex="#f59e0b"
            ),
            InfrastructureNetwork(
                network_id="NET-STORMWATER-SWALE",
                name="Sustainable Urban Drainage System (SuDS) Culverts",
                network_type="Stormwater Drainage",
                line_segments=[
                    [[-70.0, -35.0, -0.6], [65.0, -35.0, -0.6]],
                    [[65.0, -35.0, -0.6], [165.0, -35.0, -0.6]],
                ],
                color_hex="#0284c7"
            ),
        ]

        total_gfa = sum(
            b.gross_floor_area_m2
            for d in districts
            for s in d.sites
            for b in s.buildings
        )

        bbox = BoundingBox3D(
            min_x=-95.0,
            max_x=190.0,
            min_y=-75.0,
            max_y=80.0,
            min_z=0.0,
            max_z=28.0,
            width=285.0,
            height=155.0,
            depth=28.0,
            center_x=47.5,
            center_y=2.5,
            center_z=14.0
        )

        city = CityModel(
            city_id="city-techcity-smart-district",
            name="TechCity Smart Innovation District & Urban Campus",
            crs="EPSG:4326 (WGS84)",
            origin_latitude=28.6139,
            origin_longitude=77.2090,
            bounding_box=bbox,
            districts=districts,
            infrastructure_networks=infrastructure_networks,
            total_gfa_m2=total_gfa,
            total_buildings=8,
            spatial_index_bounds={
                "min_x": -95.0, "max_x": 190.0,
                "min_y": -75.0, "max_y": 80.0,
                "grid_cell_size_m": 50.0
            }
        )

        cls._cached_city = city
        return city

    @classmethod
    def get_building_by_id(cls, building_id: str) -> Optional[CityBuildingSummary]:
        city = cls.get_default_city_model()
        for d in city.districts:
            for s in d.sites:
                for b in s.buildings:
                    if b.building_id.lower() == building_id.lower():
                        return b
        return None
