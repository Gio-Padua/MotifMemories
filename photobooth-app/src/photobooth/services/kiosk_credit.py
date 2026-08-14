from datetime import datetime


def apply_bill(bills: list[int], denomination: int, price: int, accepted: list[int]) -> tuple[list[int], int, int, bool]:
    if denomination not in accepted:
        raise ValueError("unsupported denomination")
    updated = [*bills, denomination]
    credit = sum(updated)
    return updated, credit, max(credit - price, 0), credit >= price


def partial_credit_expired(deadline: datetime | None, now: datetime) -> bool:
    return deadline is not None and deadline <= now
