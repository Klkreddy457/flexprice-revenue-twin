import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.pricing_service import (
    calculate_monthly_bill,
    calculate_infra_cost,
    calculate_gross_margin
)

def test_monthly_bill():
    # Test case 1: Usage is within included units
    bill1 = calculate_monthly_bill(tasks=80, base_price=49.00, included_units=100, overage_price=0.75)
    assert bill1 == 49.00, f"Expected 49.00, got {bill1}"

    # Test case 2: Usage exceeds included units
    bill2 = calculate_monthly_bill(tasks=120, base_price=49.00, included_units=100, overage_price=0.75)
    assert bill2 == 64.00, f"Expected 64.00, got {bill2}"  # 49 + 20 * 0.75 = 64

    # Test case 3: Zero usage
    bill3 = calculate_monthly_bill(tasks=0, base_price=49.00, included_units=100, overage_price=0.75)
    assert bill3 == 49.00, f"Expected 49.00, got {bill3}"

    print("test_monthly_bill passed!")

def test_infra_cost():
    # Test with standard config
    cost = calculate_infra_cost(
        tokens_used=100000,          # 100,000 * 0.00001 = $1.00
        agent_calls=50,              # 50 * 0.005 = $0.25
        premium_model_calls=10,      # 10 * 0.05 = $0.50
        compute_seconds=1000,        # 1000 * 0.0005 = $0.50
        documents_processed=10       # 10 * 0.002 = $0.02
    )
    assert cost == 2.27, f"Expected 2.27, got {cost}"
    print("test_infra_cost passed!")

def test_gross_margin():
    margin1 = calculate_gross_margin(bill=100.0, cost=40.0)
    assert margin1 == 60.0, f"Expected 60.0, got {margin1}"

    margin2 = calculate_gross_margin(bill=0.0, cost=10.0)
    assert margin2 == 0.0, f"Expected 0.0, got {margin2}"

    print("test_gross_margin passed!")

if __name__ == "__main__":
    test_monthly_bill()
    test_infra_cost()
    test_gross_margin()
    print("All pricing service tests passed successfully!")
