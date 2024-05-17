from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse

from .models import Quiz, Room, Question, Result, Answer,history
from main.models import StudentGroup, UserUUID, MyUser
from django.db.models import Sum, Count, F, Q
from django.db.models import Count, F, Window
from django.db.models.functions import Rank
from django.db.models import Case, When, Value, CharField
from django.utils import timezone

def category(request):
    return render(request, 'quiz/main.html')

@login_required(login_url='/autofication/')
def form(request):
    users = request.user
    if not users.is_staff:
        return HttpResponseForbidden("У вас нет прав для просмотра этой страницы.")
        
    group = users.group
    context = {
        'User': users,
        'Group': group
    }
    return render(request, 'quiz/forma.html', context)

@login_required(login_url='/autofication/')
def quiz(request,group_slug):
    if request.user.is_active != 1:
        return HttpResponseForbidden("Ваш аккаунт не активирован. Пожалуйста, активируйте ваш аккаунт, чтобы получить доступ к этой странице.",status=403)
    current_time = timezone.now()
    instance = get_object_or_404(StudentGroup, slug=group_slug)
    if instance != request.user.group and not request.user.is_staff:
        return HttpResponseForbidden("У вас нет прав для просмотра этой страницы.", status=403)
    rooms = Room.objects.filter(t_start__lte=current_time, t_end__gte=current_time, group=instance, is_visible=True)
    user = request.user

    uuiD = UserUUID.objects.get(user=user)
    context = {
        'User': user,
        'Rooms': rooms,
        'UUID': uuiD,
        'history': history.objects.filter(user=user),
    }

    return render(request, 'quiz/main.html', context)
    


@login_required(login_url='/autofication/')
def Room_view(request, group_slug, token):
    if request.user.is_active != 1:
        return HttpResponseForbidden("Ваш аккаунт не активирован. Пожалуйста, активируйте ваш аккаунт, чтобы получить доступ к этой странице.")

    quiz_instance = get_object_or_404(StudentGroup, slug=group_slug)
    room_instance = get_object_or_404(Room, token=token)
     
   
    context = {
        'User': request.user,
        'Group': group_slug,
        'Room': room_instance
    }

    return render(request, 'quiz/card.html', context)

 

def get_active_rooms(request):
    current_time = timezone.now()
    user_group = request.user.group
    active_rooms = Room.objects.filter(t_start__lte=current_time, t_end__gte=current_time, group=user_group, is_visible=True)
    data = [{'quiz_title': room.quiz.title, 't_start': room.t_reg.strftime("%H:%M:%S"), 'group_slug': room.group.slug, 'token': room.token} for room in active_rooms]
    return JsonResponse(data, safe=False)



from django.db.models import Sum

def submit_answer(request, group_slug, token):
    room_instance = get_object_or_404(Room, token=token)
    if request.method == 'GET':
        if not request.user.is_active:
            return HttpResponseForbidden("Ваш аккаунт не активирован. Пожалуйста, активируйте ваш аккаунт, чтобы получить доступ к этой странице.")
        
        user = request.user

        # Получаем общий счет пользователя
        user_results = Result.objects.filter(user=user, room=room_instance)
        total_score = user_results.aggregate(total_score=Sum('score'))['total_score'] or 0

        # Получаем количество правильных ответов пользователя
        correct_answers_count = user_results.filter(score__gt=0).count()

        # Получаем место пользователя среди всех участников
        user_rank = Result.objects.filter(room=room_instance) \
            .values('user__id') \
            .annotate(total_score=Sum('score')) \
            .annotate(rank=Window(expression=Rank(), order_by=F('total_score').desc())) \
            .filter(user_id=user.id) \
            .order_by('-total_score') \
            .values('rank') \
            .first()['rank']

        # Получаем полное имя пользователя
        username = user.get_full_name()

        # Получаем топ пользователей
        top_players = Result.objects.filter(room=room_instance) \
            .values('user__id', 'user__first_name', 'user__last_name') \
            .annotate(total_score=Sum('score')) \
            .annotate(rank=Window(expression=Rank(), order_by=F('total_score').desc()))[:10]

        top_players_info = []
        print(top_players)
        for player in top_players:
            player_info = {
                'rank': player['rank'],
                'first_name': player['user__first_name'],
                'last_name': player['user__last_name'],

                'total_score': player['total_score'],
                'correct_answers_count': Result.objects.filter(user_id=player['user__id'], score__gt=0).count()
            }
            top_players_info.append(player_info)

        user_answers = user_results.annotate(
            is_correct=Case(
                When(score__gt=0, then=Value('правильный')),
                default=Value('неправильный'),
                output_field=CharField()
            )
        ).order_by('question__text').values('question__text', 'is_correct')

        current_user_info = {
            'username': username,
            'total_score': total_score,
            'correct_answers_count': correct_answers_count,
            'user_rank': user_rank
        }
        existing_history_entry = history.objects.filter(user=user, room=room_instance).exists()
        if not existing_history_entry:
            histor = history.objects.create(
                user=user,
                room=room_instance,
                quiz=room_instance.quiz,
                position=user_rank,
                skore=total_score
            )

        context = {
            'Top_players': top_players_info,
            'Current_user_info': current_user_info,
            'User_answers': list(user_answers),
        }

        return JsonResponse(context)

    elif request.method == 'POST':
        if not request.user.is_active:
            return JsonResponse({'error': 'Ваш аккаунт не активирован.'}, status=403)
        print('request post',request.POST)

        selected_option = request.POST.get('selected_option')
        question_text = request.POST.get('question_text')
        answer_time_str = request.POST.get('answer_time').strip()  # Удаляем лишние пробелы из строки времени
        minutes, seconds = map(int, answer_time_str.split(':'))  # Разделяем строку по символу ':' и преобразуем каждую часть в целое число
        total_seconds = minutes * 60 + seconds  # Вычисляем общее количество секунд
        question_instance = get_object_or_404(Question, text=question_text)
        
        # Получаем время, выделенное на ответ на данный вопрос
        allocated_time = question_instance.time  

        if selected_option is not None:
            correct_answer_instances = Answer.objects.filter(question=question_instance, is_correct=True).values_list('text', flat=True)
            if selected_option in correct_answer_instances:
                print('Правильный ответ')
                # Получаем время, выделенное на ответ на данный вопрос
                allocated_time = question_instance.time
                print('answer_time', answer_time_str)
                print('allocated_time', allocated_time)
                
                # Рассчитываем процент времени, потраченного на ответ на вопрос
                time_percentage = total_seconds / allocated_time
                time_percentage = 1 - time_percentage
                print('time_percentage', time_percentage)

                # Рассчитываем количество баллов, учитывая уменьшение за каждые 10% времени
                score = 100  # Предположим, что 100% времени дает 100 баллов
                intervals_count = int(time_percentage * 10)
                for _ in range(intervals_count):
                    score -= 10  # Уменьшаем количество баллов на 10 за каждые 10% времени
                print('score', score)
                score = max(score, 0)  # Проверяем, чтобы результат не был отрицательным
                print('score', score)
            else:
                score = 0


        result = Result.objects.create(
            user=request.user,
            quiz=room_instance.quiz,
            question=question_instance,
            room=room_instance,
            score=score  
        )
        print('Оценка: ', score)
        return JsonResponse({'message': 'Ответ успешно получен и обработан.'})

    else:
        return JsonResponse({'error': 'Метод запроса должен быть GET или POST.'}, status=405)

def check_start_quiz(request,group_slug,room_id):
    if request.method == 'GET':
        # Получаем текущее время
        room = get_object_or_404(Room, token=room_id)
        current_time = timezone.now()
        # Если текущее время больше или равно времени начала регистрации
        if room.state != 'active':
            if current_time >= room.t_reg:
                # Устанавливаем состояние комнаты в 'active'
                room.state = 'active'
                room.save()
                return JsonResponse({'state': 'active'})
            else:
                return JsonResponse({'state': 'inactive'})
        else:
            return JsonResponse({'state': 'active'})

