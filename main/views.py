from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from .models import MyUser, StudentGroup
from django.contrib.auth.hashers import check_password as check_password_hasher
import re
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import RegistrationForm
from django.contrib.auth import logout
from django.http import JsonResponse
from .models import Group
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage, send_mail
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from app.settings import DEFAULT_FROM_EMAIL
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib import messages
from django.core.cache import cache 
from .models import UserUUID
from quiz.models import Result
from django.db.models import Count, Q, Sum
import uuid
def index(request):# главная
    return render(request, 'main/index.html', {'title': 'Главная'})   

def registration_view(request):# регистрация
    if request.user.is_authenticated:
        return redirect('cabin', request.user.UUID.UUID)
    groups = StudentGroup.objects.all()
    select_group = groups.first()
    return render(request, 'main/reg.html', {'Groups': groups, 'selected_group_id': select_group.id,'title': 'Регистрация'})

def autofication_view(request): # авторизация
    if request.user.is_authenticated:
        return redirect('cabin', request.user.UUID.UUID)
    return render(request, 'main/auto.html', {'title': 'Авторизация'})

def restore_view(request): # восстановление
    return render(request, 'main/restore.html', {'title': 'Восстановление'})

def my_logout_view(request): # выход
    logout(request)
    return redirect('index')

def custom_password_reset_complete(request): # Успешная смена пароля
    return redirect('autofication')



def search_group(request):
    group_name = request.GET.get('group', '')
    results = []
    if group_name:
        groups = StudentGroup.objects.filter(name__icontains=group_name)[:5]  # Получаем первые 5 результатов поиска
        results = [{'group_name': group.name, 'group_id': group.id} for group in groups]
    return JsonResponse({'results': results})
        
def autoficationDone_view(request): # подтверждение почты
    
    return render(request, 'main/auto_done.html', {'title': 'Регистрация'})


@login_required(login_url='/autofication/')
def cabin_view(request,uid): # кабинет
    uid_obj = get_object_or_404(UserUUID, UUID=uid) # тут касяк 
    user = MyUser.objects.get(UUID=uid_obj)
    avatar = user.avatar

    if request.user.is_active != 1:
        return HttpResponseForbidden("Ваш аккаунт не активирован. Пожалуйста, активируйте ваш аккаунт, чтобы получить доступ к этой странице.")

    if request.method == 'POST':
        user.avatar = request.FILES.get('avatar')
        user.save()

    if user.group :
        Groups = user.group.slug

    posetitel = request.user
    context = {'group': Groups, 
                'user': user, 
                'uid_obj': uid_obj, 
                'avatar': avatar, 
                'posetitel': posetitel, }
    return render(request, 'main/cabin.html',context)

from collections import defaultdict

def lider_board_view(request, uid):
    uid_obj = get_object_or_404(UserUUID, UUID=uid)
    lider_board = cache.get('lider_board')
    
    if lider_board is None:
        # Получение данных для доски лидеров
        leaderboard_data = Result.objects.values('user').annotate(total_score=Sum('score')).order_by('-total_score')
        
        # Подготовка словаря для хранения лидеров групп
        group_leaders = defaultdict(list)

        leaders = []
        rank_counter = 1  # Инициализируем счетчик места в общем рейтинге
        group_rank_counters = defaultdict(int)  # Инициализируем счетчики мест для каждой группы

        for entry in leaderboard_data:
            user_id = entry['user']
            user = MyUser.objects.get(id=user_id)
            leader_entry = {
                'user_uuid': str(user.UUID),
                'full_name': user.get_full_name(),
                'total_score': entry['total_score'],
                'user_group': user.group.name,
                'course': user.course,
                'rank': rank_counter,  # Используем счетчик места в общем рейтинге
            }
            leaders.append(leader_entry)
            rank_counter += 1  # Увеличиваем счетчик места в общем рейтинге

            # Обновляем счетчик места в рамках текущей группы
            leader_entry['group_rank'] = group_rank_counters[user.group.name] + 1
            group_rank_counters[user.group.name] += 1

        # Определяем место текущего пользователя
        current_user_uuid = str(uid_obj)
        current_user_info = None
        
        for entry in leaders:
            if entry['user_uuid'] == current_user_uuid:
                current_user_info = entry
                break

        current_user_rank = current_user_info['rank'] if current_user_info else None

        # Группировка лидеров по группам
        for entry in leaders:
            group_leaders[entry['user_group']].append(entry)
        
        # Кэширование данных доски лидеров
        cache.set('lider_board', (leaders, group_leaders), 24*60*60)
    else:
        leaders, group_leaders = lider_board
        current_user_uuid = str(uid_obj)
        current_user_info = None
        
        for entry in leaders:
            if entry['user_uuid'] == current_user_uuid:
                current_user_info = entry
                break

        current_user_rank = current_user_info['rank'] if current_user_info else None

    # Получение группы текущего пользователя и его места в этой группе
    if current_user_info:
        user_group = current_user_info['user_group']
        user_group_leaders = group_leaders.get(user_group, [])
        user_group_rank = user_group_leaders.index(current_user_info) + 1 if current_user_info in user_group_leaders else None
    else:
        user_group = None
        user_group_leaders = []
        user_group_rank = None

    data = {
        'leaders': leaders,
        'current_user_rank': current_user_rank,
        'user_group_leaders': user_group_leaders,
        'user_group_rank': user_group_rank,
    }
    return JsonResponse(data)




def login_view(request):  # вход
    if request.user.is_authenticated:
        messages.error(request, 'Вы уже вошли.')
        return redirect('cabin', request.user.UUID.UUID)
    elif request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        if MyUser.objects.filter(email=email).exists():
            # Если пользователь существует, получаем пользователя
            user = MyUser.objects.get(email=email)

            # Проверяем пароль пользователя
            if user.check_password(password):  # Используем метод check_password объекта пользователя
                # Аутентификация успешна, выполняем вход пользователя
                login(request, user)
                return redirect('cabin', user.UUID.UUID)
            else:
                # Неверный пароль
                messages.error(request, 'Неверный пароль')
                return render(request, 'main/auto.html', {'title': 'Авторизация','email': email,'password': password})
        else:
            # Пользователь с указанным адресом электронной почты не найден
            messages.error(request, 'Пользователь с указанным адресом электронной почты не найден.')
            return render(request, 'main/auto.html', {'title': 'Авторизация','email': email,'password': password})
    else:
        messages.error(request, 'Метод запроса должен быть POST.')
        return HttpResponse(status=405)




def main_view(request):
    return render(request, 'main/main.html')



def submit_form_view(request):  
    if request.user.is_authenticated:
        print(request)
        logout(request)# Пользователь уже аутентифицирован
        print(request)
        
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            surname = form.cleaned_data['surname']
            course = form.cleaned_data['course']
            group_name = form.cleaned_data['group']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            activate_token = str(uuid.uuid4())
            cache.set(f'create_user_{activate_token}', {
                'first_name': first_name,
                'last_name': last_name,
                'surname': surname,
                'course': course,
                'group_name': group_name,
                'email': email,
                'password': password
            }, timeout=60 * 60)
            print(email)
            activation_link = f"http://{request.get_host()}/activate/{activate_token}"
            html_message = render_to_string('main/activation_email.html', {'activation_link': activation_link})
            plain_message = strip_tags(html_message)
            send_mail('Подтверждение регистрации', plain_message, settings.DEFAULT_FROM_EMAIL, [email,], html_message=html_message)
            return redirect('autofication_done')
        else:
            errors = form.errors
            return render(request, 'main/reg.html', {'errors': errors})
    else:
        return render(request, 'main/reg.html')


def activate_view(request,token):
    user_cache  = cache.get(f'create_user_{token}')
    group = StudentGroup.objects.get(name=user_cache['group_name'])
    if user_cache :
        user = MyUser.objects.create(
            email=user_cache ['email'],
            first_name=user_cache ['first_name'],
            last_name=user_cache ['last_name'],
            surname=user_cache ['surname'],
            course=user_cache ['course'],
            group=group,
        )
        user.set_password(user_cache ['password'])
        user.save()
        cache.delete(f'create_user_{token}')
        return redirect('autofication')  # Перенаправляем пользователя на страницу с сообщением об успешной активации
    else:
        return render(request,'main/reg.html')

 