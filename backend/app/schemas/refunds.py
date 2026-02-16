from typing import TypedDict

class RefundTaxonomy(TypedDict):
    title: str
    description: str

class RefundEligibility(TypedDict):
    eligible: bool
    reason: str
    max_refund_amount: int
    policy_violation: str | None

class RefundCalculation(TypedDict):
    item_price: int
    tax_amount: int
    discount_amount: int
    total_refund: int
    breakdown: str