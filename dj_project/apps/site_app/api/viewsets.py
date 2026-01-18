from rest_framework import viewsets, permissions
from ..models import SiteAppCategory, SiteAppRecord
from .serializer import SiteAppCategorySerializer, SiteAppRecordSerializer
from .filters import SiteAppRecordFilter


class SiteAppCategoryViewSet(viewsets.ModelViewSet):
    queryset = SiteAppCategory.objects.all()
    serializer_class = SiteAppCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]


class SiteAppRecordViewSet(viewsets.ModelViewSet):
    queryset = SiteAppRecord.objects.select_related("category", "user")
    serializer_class = SiteAppRecordSerializer
    filterset_class = SiteAppRecordFilter
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    # permission_classes = [permissions.IsAuthenticated]

    search_fields = [
        "name",
        "description",
        "category__name",
    ]

    filterset_fields = {
        "category": ["exact"],
        "user": ["exact"],
        "date_created": ["gte", "lte"],
    }

    ordering_fields = [
        "name",
        "date_created",
        "date_modified",
    ]
    ordering = ["-date_created"]

    def perform_create(self, serializer):
        # Automatically attach logged-in user
        serializer.save(user=self.request.user)
