"""URL routes for the catalog app.
"""
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from . import api, views

app_name = "catalog"

urlpatterns = [
    path("", views.index, name="index"),
    path("product/add/", views.product_add, name="product-add"),
    path("deals/", views.deals_page, name="deals-page"),

    path("api/product/", api.ProductCreate.as_view(), name="product-create"),
    path("api/product/<int:pk>/", api.ProductDetail.as_view(), name="product-detail"),
    path("api/category/<int:category_pk>/products/", api.CategoryProducts.as_view(), name="category-products"),
    path("api/deals/", api.DealsList.as_view(), name="deals-list"),
    path("api/brand/<int:pk>/", api.BrandDetail.as_view(), name="brand-detail"),
    path("api/analytics/category-pricing/", api.CategoryPricingAnalytics.as_view(), name="category-pricing"),

    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="catalog:schema"), name="docs"),
]