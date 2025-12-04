import pytest

from src.agents.records_agent import RecordsAgent
from src.models.model_client import ModelClient, ModelResponse


class MockModelClient(ModelClient):
    async def generate(self, *args, **kwargs):
        return ModelResponse(content="ok", model="mock")

    async def generate_structured(self, *args, **kwargs):
        return {"mock": True}


@pytest.fixture
def records_agent():
    return RecordsAgent(model_client=MockModelClient())


@pytest.mark.asyncio
async def test_get_patient_by_dob(records_agent):
    patient = records_agent.get_patient_by_dob("Alicia Thompson", "1985-04-12")
    assert patient is not None
    assert patient["id"] == "P-1001"


def test_get_upcoming_appointments(records_agent):
    appointments = records_agent.get_upcoming_appointments("P-1001")
    assert appointments  # should include at least one future appointment
    for appt in appointments:
        assert appt["status"] == "scheduled"


def test_medications_and_labs(records_agent):
    meds = records_agent.get_medications("P-1002")
    labs = records_agent.get_lab_results("P-1002")
    assert any(m["name"] == "Metformin" for m in meds)
    assert any(l["test_name"] == "Hemoglobin A1C" for l in labs)


@pytest.mark.asyncio
async def test_execute_dispatch(records_agent):
    result = await records_agent.execute({
        "action": "get_visit_notes",
        "patient_id": "P-1003"
    })
    assert result.is_success
    assert result.output["visit_notes"]


# New patient registration tests


def test_generate_patient_id(records_agent):
    """Test sequential patient ID generation."""
    patient_id = records_agent._generate_patient_id()
    assert patient_id.startswith("P-")
    # Should be P-1005 since mock data has P-1001 through P-1004
    assert patient_id == "P-1005"


def test_check_duplicate_existing_patient(records_agent):
    """Test duplicate detection for existing patient."""
    is_duplicate = records_agent.check_duplicate("Alicia Thompson", "1985-04-12")
    assert is_duplicate is True


def test_check_duplicate_new_patient(records_agent):
    """Test no duplicate for new patient."""
    is_duplicate = records_agent.check_duplicate("John Smith", "1990-01-01")
    assert is_duplicate is False


def test_check_duplicate_case_insensitive(records_agent):
    """Test duplicate detection is case-insensitive."""
    is_duplicate = records_agent.check_duplicate("ALICIA THOMPSON", "1985-04-12")
    assert is_duplicate is True


def test_create_patient_success(records_agent, tmp_path):
    """Test successful patient creation."""
    # Use temp directory for test to avoid modifying real data
    from src.utils.data_loader import DataLoader
    test_data_loader = DataLoader(data_dir=tmp_path)

    # Create temp patients.json
    import json
    with open(tmp_path / "patients.json", "w") as f:
        json.dump({"patients": records_agent.patients.copy()}, f)

    # Set test data loader
    original_loader = records_agent.data_loader
    records_agent.data_loader = test_data_loader

    try:
        # Create new patient
        new_patient = records_agent.create_patient(
            name="Sarah Johnson",
            dob="1990-03-15",
            phone="4155550199",
            email="sarah@example.com"
        )

        # Verify patient created
        assert new_patient["id"] == "P-1005"
        assert new_patient["name"] == "Sarah Johnson"
        assert new_patient["dob"] == "1990-03-15"
        assert new_patient["contact"]["phone"] == "+1-415-555-0199"
        assert new_patient["contact"]["email"] == "sarah@example.com"
        assert new_patient["appointments"] == []
        assert new_patient["medications"] == []

        # Verify added to in-memory list
        assert len(records_agent.patients) == 5

        # Verify persisted to file
        with open(tmp_path / "patients.json", "r") as f:
            data = json.load(f)
            assert len(data["patients"]) == 5
            assert data["patients"][-1]["id"] == "P-1005"

    finally:
        # Restore original data loader
        records_agent.data_loader = original_loader


def test_create_patient_invalid_name(records_agent):
    """Test patient creation with invalid name."""
    with pytest.raises(ValueError, match="first and last"):
        records_agent.create_patient(
            name="John",  # No last name
            dob="1990-01-01",
            phone="4155550199",
            email="john@example.com"
        )


def test_create_patient_invalid_phone(records_agent):
    """Test patient creation with invalid phone."""
    with pytest.raises(ValueError, match="10-digit"):
        records_agent.create_patient(
            name="John Smith",
            dob="1990-01-01",
            phone="123",  # Too short
            email="john@example.com"
        )


def test_create_patient_invalid_email(records_agent):
    """Test patient creation with invalid email."""
    with pytest.raises(ValueError, match="valid email"):
        records_agent.create_patient(
            name="John Smith",
            dob="1990-01-01",
            phone="4155550199",
            email="invalid"  # No @ or domain
        )


def test_create_patient_duplicate(records_agent):
    """Test patient creation with duplicate name and DOB."""
    with pytest.raises(ValueError, match="already exists"):
        records_agent.create_patient(
            name="Alicia Thompson",
            dob="1985-04-12",
            phone="4155550199",
            email="alicia@example.com"
        )


@pytest.mark.asyncio
async def test_execute_create_patient(records_agent, tmp_path):
    """Test create_patient via execute method."""
    # Use temp directory for test
    from src.utils.data_loader import DataLoader
    test_data_loader = DataLoader(data_dir=tmp_path)

    # Create temp patients.json
    import json
    with open(tmp_path / "patients.json", "w") as f:
        json.dump({"patients": records_agent.patients.copy()}, f)

    # Set test data loader
    original_loader = records_agent.data_loader
    records_agent.data_loader = test_data_loader

    try:
        result = await records_agent.execute({
            "action": "create_patient",
            "name": "Marcus Chen",
            "dob": "1988-06-08",
            "phone": "6505550123",
            "email": "marcus@example.com"
        })

        assert result.is_success
        assert result.output["patient"]["id"] == "P-1005"
        assert result.output["patient"]["name"] == "Marcus Chen"

    finally:
        records_agent.data_loader = original_loader

