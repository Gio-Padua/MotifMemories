from pydantic import BaseModel, ConfigDict, Field


class GroupKiosk(BaseModel):
    model_config = ConfigDict(title="Paid kiosk")

    payment_enabled: bool = Field(default=False, description="Enable paid sessions only after the bill acceptor is qualified.")
    price_php: int = Field(default=200, ge=1)
    accepted_denominations_php: list[int] = Field(default=[50, 100, 200])
    partial_credit_timeout_seconds: int = Field(default=90, ge=10)
    protected_action_names: list[str] = Field(
        default=[
            "kiosk-fourcut-stack",
            "kiosk-fourcut-grid",
            "kiosk-fourcut-hero",
            "kiosk-fourcut-scrapbook",
            "kiosk-sixcut-grid",
            "kiosk-eightcut-grid",
        ]
    )
    free_retakes: int = Field(default=1, ge=0)
    included_prints: int = Field(default=1, ge=0)
    minimum_free_disk_gib: float = Field(default=2.0, ge=0)
    retention_days: int = Field(default=7, ge=1)
    booth_id: str = Field(default="booth-001", pattern=r"^[a-zA-Z0-9_-]+$")

