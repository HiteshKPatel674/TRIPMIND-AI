from django.urls import path

from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('chat/', views.chat_page, name='chat'),
    path('chat/send/', views.chat_send, name='chat_send'),
    path('trips/', views.trips_list, name='trips'),
    path('trips/<uuid:pk>/', views.trip_detail, name='trip_detail'),
    path('api/trips/<uuid:pk>/transport/', views.trip_transport_api, name='trip_transport_api'),
    path('api/items/<uuid:pk>/image/', views.item_image_api, name='item_image_api'),
    path('trips/<uuid:pk>/pdf/', views.trip_pdf, name='trip_pdf'),
    path('trips/<uuid:pk>/email/', views.trip_email, name='trip_email'),
    path('trips/<uuid:pk>/delete/', views.trip_delete, name='trip_delete'),
    path('pay/create/<uuid:pk>/', views.pay_create, name='pay_create'),
    path('pay/verify/', views.pay_verify, name='pay_verify'),
]
