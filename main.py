"""
Lab 1: Evidence-Based Policy Rule Engine
========================================
Institutional Hospital Dietary Compliance Validation Service.

Validates patient meal plans against clinical and institutional nutrition policies
such as Low-Sodium, Diabetic, and Regular diets based on codified thresholds.
"""

from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# 1. ENUMS & DATA MODELS
# ============================================================================

class DietPolicy(str, Enum):
    """Supported institutional dietary policies."""
    LOW_SODIUM = "LOW_SODIUM"
    DIABETIC = "DIABETIC"
    REGULAR = "REGULAR"


class FoodItem(BaseModel):
    """Represents an individual food item in a patient meal plan."""
    name: str = Field(
        ...,
        min_length=1,
        description="Name or description of the food item",
        examples=["Grilled Chicken Breast with Steamed Broccoli"],
    )
    calories: float = Field(
        ...,
        ge=0.0,
        description="Caloric energy content in kilocalories (kcal)",
        examples=[350.0],
    )
    carbohydrates_g: float = Field(
        ...,
        ge=0.0,
        description="Total carbohydrates in grams (g)",
        examples=[12.5],
    )
    sodium_mg: float = Field(
        ...,
        ge=0.0,
        description="Sodium content in milligrams (mg)",
        examples=[380.0],
    )
    added_sugar_g: float = Field(
        ...,
        ge=0.0,
        description="Added sugar in grams (g)",
        examples=[0.0],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Oatmeal with Fresh Berries",
                "calories": 220.0,
                "carbohydrates_g": 38.0,
                "sodium_mg": 85.0,
                "added_sugar_g": 2.5,
            }
        }
    )


class MealPlanRequest(BaseModel):
    """Request payload containing a patient's dietary plan for compliance audit."""
    patient_id: str = Field(
        ...,
        min_length=1,
        description="Unique patient or clinical encounter identifier",
        examples=["PAT-94821"],
    )
    policy: DietPolicy = Field(
        ...,
        description="Institutional dietary policy to validate against",
        examples=[DietPolicy.LOW_SODIUM],
    )
    items: List[FoodItem] = Field(
        default_factory=list,
        description="List of food items planned for the patient",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "patient_id": "PAT-94821",
                "policy": "LOW_SODIUM",
                "items": [
                    {
                        "name": "Steel Cut Oatmeal with Blueberries",
                        "calories": 240.0,
                        "carbohydrates_g": 42.0,
                        "sodium_mg": 95.0,
                        "added_sugar_g": 2.0,
                    },
                    {
                        "name": "Grilled Salmon with Quinoa & Asparagus",
                        "calories": 520.0,
                        "carbohydrates_g": 36.0,
                        "sodium_mg": 320.0,
                        "added_sugar_g": 0.0,
                    },
                    {
                        "name": "Steamed Chicken Breast & Brown Rice",
                        "calories": 480.0,
                        "carbohydrates_g": 45.0,
                        "sodium_mg": 280.0,
                        "added_sugar_g": 0.0,
                    },
                ],
            }
        }
    )


class Violation(BaseModel):
    """Detailed record of a single institutional policy threshold violation."""
    rule_name: str = Field(
        ...,
        description="Canonical identifier for the policy rule",
        examples=["MAX_SODIUM"],
    )
    message: str = Field(
        ...,
        description="Human-readable explanation of the compliance breach",
        examples=["Total sodium (2450.0 mg) exceeds policy limit of 2000.0 mg"],
    )
    actual_value: float = Field(
        ...,
        description="Calculated total value from the submitted meal plan",
        examples=[2450.0],
    )
    threshold_value: float = Field(
        ...,
        description="Institutional ceiling threshold allowed by the policy",
        examples=[2000.0],
    )


class ValidationResponse(BaseModel):
    """Comprehensive compliance evaluation result."""
    patient_id: str = Field(
        ...,
        description="Identifier of the evaluated patient",
        examples=["PAT-94821"],
    )
    policy: DietPolicy = Field(
        ...,
        description="Policy against which evaluation was performed",
        examples=[DietPolicy.LOW_SODIUM],
    )
    is_compliant: bool = Field(
        ...,
        description="True if all policy rules are satisfied; False otherwise",
        examples=[True],
    )
    summary_metrics: Dict[str, float] = Field(
        ...,
        description="Aggregated nutritional totals for the meal plan",
        examples=[
            {
                "total_calories": 1240.0,
                "total_carbohydrates_g": 123.0,
                "total_sodium_mg": 695.0,
                "total_added_sugar_g": 2.0,
            }
        ],
    )
    violations: List[Violation] = Field(
        default_factory=list,
        description="List of violations if non-compliant; empty if compliant",
    )


class PolicyRuleDetail(BaseModel):
    """Detailed specifications and clinical purpose for a policy."""
    name: str
    description: str
    thresholds: Dict[str, float]


# ============================================================================
# 2. INSTITUTIONAL POLICY RULE SPECIFICATIONS
# ============================================================================

POLICY_SPECIFICATIONS: Dict[DietPolicy, PolicyRuleDetail] = {
    DietPolicy.LOW_SODIUM: PolicyRuleDetail(
        name="Low-Sodium Policy",
        description=(
            "Designed for hypertension, cardiac insufficiency, and renal disease management. "
            "Caps sodium intake at 2,000 mg while maintaining appropriate caloric and sugar boundaries."
        ),
        thresholds={
            "sodium_mg": 2000.0,
            "calories": 2500.0,
            "added_sugar_g": 50.0,
        },
    ),
    DietPolicy.DIABETIC: PolicyRuleDetail(
        name="Diabetic Policy",
        description=(
            "Aimed at glycemic control, insulin resistance management, and metabolic stabilization. "
            "Imposes strict carbohydrate (200g) and added sugar (25g) caps, alongside caloric and sodium limits."
        ),
        thresholds={
            "sodium_mg": 2300.0,
            "calories": 2200.0,
            "carbohydrates_g": 200.0,
            "added_sugar_g": 25.0,
        },
    ),
    DietPolicy.REGULAR: PolicyRuleDetail(
        name="Regular Policy",
        description=(
            "Standard hospital dietary baseline supporting balanced adult nutritional requirements "
            "without therapeutic carbohydrate or sodium reductions."
        ),
        thresholds={
            "sodium_mg": 2400.0,
            "calories": 2500.0,
            "carbohydrates_g": 300.0,
            "added_sugar_g": 50.0,
        },
    ),
}

# Rule mapping definitions for readable names, units, and metric keys
NUTRIENT_RULE_MAPPING: Dict[str, Dict[str, str]] = {
    "sodium_mg": {
        "rule_name": "MAX_SODIUM",
        "display_name": "sodium",
        "unit": "mg",
        "metric_key": "total_sodium_mg",
    },
    "calories": {
        "rule_name": "MAX_CALORIES",
        "display_name": "calories",
        "unit": "kcal",
        "metric_key": "total_calories",
    },
    "carbohydrates_g": {
        "rule_name": "MAX_CARBOHYDRATES",
        "display_name": "carbohydrates",
        "unit": "g",
        "metric_key": "total_carbohydrates_g",
    },
    "added_sugar_g": {
        "rule_name": "MAX_ADDED_SUGAR",
        "display_name": "added sugar",
        "unit": "g",
        "metric_key": "total_added_sugar_g",
    },
}


# ============================================================================
# 3. RULE ENGINE LOGIC
# ============================================================================

def calculate_summary_metrics(items: List[FoodItem]) -> Dict[str, float]:
    """Aggregate total nutritional metrics across all items in a meal plan."""
    total_calories = sum(item.calories for item in items)
    total_carbs = sum(item.carbohydrates_g for item in items)
    total_sodium = sum(item.sodium_mg for item in items)
    total_sugar = sum(item.added_sugar_g for item in items)

    return {
        "total_calories": round(total_calories, 2),
        "total_carbohydrates_g": round(total_carbs, 2),
        "total_sodium_mg": round(total_sodium, 2),
        "total_added_sugar_g": round(total_sugar, 2),
    }


def evaluate_meal_plan(request: MealPlanRequest) -> ValidationResponse:
    """
    Execute evidence-based policy rule validation.
    
    1. Aggregates nutritional metrics from all meal items.
    2. Compares aggregate values against institutional policy thresholds.
    3. Emits discrete Violation objects for any exceeded ceilings.
    4. Returns a comprehensive ValidationResponse.
    """
    if request.policy not in POLICY_SPECIFICATIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported policy: '{request.policy}'.",
        )

    policy_spec = POLICY_SPECIFICATIONS[request.policy]
    summary = calculate_summary_metrics(request.items)
    violations: List[Violation] = []

    # Evaluate each configured threshold for the active policy
    for nutrient_key, threshold in policy_spec.thresholds.items():
        meta = NUTRIENT_RULE_MAPPING[nutrient_key]
        metric_key = meta["metric_key"]
        actual_val = summary[metric_key]

        # Policy threshold is breached if actual exceeds allowed maximum
        if actual_val > threshold:
            violations.append(
                Violation(
                    rule_name=meta["rule_name"],
                    message=(
                        f"Total {meta['display_name']} ({actual_val} {meta['unit']}) "
                        f"exceeds policy limit of {threshold} {meta['unit']}"
                    ),
                    actual_value=actual_val,
                    threshold_value=threshold,
                )
            )

    return ValidationResponse(
        patient_id=request.patient_id,
        policy=request.policy,
        is_compliant=len(violations) == 0,
        summary_metrics=summary,
        violations=violations,
    )


# ============================================================================
# 4. FASTAPI APPLICATION SETUP
# ============================================================================

app = FastAPI(
    title="Evidence-Based Policy Rule Engine",
    description=(
        "Public Policy & Program Outcomes Dietary Compliance Validation Engine. "
        "Audits customized patient meal plans against clinical and institutional guidelines."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================================
# 5. REST API ENDPOINTS
# ============================================================================

@app.get(
    "/",
    tags=["System"],
    summary="Health check & service status",
    response_description="Returns operational health status and metadata",
)
def health_check() -> Dict[str, str]:
    """Health check endpoint confirming service availability."""
    return {
        "status": "healthy",
        "service": "Evidence-Based Policy Rule Engine",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "docs_url": "/docs",
    }


@app.get(
    "/policies",
    tags=["Policies"],
    summary="Get institutional policy rule limits",
    response_description="Returns configuration and thresholds for all supported dietary policies",
    response_model=Dict[DietPolicy, PolicyRuleDetail],
)
def get_policies() -> Dict[DietPolicy, PolicyRuleDetail]:
    """Returns currently codified institutional policies and their respective nutrient thresholds."""
    return POLICY_SPECIFICATIONS


@app.post(
    "/validate",
    tags=["Validation"],
    summary="Validate meal plan against institutional dietary policy",
    response_description="Detailed compliance verdict, summary metrics, and any rule violations",
    response_model=ValidationResponse,
    status_code=status.HTTP_200_OK,
)
def validate_meal_plan(request: MealPlanRequest) -> ValidationResponse:
    """
    Accepts a patient meal plan, aggregates nutritional metrics,
    evaluates totals against the specified institutional policy thresholds,
    and returns a structured compliance response.
    """
    return evaluate_meal_plan(request)


# ============================================================================
# 6. LOCAL ENTRYPOINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
