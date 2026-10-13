"""
Unit and Integration Tests for Evidence-Based Policy Rule Engine
================================================================
Tests dietary policy compliance validation using Pytest and FastAPI's TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from main import (
    app,
    DietPolicy,
    FoodItem,
    MealPlanRequest,
    calculate_summary_metrics,
    evaluate_meal_plan,
)

client = TestClient(app)


# ============================================================================
# 1. SYSTEM & POLICIES ENDPOINT TESTS
# ============================================================================

def test_health_check_endpoint():
    """Verify that the GET / endpoint returns 200 OK and healthy status."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Evidence-Based Policy Rule Engine" in data["service"]
    assert "version" in data
    assert "timestamp" in data


def test_get_policies_endpoint():
    """Verify that GET /policies returns rule thresholds for all policies."""
    response = client.get("/policies")
    assert response.status_code == 200
    policies = response.json()

    # All three policies must be present
    assert "LOW_SODIUM" in policies
    assert "DIABETIC" in policies
    assert "REGULAR" in policies

    # Verify Low-Sodium thresholds
    low_sodium = policies["LOW_SODIUM"]["thresholds"]
    assert low_sodium["sodium_mg"] == 2000.0
    assert low_sodium["calories"] == 2500.0
    assert low_sodium["added_sugar_g"] == 50.0

    # Verify Diabetic thresholds
    diabetic = policies["DIABETIC"]["thresholds"]
    assert diabetic["sodium_mg"] == 2300.0
    assert diabetic["calories"] == 2200.0
    assert diabetic["carbohydrates_g"] == 200.0
    assert diabetic["added_sugar_g"] == 25.0

    # Verify Regular thresholds
    regular = policies["REGULAR"]["thresholds"]
    assert regular["sodium_mg"] == 2400.0
    assert regular["calories"] == 2500.0
    assert regular["carbohydrates_g"] == 300.0
    assert regular["added_sugar_g"] == 50.0


# ============================================================================
# 2. LOW-SODIUM POLICY VALIDATION TESTS
# ============================================================================

def test_low_sodium_fully_compliant():
    """A meal plan within all Low-Sodium limits must return is_compliant == True."""
    payload = {
        "patient_id": "PAT-LS-001",
        "policy": "LOW_SODIUM",
        "items": [
            {
                "name": "Oatmeal with Blueberries",
                "calories": 250.0,
                "carbohydrates_g": 45.0,
                "sodium_mg": 120.0,
                "added_sugar_g": 5.0,
            },
            {
                "name": "Steamed Chicken Breast & Quinoa",
                "calories": 600.0,
                "carbohydrates_g": 50.0,
                "sodium_mg": 380.0,
                "added_sugar_g": 0.0,
            },
            {
                "name": "Baked Salmon with Steamed Asparagus",
                "calories": 550.0,
                "carbohydrates_g": 10.0,
                "sodium_mg": 400.0,
                "added_sugar_g": 0.0,
            },
        ],
    }

    response = client.post("/validate", json=payload)
    assert response.status_code == 200
    result = response.json()

    assert result["patient_id"] == "PAT-LS-001"
    assert result["policy"] == "LOW_SODIUM"
    assert result["is_compliant"] is True
    assert len(result["violations"]) == 0
    assert result["summary_metrics"]["total_calories"] == 1400.0
    assert result["summary_metrics"]["total_sodium_mg"] == 900.0
    assert result["summary_metrics"]["total_added_sugar_g"] == 5.0


def test_low_sodium_non_compliant_exceeds_sodium():
    """A meal plan exceeding 2000mg sodium must report an invalid compliance status and violation."""
    payload = {
        "patient_id": "PAT-LS-002",
        "policy": "LOW_SODIUM",
        "items": [
            {
                "name": "Canned Soup (High Sodium)",
                "calories": 300.0,
                "carbohydrates_g": 35.0,
                "sodium_mg": 1600.0,
                "added_sugar_g": 4.0,
            },
            {
                "name": "Deli Turkey Sandwich with Pickles",
                "calories": 450.0,
                "carbohydrates_g": 40.0,
                "sodium_mg": 1100.0,
                "added_sugar_g": 3.0,
            },
        ],
    }

    response = client.post("/validate", json=payload)
    assert response.status_code == 200
    result = response.json()

    assert result["patient_id"] == "PAT-LS-002"
    assert result["policy"] == "LOW_SODIUM"
    assert result["is_compliant"] is False
    assert result["summary_metrics"]["total_sodium_mg"] == 2700.0
    assert len(result["violations"]) == 1

    violation = result["violations"][0]
    assert violation["rule_name"] == "MAX_SODIUM"
    assert violation["actual_value"] == 2700.0
    assert violation["threshold_value"] == 2000.0
    assert "Total sodium" in violation["message"]


# ============================================================================
# 3. DIABETIC POLICY VALIDATION TESTS
# ============================================================================

def test_diabetic_fully_compliant():
    """A meal plan respecting carbohydrate (<=200g) and sugar (<=25g) caps passes Diabetic policy."""
    payload = {
        "patient_id": "PAT-DB-001",
        "policy": "DIABETIC",
        "items": [
            {
                "name": "Scrambled Eggs with Spinach",
                "calories": 320.0,
                "carbohydrates_g": 4.0,
                "sodium_mg": 280.0,
                "added_sugar_g": 0.0,
            },
            {
                "name": "Grilled Turkey Salad",
                "calories": 480.0,
                "carbohydrates_g": 18.0,
                "sodium_mg": 450.0,
                "added_sugar_g": 2.0,
            },
            {
                "name": "Baked Cod with Brown Rice & Broccoli",
                "calories": 550.0,
                "carbohydrates_g": 45.0,
                "sodium_mg": 380.0,
                "added_sugar_g": 0.0,
            },
        ],
    }

    response = client.post("/validate", json=payload)
    assert response.status_code == 200
    result = response.json()

    assert result["patient_id"] == "PAT-DB-001"
    assert result["policy"] == "DIABETIC"
    assert result["is_compliant"] is True
    assert len(result["violations"]) == 0
    assert result["summary_metrics"]["total_carbohydrates_g"] == 67.0
    assert result["summary_metrics"]["total_added_sugar_g"] == 2.0


def test_diabetic_multiple_violations_reported():
    """A high sugar and carbohydrate meal plan reports all distinct violations."""
    payload = {
        "patient_id": "PAT-DB-002",
        "policy": "DIABETIC",
        "items": [
            {
                "name": "Glazed Pastry & Large Soda",
                "calories": 1100.0,
                "carbohydrates_g": 130.0,
                "sodium_mg": 900.0,
                "added_sugar_g": 55.0,
            },
            {
                "name": "Cheeseburger & Fries Combo",
                "calories": 1400.0,
                "carbohydrates_g": 120.0,
                "sodium_mg": 1800.0,
                "added_sugar_g": 15.0,
            },
        ],
    }

    response = client.post("/validate", json=payload)
    assert response.status_code == 200
    result = response.json()

    assert result["patient_id"] == "PAT-DB-002"
    assert result["policy"] == "DIABETIC"
    assert result["is_compliant"] is False

    metrics = result["summary_metrics"]
    assert metrics["total_calories"] == 2500.0        # Limit: 2200.0
    assert metrics["total_carbohydrates_g"] == 250.0 # Limit: 200.0
    assert metrics["total_sodium_mg"] == 2700.0       # Limit: 2300.0
    assert metrics["total_added_sugar_g"] == 70.0    # Limit: 25.0

    # Ensure all 4 rules were violated and captured
    violated_rules = {v["rule_name"]: v for v in result["violations"]}
    assert "MAX_CALORIES" in violated_rules
    assert "MAX_CARBOHYDRATES" in violated_rules
    assert "MAX_SODIUM" in violated_rules
    assert "MAX_ADDED_SUGAR" in violated_rules

    assert violated_rules["MAX_CALORIES"]["actual_value"] == 2500.0
    assert violated_rules["MAX_CALORIES"]["threshold_value"] == 2200.0

    assert violated_rules["MAX_CARBOHYDRATES"]["actual_value"] == 250.0
    assert violated_rules["MAX_CARBOHYDRATES"]["threshold_value"] == 200.0

    assert violated_rules["MAX_SODIUM"]["actual_value"] == 2700.0
    assert violated_rules["MAX_SODIUM"]["threshold_value"] == 2300.0

    assert violated_rules["MAX_ADDED_SUGAR"]["actual_value"] == 70.0
    assert violated_rules["MAX_ADDED_SUGAR"]["threshold_value"] == 25.0


# ============================================================================
# 4. REGULAR POLICY VALIDATION TESTS
# ============================================================================

def test_regular_fully_compliant():
    """A standard meal plan within standard guidelines passes Regular policy."""
    payload = {
        "patient_id": "PAT-REG-001",
        "policy": "REGULAR",
        "items": [
            {
                "name": "Roast Chicken with Mashed Potatoes & Green Beans",
                "calories": 750.0,
                "carbohydrates_g": 65.0,
                "sodium_mg": 700.0,
                "added_sugar_g": 8.0,
            },
            {
                "name": "Beef Stew with Dinner Roll",
                "calories": 800.0,
                "carbohydrates_g": 85.0,
                "sodium_mg": 850.0,
                "added_sugar_g": 5.0,
            },
        ],
    }

    response = client.post("/validate", json=payload)
    assert response.status_code == 200
    result = response.json()

    assert result["is_compliant"] is True
    assert len(result["violations"]) == 0
    assert result["summary_metrics"]["total_calories"] == 1550.0
    assert result["summary_metrics"]["total_carbohydrates_g"] == 150.0
    assert result["summary_metrics"]["total_sodium_mg"] == 1550.0
    assert result["summary_metrics"]["total_added_sugar_g"] == 13.0


def test_regular_policy_violations():
    """Exceeding 300g carbs and 2400mg sodium in Regular policy generates violations."""
    payload = {
        "patient_id": "PAT-REG-002",
        "policy": "REGULAR",
        "items": [
            {
                "name": "Extra Large Pasta Feast",
                "calories": 1800.0,
                "carbohydrates_g": 260.0,
                "sodium_mg": 1600.0,
                "added_sugar_g": 20.0,
            },
            {
                "name": "Garlic Bread & Sweet Dessert",
                "calories": 900.0,
                "carbohydrates_g": 90.0,
                "sodium_mg": 1000.0,
                "added_sugar_g": 35.0,
            },
        ],
    }

    response = client.post("/validate", json=payload)
    assert response.status_code == 200
    result = response.json()

    assert result["is_compliant"] is False
    violated_rule_names = [v["rule_name"] for v in result["violations"]]
    assert "MAX_CALORIES" in violated_rule_names       # 2700 > 2500
    assert "MAX_CARBOHYDRATES" in violated_rule_names  # 350 > 300
    assert "MAX_SODIUM" in violated_rule_names         # 2600 > 2400
    assert "MAX_ADDED_SUGAR" in violated_rule_names    # 55 > 50


# ============================================================================
# 5. EDGE & BOUNDARY TESTS
# ============================================================================

def test_empty_meal_plan_is_compliant():
    """An empty meal items list has zero nutrients and is strictly compliant."""
    payload = {
        "patient_id": "PAT-EMPTY-001",
        "policy": "LOW_SODIUM",
        "items": [],
    }

    response = client.post("/validate", json=payload)
    assert response.status_code == 200
    result = response.json()

    assert result["is_compliant"] is True
    assert result["violations"] == []
    assert result["summary_metrics"]["total_calories"] == 0.0
    assert result["summary_metrics"]["total_sodium_mg"] == 0.0


def test_exact_threshold_boundary_is_compliant():
    """A meal plan exactly equal to the threshold boundary must pass (not strictly greater than)."""
    payload = {
        "patient_id": "PAT-BOUNDARY",
        "policy": "LOW_SODIUM",
        "items": [
            {
                "name": "Exact Threshold Meal",
                "calories": 2500.0,       # Exact limit
                "carbohydrates_g": 100.0,
                "sodium_mg": 2000.0,       # Exact limit
                "added_sugar_g": 50.0,    # Exact limit
            }
        ],
    }

    response = client.post("/validate", json=payload)
    assert response.status_code == 200
    result = response.json()

    assert result["is_compliant"] is True
    assert len(result["violations"]) == 0


def test_threshold_boundary_plus_one_fails():
    """A meal plan just 0.1 over the threshold boundary must be marked non-compliant."""
    payload = {
        "patient_id": "PAT-BOUNDARY-OVER",
        "policy": "LOW_SODIUM",
        "items": [
            {
                "name": "Slightly Over Meal",
                "calories": 2500.1,
                "carbohydrates_g": 100.0,
                "sodium_mg": 2000.0,
                "added_sugar_g": 50.0,
            }
        ],
    }

    response = client.post("/validate", json=payload)
    assert response.status_code == 200
    result = response.json()

    assert result["is_compliant"] is False
    assert len(result["violations"]) == 1
    assert result["violations"][0]["rule_name"] == "MAX_CALORIES"


# ============================================================================
# 6. INPUT VALIDATION & BAD REQUEST TESTS
# ============================================================================

def test_invalid_policy_enum_returns_422():
    """Supplying an unknown dietary policy enum must yield 422 Unprocessable Entity."""
    payload = {
        "patient_id": "PAT-INVALID",
        "policy": "KETO_PALEO_SPECIAL",
        "items": [],
    }

    response = client.post("/validate", json=payload)
    assert response.status_code == 422


def test_negative_nutritional_values_return_422():
    """Negative values for calories or sodium must fail Pydantic validation with 422."""
    payload = {
        "patient_id": "PAT-NEG",
        "policy": "LOW_SODIUM",
        "items": [
            {
                "name": "Faulty Item",
                "calories": -100.0,
                "carbohydrates_g": 10.0,
                "sodium_mg": -50.0,
                "added_sugar_g": 0.0,
            }
        ],
    }

    response = client.post("/validate", json=payload)
    assert response.status_code == 422


def test_missing_required_fields_return_422():
    """Missing patient_id or policy must return 422."""
    response = client.post("/validate", json={"items": []})
    assert response.status_code == 422


# ============================================================================
# 7. PURE PYTHON UNIT ENGINE TESTS
# ============================================================================

def test_pure_function_evaluate_meal_plan():
    """Directly test evaluate_meal_plan logic independent of HTTP routing."""
    req = MealPlanRequest(
        patient_id="PAT-DIRECT",
        policy=DietPolicy.DIABETIC,
        items=[
            FoodItem(
                name="Apple Slices",
                calories=95.0,
                carbohydrates_g=25.0,
                sodium_mg=2.0,
                added_sugar_g=0.0,
            )
        ],
    )
    result = evaluate_meal_plan(req)
    assert result.is_compliant is True
    assert result.summary_metrics["total_carbohydrates_g"] == 25.0
    assert result.violations == []


def test_calculate_summary_metrics_precision():
    """Test floating point aggregation rounding behavior."""
    items = [
        FoodItem(
            name="Item 1",
            calories=10.123,
            carbohydrates_g=5.111,
            sodium_mg=20.222,
            added_sugar_g=1.333,
        ),
        FoodItem(
            name="Item 2",
            calories=20.456,
            carbohydrates_g=10.222,
            sodium_mg=40.444,
            added_sugar_g=2.666,
        ),
    ]
    summary = calculate_summary_metrics(items)
    assert summary["total_calories"] == 30.58
    assert summary["total_carbohydrates_g"] == 15.33
    assert summary["total_sodium_mg"] == 60.67
    assert summary["total_added_sugar_g"] == 4.0
