# filters.py
import django_filters
from ..models import SiteAppRecord


class SiteAppRecordFilter(django_filters.FilterSet):
    category_name = django_filters.CharFilter(
        field_name="category__name", lookup_expr="icontains"
    )

    class Meta:
        model = SiteAppRecord
        fields = [
            "category",
            "category_name",
            "date_created",
        ]