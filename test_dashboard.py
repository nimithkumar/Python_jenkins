"""
Unit Tests for COVID-19 & Indian Voters Dashboard
===================================================
Run with:
    pip install pytest httpx
    pytest test_dashboard.py -v

Or with coverage:
    pip install pytest-cov
    pytest test_dashboard.py -v --cov=main --cov-report=term-missing
"""

import pytest
from fastapi.testclient import TestClient
from main import (
    app,
    generate_covid_data,
    generate_voter_data,
    COVID_DATA,
    VOTER_DATA,
    STATES,
)

# ─────────────────────────────────────────────
# 🔧 TEST CLIENT SETUP
# ─────────────────────────────────────────────

client = TestClient(app)


# ═══════════════════════════════════════════════════════
# 🧪 SECTION 1: DATA GENERATION TESTS
# ═══════════════════════════════════════════════════════

class TestGenerateCovidData:
    """Tests for the generate_covid_data() function."""

    def setup_method(self):
        self.data = generate_covid_data()

    def test_returns_list(self):
        assert isinstance(self.data, list)

    def test_correct_number_of_states(self):
        assert len(self.data) == len(STATES)

    def test_all_states_present(self):
        state_names = [d["state"] for d in self.data]
        for state in STATES:
            assert state in state_names, f"Missing state: {state}"

    def test_required_fields_present(self):
        required = {"state", "total_cases", "active_cases", "recovered", "deaths", "vaccinated", "vaccination_pct"}
        for entry in self.data:
            assert required.issubset(entry.keys()), f"Missing fields in: {entry}"

    def test_total_cases_positive(self):
        for d in self.data:
            assert d["total_cases"] > 0, f"Non-positive total_cases for {d['state']}"

    def test_active_cases_non_negative(self):
        for d in self.data:
            assert d["active_cases"] >= 0

    def test_deaths_non_negative(self):
        for d in self.data:
            assert d["deaths"] >= 0

    def test_recovered_non_negative(self):
        for d in self.data:
            assert d["recovered"] >= 0

    def test_cases_conservation(self):
        """active + deaths + recovered should equal total_cases."""
        for d in self.data:
            computed = d["active_cases"] + d["deaths"] + d["recovered"]
            assert computed == d["total_cases"], (
                f"{d['state']}: {d['active_cases']} + {d['deaths']} + "
                f"{d['recovered']} != {d['total_cases']}"
            )

    def test_vaccination_pct_in_valid_range(self):
        for d in self.data:
            assert 0 <= d["vaccination_pct"] <= 100, (
                f"{d['state']} has invalid vaccination_pct: {d['vaccination_pct']}"
            )

    def test_vaccination_pct_calculation(self):
        """vaccination_pct should match vaccinated / total_cases * 100."""
        for d in self.data:
            expected = round(d["vaccinated"] / d["total_cases"] * 100, 1)
            assert d["vaccination_pct"] == expected

    def test_vaccinated_within_total_cases(self):
        for d in self.data:
            assert d["vaccinated"] <= d["total_cases"], (
                f"{d['state']}: vaccinated > total_cases"
            )


class TestGenerateVoterData:
    """Tests for the generate_voter_data() function."""

    def setup_method(self):
        self.data = generate_voter_data()

    def test_returns_list(self):
        assert isinstance(self.data, list)

    def test_correct_number_of_states(self):
        assert len(self.data) == len(STATES)

    def test_all_states_present(self):
        state_names = [d["state"] for d in self.data]
        for state in STATES:
            assert state in state_names

    def test_required_fields_present(self):
        required = {"state", "total_voters", "male_voters", "female_voters",
                    "turnout_pct", "young_voters", "young_voter_pct"}
        for entry in self.data:
            assert required.issubset(entry.keys())

    def test_total_voters_positive(self):
        for d in self.data:
            assert d["total_voters"] > 0

    def test_male_plus_female_equals_total(self):
        for d in self.data:
            assert d["male_voters"] + d["female_voters"] == d["total_voters"], (
                f"{d['state']}: male + female != total"
            )

    def test_turnout_pct_in_range(self):
        for d in self.data:
            assert 0 <= d["turnout_pct"] <= 100, (
                f"{d['state']} has invalid turnout: {d['turnout_pct']}"
            )

    def test_young_voter_pct_in_range(self):
        for d in self.data:
            assert 0 <= d["young_voter_pct"] <= 100

    def test_young_voters_within_total(self):
        for d in self.data:
            assert d["young_voters"] <= d["total_voters"]

    def test_young_voter_pct_matches(self):
        for d in self.data:
            expected = round(d["young_voters"] / d["total_voters"] * 100, 1)
            assert d["young_voter_pct"] == expected

    def test_uttar_pradesh_largest_voter_base(self):
        """UP should have the largest voter base as per voter_bases dict."""
        up = next(d for d in self.data if d["state"] == "Uttar Pradesh")
        assert up["total_voters"] == 152_000_000


# ═══════════════════════════════════════════════════════
# 🌐 SECTION 2: API ENDPOINT TESTS
# ═══════════════════════════════════════════════════════

class TestDashboardRoute:
    """Tests for the HTML dashboard route."""

    def test_dashboard_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200

    def test_dashboard_returns_html(self):
        response = client.get("/")
        assert "text/html" in response.headers["content-type"]

    def test_dashboard_contains_title(self):
        response = client.get("/")
        assert "COVID-19" in response.text
        assert "Voters" in response.text

    def test_dashboard_has_plotly_script(self):
        response = client.get("/")
        assert "plotly" in response.text.lower()

    def test_dashboard_has_api_calls(self):
        response = client.get("/")
        assert "/api/covid" in response.text
        assert "/api/voters" in response.text


class TestCovidEndpoint:
    """Tests for GET /api/covid"""

    def test_returns_200(self):
        response = client.get("/api/covid")
        assert response.status_code == 200

    def test_returns_json_list(self):
        response = client.get("/api/covid")
        data = response.json()
        assert isinstance(data, list)

    def test_returns_all_states(self):
        response = client.get("/api/covid")
        assert len(response.json()) == len(STATES)

    def test_each_entry_has_required_fields(self):
        response = client.get("/api/covid")
        required = {"state", "total_cases", "active_cases", "recovered", "deaths", "vaccinated", "vaccination_pct"}
        for entry in response.json():
            assert required.issubset(entry.keys())

    def test_data_types_correct(self):
        response = client.get("/api/covid")
        for entry in response.json():
            assert isinstance(entry["state"], str)
            assert isinstance(entry["total_cases"], int)
            assert isinstance(entry["vaccination_pct"], float)

    def test_content_type_is_json(self):
        response = client.get("/api/covid")
        assert "application/json" in response.headers["content-type"]


class TestVotersEndpoint:
    """Tests for GET /api/voters"""

    def test_returns_200(self):
        response = client.get("/api/voters")
        assert response.status_code == 200

    def test_returns_json_list(self):
        response = client.get("/api/voters")
        assert isinstance(response.json(), list)

    def test_returns_all_states(self):
        response = client.get("/api/voters")
        assert len(response.json()) == len(STATES)

    def test_each_entry_has_required_fields(self):
        response = client.get("/api/voters")
        required = {"state", "total_voters", "male_voters", "female_voters",
                    "turnout_pct", "young_voters", "young_voter_pct"}
        for entry in response.json():
            assert required.issubset(entry.keys())

    def test_data_types_correct(self):
        response = client.get("/api/voters")
        for entry in response.json():
            assert isinstance(entry["state"], str)
            assert isinstance(entry["total_voters"], int)
            assert isinstance(entry["turnout_pct"], float)


class TestSummaryEndpoint:
    """Tests for GET /api/summary"""

    def test_returns_200(self):
        response = client.get("/api/summary")
        assert response.status_code == 200

    def test_has_covid_and_voters_keys(self):
        data = client.get("/api/summary").json()
        assert "covid" in data
        assert "voters" in data

    def test_covid_summary_fields(self):
        data = client.get("/api/summary").json()["covid"]
        required = {"total_cases", "total_deaths", "total_recovered",
                    "total_active", "total_vaccinated", "recovery_rate", "fatality_rate"}
        assert required.issubset(data.keys())

    def test_voters_summary_fields(self):
        data = client.get("/api/summary").json()["voters"]
        assert "total_voters" in data
        assert "avg_turnout" in data

    def test_recovery_rate_plus_fatality_rate_under_100(self):
        data = client.get("/api/summary").json()["covid"]
        assert data["recovery_rate"] + data["fatality_rate"] <= 100

    def test_recovery_rate_in_valid_range(self):
        data = client.get("/api/summary").json()["covid"]
        assert 0 <= data["recovery_rate"] <= 100

    def test_fatality_rate_in_valid_range(self):
        data = client.get("/api/summary").json()["covid"]
        assert 0 <= data["fatality_rate"] <= 100

    def test_avg_turnout_in_valid_range(self):
        data = client.get("/api/summary").json()["voters"]
        assert 0 <= data["avg_turnout"] <= 100

    def test_totals_match_individual_data(self):
        """Summary totals should match sum of per-state data."""
        summary = client.get("/api/summary").json()
        covid_list = client.get("/api/covid").json()
        expected_cases = sum(d["total_cases"] for d in covid_list)
        assert summary["covid"]["total_cases"] == expected_cases

    def test_voter_total_matches_individual(self):
        summary = client.get("/api/summary").json()
        voter_list = client.get("/api/voters").json()
        expected = sum(d["total_voters"] for d in voter_list)
        assert summary["voters"]["total_voters"] == expected


class TestStateCOVIDEndpoint:
    """Tests for GET /api/covid/{state}"""

    def test_valid_state_returns_200(self):
        response = client.get("/api/covid/Maharashtra")
        assert response.status_code == 200

    def test_case_insensitive_lookup(self):
        response = client.get("/api/covid/maharashtra")
        assert response.status_code == 200

    def test_returns_correct_state(self):
        response = client.get("/api/covid/Delhi")
        data = response.json()
        assert data["state"] == "Delhi"

    def test_invalid_state_returns_404(self):
        response = client.get("/api/covid/Atlantis")
        assert response.status_code == 404

    def test_invalid_state_returns_error_key(self):
        response = client.get("/api/covid/Atlantis")
        assert "error" in response.json()

    def test_returns_all_covid_fields(self):
        response = client.get("/api/covid/Kerala")
        data = response.json()
        required = {"state", "total_cases", "active_cases", "recovered",
                    "deaths", "vaccinated", "vaccination_pct"}
        assert required.issubset(data.keys())

    @pytest.mark.parametrize("state", ["Uttar Pradesh", "Tamil Nadu", "Gujarat", "Delhi", "Punjab"])
    def test_multiple_states(self, state):
        response = client.get(f"/api/covid/{state}")
        assert response.status_code == 200
        assert response.json()["state"] == state


class TestStateVotersEndpoint:
    """Tests for GET /api/voters/{state}"""

    def test_valid_state_returns_200(self):
        response = client.get("/api/voters/Karnataka")
        assert response.status_code == 200

    def test_case_insensitive_lookup(self):
        response = client.get("/api/voters/karnataka")
        assert response.status_code == 200

    def test_returns_correct_state(self):
        response = client.get("/api/voters/Kerala")
        assert response.json()["state"] == "Kerala"

    def test_invalid_state_returns_404(self):
        response = client.get("/api/voters/Narnia")
        assert response.status_code == 404

    def test_invalid_state_has_error_message(self):
        response = client.get("/api/voters/Narnia")
        assert "error" in response.json()

    def test_returns_all_voter_fields(self):
        response = client.get("/api/voters/Bihar")
        data = response.json()
        required = {"state", "total_voters", "male_voters", "female_voters",
                    "turnout_pct", "young_voters", "young_voter_pct"}
        assert required.issubset(data.keys())

    @pytest.mark.parametrize("state", ["Bihar", "Rajasthan", "Assam", "Haryana"])
    def test_multiple_states(self, state):
        response = client.get(f"/api/voters/{state}")
        assert response.status_code == 200
        assert response.json()["state"] == state


# ═══════════════════════════════════════════════════════
# 📐 SECTION 3: BUSINESS LOGIC / DATA INTEGRITY TESTS
# ═══════════════════════════════════════════════════════

class TestDataIntegrity:
    """Cross-checks between datasets and expected business rules."""

    def test_covid_and_voter_data_cover_same_states(self):
        covid_states = {d["state"] for d in COVID_DATA}
        voter_states = {d["state"] for d in VOTER_DATA}
        assert covid_states == voter_states

    def test_no_duplicate_states_in_covid(self):
        states = [d["state"] for d in COVID_DATA]
        assert len(states) == len(set(states)), "Duplicate states found in COVID data"

    def test_no_duplicate_states_in_voters(self):
        states = [d["state"] for d in VOTER_DATA]
        assert len(states) == len(set(states)), "Duplicate states found in voter data"

    def test_national_total_cases_positive(self):
        total = sum(d["total_cases"] for d in COVID_DATA)
        assert total > 0

    def test_national_recovery_rate_reasonable(self):
        total_cases = sum(d["total_cases"] for d in COVID_DATA)
        total_recovered = sum(d["recovered"] for d in COVID_DATA)
        rate = total_recovered / total_cases * 100
        assert 70 <= rate <= 100, f"Unexpected national recovery rate: {rate:.2f}%"

    def test_national_fatality_rate_reasonable(self):
        total_cases = sum(d["total_cases"] for d in COVID_DATA)
        total_deaths = sum(d["deaths"] for d in COVID_DATA)
        rate = total_deaths / total_cases * 100
        assert 0 <= rate <= 5, f"Unexpected national fatality rate: {rate:.2f}%"

    def test_all_turnout_values_are_reasonable(self):
        for d in VOTER_DATA:
            assert 30 <= d["turnout_pct"] <= 100, (
                f"{d['state']} has suspicious turnout: {d['turnout_pct']}%"
            )

    def test_male_voters_greater_than_zero(self):
        for d in VOTER_DATA:
            assert d["male_voters"] > 0

    def test_female_voters_greater_than_zero(self):
        for d in VOTER_DATA:
            assert d["female_voters"] > 0

    def test_gender_ratio_plausible(self):
        """Male/Female ratio should be roughly 50-60%."""
        for d in VOTER_DATA:
            male_pct = d["male_voters"] / d["total_voters"] * 100
            assert 45 <= male_pct <= 65, (
                f"{d['state']}: male voter % out of range: {male_pct:.1f}%"
            )

    def test_summary_total_active_matches_covid_list(self):
        expected_active = sum(d["active_cases"] for d in COVID_DATA)
        summary = client.get("/api/summary").json()
        assert summary["covid"]["total_active"] == expected_active

    def test_summary_total_deaths_matches_covid_list(self):
        expected_deaths = sum(d["deaths"] for d in COVID_DATA)
        summary = client.get("/api/summary").json()
        assert summary["covid"]["total_deaths"] == expected_deaths


# ═══════════════════════════════════════════════════════
# ⚡ SECTION 4: EDGE CASE TESTS
# ═══════════════════════════════════════════════════════

class TestEdgeCases:
    """Edge cases and boundary condition tests."""

    def test_state_with_spaces_in_url(self):
        """States with spaces should work when URL-encoded."""
        response = client.get("/api/covid/Uttar Pradesh")
        assert response.status_code == 200

    def test_state_name_with_mixed_case(self):
        response = client.get("/api/covid/MAHARASHTRA")
        assert response.status_code == 200

    def test_completely_invalid_state_name(self):
        for endpoint in ["/api/covid/XYZ123", "/api/voters/XYZ123"]:
            response = client.get(endpoint)
            assert response.status_code == 404

    def test_empty_string_state(self):
        """An empty state path segment won't match the route."""
        response = client.get("/api/covid/ ")
        # Should either be 404 or return error
        assert response.status_code in [404, 422]

    def test_all_states_reachable_via_covid_api(self):
        for state in STATES:
            response = client.get(f"/api/covid/{state}")
            assert response.status_code == 200, f"Failed for state: {state}"

    def test_all_states_reachable_via_voter_api(self):
        for state in STATES:
            response = client.get(f"/api/voters/{state}")
            assert response.status_code == 200, f"Failed for state: {state}"

    def test_api_response_is_not_empty(self):
        for endpoint in ["/api/covid", "/api/voters", "/api/summary"]:
            response = client.get(endpoint)
            assert len(response.content) > 0

    def test_covid_vaccinated_less_than_total(self):
        for d in COVID_DATA:
            assert d["vaccinated"] <= d["total_cases"], (
                f"{d['state']}: vaccinated > total_cases is logically impossible"
            )

    def test_no_negative_values_in_covid_data(self):
        numeric_fields = ["total_cases", "active_cases", "recovered", "deaths", "vaccinated"]
        for d in COVID_DATA:
            for field in numeric_fields:
                assert d[field] >= 0, f"{d['state']}.{field} is negative"

    def test_no_negative_values_in_voter_data(self):
        numeric_fields = ["total_voters", "male_voters", "female_voters", "young_voters"]
        for d in VOTER_DATA:
            for field in numeric_fields:
                assert d[field] >= 0, f"{d['state']}.{field} is negative"


# ═══════════════════════════════════════════════════════
# 🏁 SECTION 5: PERFORMANCE / SMOKE TESTS
# ═══════════════════════════════════════════════════════

class TestSmoke:
    """Quick smoke tests to verify the app is alive and responding."""

    def test_all_main_endpoints_respond(self):
        endpoints = ["/", "/api/covid", "/api/voters", "/api/summary"]
        for ep in endpoints:
            r = client.get(ep)
            assert r.status_code == 200, f"Endpoint {ep} failed with {r.status_code}"

    def test_covid_list_is_not_empty(self):
        assert len(client.get("/api/covid").json()) > 0

    def test_voter_list_is_not_empty(self):
        assert len(client.get("/api/voters").json()) > 0

    def test_summary_has_non_zero_totals(self):
        summary = client.get("/api/summary").json()
        assert summary["covid"]["total_cases"] > 0
        assert summary["voters"]["total_voters"] > 0

    def test_app_title(self):
        assert app.title == "COVID-19 & Indian Voters Dashboard"

    def test_app_version(self):
        assert app.version == "1.0.0"

    # demo run