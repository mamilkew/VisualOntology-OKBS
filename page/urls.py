from django.urls import path
from . import views, admin, forcegraph_views, timelinegraph_views

urlpatterns = [
    path('', views.index, name='index'),
    path('property_datemarked/', admin.DateMarkedAutoComplete.as_view(), name='property_datedmarked'),
    path('property_faceted/', admin.PropertyAutoComplete.as_view(), name='property_faceted'),

    path('forcegraph/<int:page_id>/', forcegraph_views.forcegraph, name='pages_forcegraph'),
    path('filter_forcegraph/', forcegraph_views.filter_forcegraph, name='filter_forcegraph'),  # for ajax in forcegraph.html

    path('timeline/<int:page_id>/', timelinegraph_views.timelinegraph, name='timelinegraph'),
    path('filter_timeline/', timelinegraph_views.filter_timeline, name='filter_timeline'),
]
