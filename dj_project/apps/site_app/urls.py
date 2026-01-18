from rest_framework.routers import DefaultRouter
from .api.viewsets import SiteAppCategoryViewSet, SiteAppRecordViewSet

router = DefaultRouter()
router.register(r"categories", SiteAppCategoryViewSet, basename="category")
router.register(r"records", SiteAppRecordViewSet, basename="record")

urlpatterns = router.urls