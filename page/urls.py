from django.urls import path

from . import views, admin

urlpatterns = [
    path('', views.index, name='index'),
    path('property_datemarked/', admin.DateMarkedAutoComplete.as_view(), name='property_datedmarked'),
    path('property_faceted/', admin.PropertyAutoComplete.as_view(), name='property_faceted'),
]