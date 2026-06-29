"""HTML views for the catalog app.

Testing that the page renders correctly
"""
from django.http import HttpResponse


def index(request):
    """Temporary landing page; confirms routing works end to end."""
    return HttpResponse(
        "<h1>retailapi</h1> Render test "
    )