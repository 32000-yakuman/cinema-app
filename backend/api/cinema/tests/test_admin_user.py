from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

class AdminUserTogglePartialUpdateTests(TestCase):
    """
    AdminUserDetailView.patch()の回帰テスト。

    以前はpartial=Trueが指定されておらず、フロントが1フィールドだけ
    送るPATCHリクエスト(例: {"is_staff": true})を送ると、リクエストに
    含まれていない他のフラグ(is_active, is_staff_member)がモデルの
    デフォルト値で意図せず上書きされてしまうバグがあった。
    """

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username="admin-user", password="test-password", is_staff=True
        )

    def test_patching_one_flag_does_not_reset_other_flags(self):
        """
        is_staffだけを更新しても、is_staff_memberとis_activeの
        現在の値が保たれること
        """
        target_user = User.objects.create_user(
            username="target-user",
            password="test-password",
            is_staff_member=True,
            is_active=False,
        )
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.patch(
            f"/api/cinema/admin/users/{target_user.id}/",
            {"is_staff": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        target_user.refresh_from_db()

        # 更新対象のフラグは反映されていること
        self.assertTrue(target_user.is_staff)
        # 更新対象外のフラグは維持されていること
        # (以前のバグではis_staff_memberがFalse、is_activeがTrueに
        #  リセットされていた)
        self.assertTrue(target_user.is_staff_member)
        self.assertFalse(target_user.is_active)
