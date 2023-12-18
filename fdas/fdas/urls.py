from django.contrib import admin
from django.urls import path
from mainapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('get_data/', views.get_data, name='get_data'),  # URL for the get_data view
]