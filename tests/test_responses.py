import glob
import os
import pytest
from pathlib import Path
from typing import Dict, Any

# These will be imported from the schemas repository
from schemas.python.can_frame import CANIDFormat
from schemas.python.json_formatter import format_file
from schemas.python.signals_testing import obd_testrunner

REPO_ROOT = Path(__file__).parent.parent.absolute()

TEST_CASES = [
    {
        "model_year": "2024",
        "signalset": "default.json",
        "tests": [
            # State of charge
            ("7DA04621F5B96", {"COROLLAHYBRID_SOC": 58.8235294117647}),
            ("7DA04621F5BB3", {"COROLLAHYBRID_SOC": 70.19607843137256}),

            # State of charge
            ("7C805621022086B", {"COROLLAHYBRID_FLV": 21.55}),
            ("7C8056210220BA9", {"COROLLAHYBRID_FLV": 29.85}),
            ("7C805621022FFFF", {"COROLLAHYBRID_FLV": 100}),

            # Tire positions
            ("""
7582A10086220210403
7582A21020100000000
             """, {
                 "COROLLAHYBRID_TID_1": "RR",
                 "COROLLAHYBRID_TID_2": "RL",
                 "COROLLAHYBRID_TID_3": "FR",
                 "COROLLAHYBRID_TID_4": "FL",
                 }),

            # Tire temperatures
            ("""
7582A10086210040000
7582A21000000000000
             """, {
                 "COROLLAHYBRID_TT_1": -30,
                 "COROLLAHYBRID_TT_2": -30,
                 "COROLLAHYBRID_TT_3": -30,
                 "COROLLAHYBRID_TT_4": -30,
                 }),
            ("""
7582A10086210043E3C
7582A21403F00000000
             """, {
                 "COROLLAHYBRID_TT_1": 22,
                 "COROLLAHYBRID_TT_2": 20,
                 "COROLLAHYBRID_TT_3": 24,
                 "COROLLAHYBRID_TT_4": 23,
                 }),

            # Tire pressures
            ("""
7582A100D6210050000
7582A21000000000000
7582A22000000000000
             """, {
                 "COROLLAHYBRID_TP_1": 0,
                 "COROLLAHYBRID_TP_2": 0,
                 "COROLLAHYBRID_TP_3": 0,
                 "COROLLAHYBRID_TP_4": 0,
                 }),
            ("""
7582A100D621005009E
7582A21009D00A600A4
7582A22000000000000
             """, {
                 "COROLLAHYBRID_TP_1": 32.6060606030303,
                 "COROLLAHYBRID_TP_2": 32.363636360606066,
                 "COROLLAHYBRID_TP_3": 34.54545454242424,
                 "COROLLAHYBRID_TP_4": 34.060606057575754,
                 }),
        ]
    },
]

def load_signalset(filename: str) -> str:
    """Load a signalset JSON file from the standard location."""
    signalset_path = REPO_ROOT / "signalsets" / "v3" / filename
    with open(signalset_path) as f:
        return f.read()

@pytest.mark.parametrize(
    "test_group",
    TEST_CASES,
    ids=lambda test_case: f"MY{test_case['model_year']}"
)
def test_signals(test_group: Dict[str, Any]):
    """Test signal decoding against known responses."""
    signalset_json = load_signalset(test_group["signalset"])

    # Run each test case in the group
    for response_hex, expected_values in test_group["tests"]:
        try:
            obd_testrunner(
                signalset_json,
                response_hex,
                expected_values,
                can_id_format=CANIDFormat.ELEVEN_BIT,
                extended_addressing_enabled=response_hex.strip().startswith('758')
            )
        except Exception as e:
            pytest.fail(
                f"Failed on response {response_hex} "
                f"(Model Year: {test_group['model_year']}, "
                f"Signalset: {test_group['signalset']}): {e}"
            )

def get_json_files():
    """Get all JSON files from the signalsets/v3 directory."""
    signalsets_path = os.path.join(REPO_ROOT, 'signalsets', 'v3')
    json_files = glob.glob(os.path.join(signalsets_path, '*.json'))
    # Convert full paths to relative filenames
    return [os.path.basename(f) for f in json_files]

@pytest.mark.parametrize("test_file",
    get_json_files(),
    ids=lambda x: x.split('.')[0].replace('-', '_')  # Create readable test IDs
)
def test_formatting(test_file):
    """Test signal set formatting for all vehicle models in signalsets/v3/."""
    signalset_path = os.path.join(REPO_ROOT, 'signalsets', 'v3', test_file)

    formatted = format_file(signalset_path)

    with open(signalset_path) as f:
        assert f.read() == formatted

if __name__ == '__main__':
    pytest.main([__file__])
