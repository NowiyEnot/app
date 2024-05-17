from django.contrib import admin
from django.urls import include, path

from quiz import views

urlpatterns = [
    path('<slug:group_slug>/<slug:room_id>/check_room_state/', views.check_start_quiz, name='check_start_quiz'),
    path('<slug:group_slug>/<slug:token>/submit_answer/', views.submit_answer, name='submit_answer'),
    # path('submit_answer/', views.category, name='category'),
    path('<slug:group_slug>/', views.quiz, name='quiz'),
    path('<slug:group_slug>/<slug:token>/', views.Room_view, name='Room'),
    path('create', views.form, name='form'),
    path('get_active_rooms', views.get_active_rooms, name='get_active_rooms'),
    
]