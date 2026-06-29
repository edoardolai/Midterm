"""Top-level URL configuration for the retailapi project.

The project delegates all application routes to the ``catalog`` app and
exposes Django's built-in admin site.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("catalog.urls")),
    path("admin/", admin.site.urls),
]