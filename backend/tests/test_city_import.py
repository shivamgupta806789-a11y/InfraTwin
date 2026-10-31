import pytest
import io
import json
import zipfile
from fastapi.testclient import TestClient
from app.main import app
from app.services.city_import_service import CityImportService
from app.services.ifc_parser import IfcParserService

client = TestClient(app)


def test_supported_formats():
    response = client.get("/api/v1/city/supported-formats")
    assert response.status_code == 200
    data = response.json()
    assert ".geojson" in data
    assert ".cityjson" in data
    assert ".zip" in data
    assert ".gpkg" in data
    assert ".dxf" in data


def test_import_geojson_file():
    sample_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [77.2090, 28.6139],
                        [77.2095, 28.6139],
                        [77.2095, 28.6143],
                        [77.2090, 28.6143],
                        [77.2090, 28.6139],
                    ]]
                },
                "properties": {
                    "id": "BLD-GEO-TEST",
                    "name": "Civic Innovation Lab",
                    "height": 18.5,
                    "building:levels": 5,
                    "building": "commercial"
                }
            }
        ]
    }
    file_bytes = json.dumps(sample_geojson).encode("utf-8")
    response = client.post(
        "/api/v1/city/import-file",
        files={"file": ("test_district.geojson", file_bytes, "application/geo+json")},
        data={"district_name": "Test Innovation Hub", "district_type": "Innovation Hub"}
    )
    assert response.status_code == 200
    city = response.json()
    assert "city_id" in city
    assert any(d["name"] == "Test Innovation Hub" for d in city["districts"])


def test_restore_sample_city():
    response = client.post("/api/v1/city/restore-sample")
    assert response.status_code == 200
    city = response.json()
    assert "TechCity" in city["name"]
    assert len(city["districts"]) >= 2


def test_ifc4x3_rc2_schema_support(tmp_path):
    rc2_content = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('test_bridge_infra.ifc','2026-10-31T00:00:00',('InfraTwinAI'),('InfraTwinAI Corp'),'IfcOpenShell','IfcOpenShell','');
FILE_SCHEMA(('IFC4X3_RC2'));
ENDSEC;
DATA;
#1=IFCPROJECT('2vBw0_0000000000000001',$,'Civil Infrastructure Project',$,$,$,$,(#10),#20);
#10=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#11,$);
#11=IFCAXIS2PLACEMENT3D(#12,#13,#14);
#12=IFCCARTESIANPOINT((0.,0.,0.));
#13=IFCDIRECTION((0.,0.,1.));
#14=IFCDIRECTION((1.,0.,0.));
#20=IFCUNITASSIGNMENT((#21));
#21=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);
#30=IFCSITE('2vBw0_0000000000000002',$,'Infra Site',$,$,#40,$,$,.ELEMENT.,(28,36,50,40000),(77,12,32,40000),216.5,$,$);
#40=IFCLOCALPLACEMENT($,#11);
#50=IFCBUILDING('2vBw0_0000000000000003',$,'Station Headhouse',$,$,#40,$,$,.ELEMENT.,$,$,$);
#60=IFCRELAGGREGATES('2vBw0_0000000000000004',$,$,$,#1,(#30));
#61=IFCRELAGGREGATES('2vBw0_0000000000000005',$,$,$,#30,(#50));
ENDSEC;
END-ISO-10303-21;
"""
    test_file = tmp_path / "test_rc2.ifc"
    test_file.write_text(rc2_content, encoding="utf-8")

    detail, warnings, missing = IfcParserService.parse_ifc_file(str(test_file), "test_rc2.ifc")

    assert detail.schema_version == "IFC4X3_RC2"
    assert detail.building_name == "Station Headhouse"
    assert detail.georeferencing is not None
    assert detail.georeferencing.get("has_ifc_georeferencing") is True
    assert pytest.approx(detail.georeferencing.get("ref_latitude"), 0.001) == 28.614
    assert pytest.approx(detail.georeferencing.get("ref_longitude"), 0.001) == 77.209
    assert detail.georeferencing.get("ref_elevation_m") == 216.5
