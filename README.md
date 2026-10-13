# Lab 1: Evidence-Based Policy Rule Engine
**Public Policy & Program Outcomes: Institutional Dietary Compliance Validation**

---

## 1. Project Overview

In clinical and healthcare institutions, dietary compliance is a critical public health and patient safety safeguard. Patients recovering from cardiac events, managed for hypertension, or undergoing glycemic control must strictly adhere to evidence-based dietary guidelines codified by institutional policy.

This project delivers a **production-ready, high-performance rule engine** built with **FastAPI** and **Pydantic v2**. It enables hospitals and dietary departments to:
- Ingest patient meal plans composed of discrete food items with micro- and macro-nutrient metrics.
- Automatically aggregate total caloric and nutritional values.
- Audit aggregate values against institutional dietary policies (**Low-Sodium**, **Diabetic**, and **Regular**).
- Emit structured, actionable compliance responses highlighting exact rule breaches, threshold limits, and observed values.

---

## 2. Tech Stack

- **Python**: 3.10+ (tested on Python 3.14)
- **FastAPI**: Modern, high-performance web framework for building APIs.
- **Pydantic v2**: High-speed data validation and serialization.
- **Uvicorn**: Lightning-fast ASGI server.
- **Pytest & HTTPX**: Comprehensive test automation suite and test client.

---

## 3. Institutional Policy Threshold Matrix

The rule engine codifies institutional nutrition guidelines across four primary dimensions:

| Policy | Sodium Max (mg) | Calories Max (kcal) | Carbohydrates Max (g) | Added Sugar Max (g) | Primary Clinical Objective |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`LOW_SODIUM`** | `2000.0` | `2500.0` | *No cap* | `50.0` | Hypertension, cardiac insufficiency, renal protection |
| **`DIABETIC`** | `2300.0` | `2200.0` | `200.0` | `25.0` | Glycemic control, insulin resistance, metabolic stability |
| **`REGULAR`** | `2400.0` | `2500.0` | `300.0` | `50.0` | General inpatient population maintenance |

---

## 4. Project File Structure

```text
.
├── requirements.txt   # Pinned dependencies (FastAPI, Uvicorn, Pydantic, Pytest, HTTPX)
├── main.py            # Complete FastAPI application, Pydantic v2 models, policy rules, and endpoints
├── test_main.py       # 16 unit and integration tests verifying compliant & non-compliant flows
└── README.md          # Comprehensive documentation, setup guide, and API reference
```

---

## 5. Installation & Setup

### Prerequisites
- Python 3.10 or higher installed.

### Step 1: Clone or navigate to the workspace directory
```bash
cd <workspace-path>
```

### Step 2: (Optional but recommended) Create a virtual environment
```bash
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate
```

### Step 3: Install dependencies
```bash
python -m pip install -r requirements.txt
```

---

## 6. Running the API Server

Start the Uvicorn development server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Or run directly via Python:

```bash
python main.py
```

The server will be available at:
- **Base URL**: `http://localhost:8000`
- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

---

## 7. API Reference & Examples

### Endpoint 1: Health Check
- **Method**: `GET /`
- **Description**: Verifies service operational readiness and returns metadata.

#### Example Request:
```bash
curl -X GET "http://localhost:8000/"
```

#### Example Response:
```json
{
  "status": "healthy",
  "service": "Evidence-Based Policy Rule Engine",
  "version": "1.0.0",
  "timestamp": "2026-10-13T08:55:00.000000+00:00",
  "docs_url": "/docs"
}
```

---

### Endpoint 2: Get Policy Limits
- **Method**: `GET /policies`
- **Description**: Returns the codified nutrient limits and clinical guidelines for all supported policies.

#### Example Request:
```bash
curl -X GET "http://localhost:8000/policies"
```

#### Example Response:
```json
{
  "LOW_SODIUM": {
    "name": "Low-Sodium Policy",
    "description": "Designed for hypertension, cardiac insufficiency, and renal disease management. Caps sodium intake at 2,000 mg while maintaining appropriate caloric and sugar boundaries.",
    "thresholds": {
      "sodium_mg": 2000.0,
      "calories": 2500.0,
      "added_sugar_g": 50.0
    }
  },
  "DIABETIC": {
    "name": "Diabetic Policy",
    "description": "Aimed at glycemic control, insulin resistance management, and metabolic stabilization. Imposes strict carbohydrate (200g) and added sugar (25g) caps, alongside caloric and sodium limits.",
    "thresholds": {
      "sodium_mg": 2300.0,
      "calories": 2200.0,
      "carbohydrates_g": 200.0,
      "added_sugar_g": 25.0
    }
  },
  "REGULAR": {
    "name": "Regular Policy",
    "description": "Standard hospital dietary baseline supporting balanced adult nutritional requirements without therapeutic carbohydrate or sodium reductions.",
    "thresholds": {
      "sodium_mg": 2400.0,
      "calories": 2500.0,
      "carbohydrates_g": 300.0,
      "added_sugar_g": 50.0
    }
  }
}
```

---

### Endpoint 3: Validate Meal Plan
- **Method**: `POST /validate`
- **Description**: Validates a patient meal plan against the selected dietary policy.

#### Case A: Fully Compliant Meal Plan (`is_compliant == True`)

```bash
curl -X POST "http://localhost:8000/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "PAT-94821",
    "policy": "LOW_SODIUM",
    "items": [
      {
        "name": "Oatmeal with Blueberries",
        "calories": 240.0,
        "carbohydrates_g": 42.0,
        "sodium_mg": 95.0,
        "added_sugar_g": 2.0
      },
      {
        "name": "Grilled Salmon with Quinoa",
        "calories": 520.0,
        "carbohydrates_g": 36.0,
        "sodium_mg": 320.0,
        "added_sugar_g": 0.0
      },
      {
        "name": "Steamed Chicken Breast & Brown Rice",
        "calories": 480.0,
        "carbohydrates_g": 45.0,
        "sodium_mg": 280.0,
        "added_sugar_g": 0.0
      }
    ]
  }'
```

**Response (`200 OK`):**
```json
{
  "patient_id": "PAT-94821",
  "policy": "LOW_SODIUM",
  "is_compliant": true,
  "summary_metrics": {
    "total_calories": 1240.0,
    "total_carbohydrates_g": 123.0,
    "total_sodium_mg": 695.0,
    "total_added_sugar_g": 2.0
  },
  "violations": []
}
```

---

#### Case B: Non-Compliant Meal Plan Exceeding Sodium Limit (`is_compliant == False`)

```bash
curl -X POST "http://localhost:8000/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "PAT-94822",
    "policy": "LOW_SODIUM",
    "items": [
      {
        "name": "Canned Vegetable Soup",
        "calories": 320.0,
        "carbohydrates_g": 35.0,
        "sodium_mg": 1450.0,
        "added_sugar_g": 3.0
      },
      {
        "name": "Smoked Ham & Pickle Sandwich",
        "calories": 580.0,
        "carbohydrates_g": 48.0,
        "sodium_mg": 1350.0,
        "added_sugar_g": 2.0
      }
    ]
  }'
```

**Response (`200 OK`):**
```json
{
  "patient_id": "PAT-94822",
  "policy": "LOW_SODIUM",
  "is_compliant": false,
  "summary_metrics": {
    "total_calories": 900.0,
    "total_carbohydrates_g": 83.0,
    "total_sodium_mg": 2800.0,
    "total_added_sugar_g": 5.0
  },
  "violations": [
    {
      "rule_name": "MAX_SODIUM",
      "message": "Total sodium (2800.0 mg) exceeds policy limit of 2000.0 mg",
      "actual_value": 2800.0,
      "threshold_value": 2000.0
    }
  ]
}
```

---

#### Case C: Diabetic Non-Compliant Meal Plan (Multiple Violations)

```bash
curl -X POST "http://localhost:8000/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "PAT-94823",
    "policy": "DIABETIC",
    "items": [
      {
        "name": "Jumbo Caramel Mocha & Frosted Pastry",
        "calories": 1150.0,
        "carbohydrates_g": 140.0,
        "sodium_mg": 850.0,
        "added_sugar_g": 52.0
      },
      {
        "name": "Double Bacon Cheeseburger & Large Fries",
        "calories": 1450.0,
        "carbohydrates_g": 115.0,
        "sodium_mg": 1900.0,
        "added_sugar_g": 12.0
      }
    ]
  }'
```

**Response (`200 OK`):**
```json
{
  "patient_id": "PAT-94823",
  "policy": "DIABETIC",
  "is_compliant": false,
  "summary_metrics": {
    "total_calories": 2600.0,
    "total_carbohydrates_g": 255.0,
    "total_sodium_mg": 2750.0,
    "total_added_sugar_g": 64.0
  },
  "violations": [
    {
      "rule_name": "MAX_SODIUM",
      "message": "Total sodium (2750.0 mg) exceeds policy limit of 2300.0 mg",
      "actual_value": 2750.0,
      "threshold_value": 2300.0
    },
    {
      "rule_name": "MAX_CALORIES",
      "message": "Total calories (2600.0 kcal) exceeds policy limit of 2200.0 kcal",
      "actual_value": 2600.0,
      "threshold_value": 2200.0
    },
    {
      "rule_name": "MAX_CARBOHYDRATES",
      "message": "Total carbohydrates (255.0 g) exceeds policy limit of 200.0 g",
      "actual_value": 255.0,
      "threshold_value": 200.0
    },
    {
      "rule_name": "MAX_ADDED_SUGAR",
      "message": "Total added sugar (64.0 g) exceeds policy limit of 25.0 g",
      "actual_value": 64.0,
      "threshold_value": 25.0
    }
  ]
}
```

---

## 8. Running the Automated Test Suite

Execute the test suite using `pytest`:

```bash
python -m pytest test_main.py -v
```

### Test Suite Coverage:
1. `test_health_check_endpoint`: Verifies `GET /` 200 OK status.
2. `test_get_policies_endpoint`: Verifies `GET /policies` returns exact thresholds for `LOW_SODIUM`, `DIABETIC`, and `REGULAR`.
3. `test_low_sodium_fully_compliant`: Confirms compliant low-sodium meal plan yields `is_compliant == True` and zero violations.
4. `test_low_sodium_non_compliant_exceeds_sodium`: Confirms sodium breach yields `is_compliant == False` and `MAX_SODIUM` violation.
5. `test_diabetic_fully_compliant`: Verifies compliant diabetic meal plan under 200g carbs and 25g added sugar.
6. `test_diabetic_multiple_violations_reported`: Verifies simultaneous reporting of `MAX_CALORIES`, `MAX_CARBOHYDRATES`, `MAX_SODIUM`, and `MAX_ADDED_SUGAR`.
7. `test_regular_fully_compliant`: Verifies compliant standard hospital meal plan.
8. `test_regular_policy_violations`: Verifies breaches against regular limits.
9. `test_empty_meal_plan_is_compliant`: Edge case where items is empty (`[]`).
10. `test_exact_threshold_boundary_is_compliant`: Boundary case where totals exactly equal policy maximum.
11. `test_threshold_boundary_plus_one_fails`: Boundary case where totals exceed limit by 0.1.
12. `test_invalid_policy_enum_returns_422`: Schema validation ensuring invalid policy strings return 422.
13. `test_negative_nutritional_values_return_422`: Schema validation rejecting negative nutrient values with 422.
14. `test_missing_required_fields_return_422`: Schema validation ensuring mandatory fields are enforced.
15. `test_pure_function_evaluate_meal_plan`: Direct unit test of `evaluate_meal_plan` rule engine logic.
16. `test_calculate_summary_metrics_precision`: Precision unit test verifying 2-decimal-place floating point rounding.
