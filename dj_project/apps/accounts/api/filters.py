from django_filters import rest_framework as filters
from django.contrib.auth.models import Group
from ..models import User


class UserFilter(filters.FilterSet):
    is_staff = filters.BooleanFilter(field_name="is_staff")
    is_superuser = filters.BooleanFilter(field_name="is_superuser")
    groups = filters.CharFilter(method="filter_by_groups")

    class Meta:
        model = User
        fields = {
            "id": ["exact", "lte", "gte", "icontains", "contains"],
            "username": ["exact", "icontains"],
            "email": ["exact", "icontains"],
            "first_name": ["exact", "icontains"],
            "last_name": ["exact", "icontains"],
        }

    def filter_by_groups(self, queryset, name, value):
        # Split the comma-separated values and filter by group IDs
        group_ids = [
            int(group_id) for group_id in value.split(",") if group_id.isdigit()
        ]
        return queryset.filter(groups__id__in=group_ids).distinct()


class GroupFilter(filters.FilterSet):

    class Meta:
        model = Group
        fields = {
            "id": ["exact", "lte", "gte"],
            "name": ["exact", "icontains"],
        }
