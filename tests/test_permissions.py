tests/test_permissions.py
═══════════════════════════════════════════════════════════════
اختبارات محرك الصلاحيات (القاعدة الذهبية).
═══════════════════════════════════════════════════════════════
"""

import pytest

from config.constants import RankLevel
from services.permission_service import PERMISSION_MATRIX


def test_permission_matrix_completeness():
    """التأكد من أن كل الصلاحيات الحرجة معرّفة."""
    critical = ["ban", "mute", "kick", "promote_admin", "broadcast", "manage_developers"]
    for perm in critical:
        assert perm in PERMISSION_MATRIX, f"الصلاحية {perm} غير معرّفة"


def test_rank_hierarchy():
    """التأكد من الترتيب الصحيح للرتب."""
    assert RankLevel.MEMBER < RankLevel.ADMIN
    assert RankLevel.ADMIN < RankLevel.OWNER
    assert RankLevel.OWNER < RankLevel.MAIN_DEVELOPER


def test_developer_permissions_higher():
    """صلاحيات المطور أعلى من المالك."""
    assert PERMISSION_MATRIX["broadcast"] >= RankLevel.DEVELOPER
    assert PERMISSION_MATRIX["manage_developers"] == RankLevel.MAIN_DEVELOPER


def test_member_basic_permissions():
    """العضو العادي يملك الصلاحيات الأساسية فقط."""
    assert PERMISSION_MATRIX["use_replies"] == RankLevel.MEMBER
    assert PERMISSION_MATRIX["ban"] > RankLevel.MEMBER
