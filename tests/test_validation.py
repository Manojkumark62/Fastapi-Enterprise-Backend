import pytest
from pydantic import ValidationError

from core.constants import OrderStatusEnum
from schemas.auth import UserRegisterRequest
from schemas.order import OrderStatusUpdateRequest


def test_registration_rejects_weak_password():
    with pytest.raises(ValidationError):
        UserRegisterRequest(email="user@example.com", full_name="User", password="weak")


def test_order_status_is_constrained_to_domain_values():
    assert OrderStatusUpdateRequest(status=OrderStatusEnum.CONFIRMED).status == OrderStatusEnum.CONFIRMED
    with pytest.raises(ValidationError):
        OrderStatusUpdateRequest(status="made_up_status")