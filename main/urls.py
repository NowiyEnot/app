from django.urls import include, path
from django.contrib.auth import views as auth_views

from main import admin, views

urlpatterns = [
    path('', views.index, name='index'),
    
    path('autofication/', views.autofication_view, name='autofication'),
    path('submit_form/', views.submit_form_view, name='submit_form'), 
    path('restore/', views.restore_view, name='restore'),
    path('login/', views.login_view, name='login'),
    
    
    path('cabin/<str:uid>/', views.cabin_view, name='cabin'),
    path('cabin/<str:uid>/leaderboard', views.lider_board_view, name='lider_board_view'),
    path('logout/', views.my_logout_view, name='logout'),
    path('search_group/', views.search_group, name='search_group'),
    # востановление пароля (потом вынесу в отдельный сервис )
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='main/restore.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='main/custom_password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='main/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', views.custom_password_reset_complete, name='password_reset_complete'),


    # Регистрация (потом вынесу в отдельный сервис )
    path('registration/', views.registration_view, name='registration'),    
    path('autofication/done/', views.autoficationDone_view,name='autofication_done'),  # тут нужно создать сообщение о том что письмо отправленоо на почту/ можно обьеденить с  password_reset/done/
    path('activate/<token>/', views.activate_view, name='activate_view'),
]
