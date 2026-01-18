from rest_framework import serializers
from ..models import SiteAppCategory, SiteAppRecord


class SiteAppCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteAppCategory
        fields = [
            "id",
            "name",
        ]


class SiteAppRecordSerializer(serializers.ModelSerializer):
    # Optional: show category name in response
    category_name = serializers.CharField(
        source="category.name", read_only=True
    )

    # Optional: make user read-only (auto-set from request)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = SiteAppRecord
        fields = [
            "id",
            "name",
            "category",
            "category_name",
            "description",
            "date_created",
            "date_modified",
            "user",
        ]
        read_only_fields = [
            "date_created",
            "date_modified",
        ]
