from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_file, name='upload_file'),
    path('download/<uuid:transfer_id>/', views.download_file, name='download_file'),
    path('cleanup/<uuid:transfer_id>/', views.cleanup_file, name='cleanup_file'),
    path('status/<uuid:transfer_id>/', views.get_transfer_status, name='transfer_status'),
]
