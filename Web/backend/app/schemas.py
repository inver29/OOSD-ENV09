from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("start_at", "end_at", "effective_from", check_fields=False)
    @classmethod
    def sql_second_precision(cls, value):
        # The schema stores DATETIMEOFFSET(0); compare and retry at that precision.
        return value.replace(microsecond=0)


class LoginInput(Input):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class PasswordInput(Input):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=128)


class UserInput(Input):
    username: str = Field(pattern=r"^[a-zA-Z0-9_.-]{3,100}$")
    name: str = Field(min_length=2, max_length=150)
    email: str = Field(min_length=5, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    unit_id: int = Field(gt=0)
    roles: list[Literal["THANH_VIEN", "QUAN_LY", "QUAN_TRI"]] = Field(min_length=1, max_length=1)
    active: bool = True
    password: str | None = Field(default=None, min_length=8, max_length=128)


class CatalogInput(Input):
    name: str = Field(min_length=2, max_length=150)
    address: str | None = Field(default=None, max_length=300)
    active: bool = True
    unit_id: int | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, max_length=500)


class PolicyInput(Input):
    name: str = Field(min_length=2, max_length=150)
    max_days: int = Field(gt=0, le=365)
    buffer_hours: int = Field(ge=0, le=168)
    pickup_hours: int = Field(gt=0, le=168)
    effective_from: AwareDatetime


class AssetInput(Input):
    name: str = Field(min_length=2, max_length=200)
    category_id: int = Field(gt=0)
    location_id: int = Field(gt=0)
    custodian_id: int | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, max_length=1000)
    condition: str = Field(min_length=2, max_length=500)
    image_path: str | None = Field(default=None, max_length=500)
    version: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{16}$")


class NeedInput(Input):
    category_id: int = Field(gt=0)
    purpose: str = Field(min_length=10, max_length=1000)
    start_at: AwareDatetime
    end_at: AwareDatetime
    alternative: Literal["MUA_MOI", "HOAN_NHU_CAU"]
    evidence_path: str | None = Field(default=None, max_length=500)
    auto_submit: bool = False


class LoanInput(Input):
    asset_id: int = Field(gt=0)
    start_at: AwareDatetime
    end_at: AwareDatetime
    purpose: str = Field(min_length=5, max_length=1000)
    need_id: int | None = Field(default=None, gt=0)
    request_id: UUID
    new_need: NeedInput | None = None


class DecisionInput(Input):
    approve: bool
    reason: str = Field(default="", max_length=500)


class AssetReviewInput(DecisionInput):
    version: str = Field(pattern=r"^[0-9a-fA-F]{16}$")


class AssetWithdrawInput(Input):
    version: str = Field(pattern=r"^[0-9a-fA-F]{16}$")


class ReasonInput(Input):
    reason: str = Field(min_length=5, max_length=500)


class ReportInput(Input):
    kind: Literal["GIAO", "TRA"]
    content: str = Field(min_length=5, max_length=1000)
    condition: Literal["Đạt", "Hư hỏng"]
    evidence_path: str | None = Field(default=None, max_length=500)
    version: int | None = Field(default=None, gt=0)
    confirm_self: bool = False
    receiver_id: int | None = Field(default=None, gt=0)


class ReturnInput(Input):
    content: str = Field(min_length=5, max_length=1000)
    condition: Literal["Đạt", "Hư hỏng"]
    evidence_path: str | None = Field(default=None, max_length=500)
    version: int | None = Field(default=None, gt=0)
    receiver_id: int | None = Field(default=None, gt=0)


class VersionInput(Input):
    version: int = Field(gt=0)


class EventInput(Input):
    kind: Literal["SU_CO", "XU_LY", "DANH_GIA"]
    content: str = Field(min_length=5, max_length=1000)
    basis: str | None = Field(default=None, max_length=1000)
    decision: Literal["TIEP_TUC", "BAO_TRI"] | None = None
    cancel_pending: bool = False
    condition: str | None = Field(default=None, min_length=2, max_length=500)


class OutcomeInput(Input):
    purchased: bool | None


class VerificationInput(Input):
    accepted: bool
    intended_purchase: bool
    purpose_met: bool
    conclusion: str = Field(min_length=10, max_length=1000)
    evidence_path: str | None = Field(default=None, max_length=500)
