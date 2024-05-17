import asyncio
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async, async_to_sync
from .models import Room, Question, Result
from channels.db import database_sync_to_async
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache  
from main.models import MyUser
from django.utils import timezone

import asyncio
from django.core.cache import cache
from asgiref.sync import sync_to_async

class QuizConsumer(AsyncWebsocketConsumer):

   async def connect(self):
      self.room_token = self.scope['url_route']['kwargs']['room_token']
      self.room_group_name = f'quiz_{self.room_token}'
      

      self.room = await sync_to_async(Room.objects.get)(token=self.room_token)
      self.user = self.scope['user'].id
      print('self.user', self.user)

      await self.channel_layer.group_add(self.room_group_name, self.channel_name)
      await self.accept()

      if self.room.state == 'hub':
         await self.handle_hub_room()
      elif self.room.state == 'active':
         await self.handle_active_room()




   async def fetch_questions_to_cache(self):
      if not cache.get(self.room_token):
         questions = await sync_to_async(list)(Question.objects.filter(quiz=self.room.quiz_id))
         print('Получаем список вопросов для текущей комнаты')
         question_data = []
         for question in questions:
               answers = await sync_to_async(list)(question.answer_set.values_list('text', flat=True))

                  # Получаем URL изображения, если оно существует
               image_url = None
               if question.Images:
                  print('Изображение существует')
                  print(question.Images.url)
                  image_url = question.Images.url
                  print('Ссылка на изображение', image_url)
               question_full_text = None
               if question.full_text:
                  question_full_text = question.full_text

               question_data.append({
                  'text': question.text,
                  'full_text': question_full_text,
                  'answers': answers,
                  'time': question.time,
                  'quiz_type': question.tupe_question,
                  'image_url': image_url  # Добавляем ссылку на изображение в данные о вопросе
               })

         print('Создаем список словарей с данными о вопросах') 
         await sync_to_async(cache.set)(self.room_token, question_data, timeout=1800)
         print('Кэш заполнен')
      else:
         print('Кэш уже заполнен')

   @receiver(post_save, sender=Room)
   def handle_room_state_change(sender, instance, **kwargs):
      channel_layer = get_channel_layer()
      async_to_sync(channel_layer.group_send)(
         f'quiz_{instance.token}',
         {
               'type': 'room.state_changed',
               'state': instance.state,
         }
      )
      print('состояние комнаты', instance.state)

   async def room_state_changed(self, event):
      new_state = event['state']
      print(f'Новое состояние комнаты: {new_state}')
      if new_state == 'hub':
         await self.handle_hub_room()
      elif new_state == 'active':
         await self.handle_active_room()
      elif new_state == 'finished':
         await self.send(text_data=json.dumps({'type': 'end_of_questions'}))

   async def handle_hub_room(self):
      print('Комната хаба')
      print(self.scope['user'])
      self.user_index = cache.get(f'Index_{self.room_token}' )
      print(self.user_index)
      if self.user_index is None:
         await sync_to_async(cache.set)(f'Index_{self.room_token}', {'user': self.user,'current_question_index': 0}, timeout=3600)
      else:
         print('Пользователь присутствует в группе')

      users_list = await self.get_users_list()
      # Проверяем, что список пользователей не пустой
      if users_list:
         # Проверяем, есть ли пользователь уже в списке участников
         if not any(user['id'] == self.user for user in users_list):
               # Если пользователь еще не в списке, добавляем его
               users_list.append({'id': self.user, 'name': self.scope['user'].get_full_name()})
               await self.send_users_list_to_group(users_list)
         else:
               print('Пользователь уже присутствует в списке')
      else:
         print('Список пользователей пуст')

   


   async def handle_active_room(self):
      # print('Активная комната')
      self.user_index = cache.get(f'Index_{self.room_token}' )
      if self.user_index is not None:
         self.current_question_index = self.user_index.get('current_question_index', 0)
         await self.fetch_questions_to_cache() 
         await self.send_question()
      else:
         # print('Пользователь не присутствует в группе')
         users_cache_key = f'users_list_{self.room_token}'
         # print('users_cache_key', users_cache_key)
         users_list = cache.get(users_cache_key)
         if users_list is None:
               # print('users_list', users_list)
               await self.send(text_data=json.dumps({
                  'type': 'users_list_active_room',
                  'users': users_list
               }))
         else:
               print('Комната пустая ')





   async def get_users_list(self):
      # Получаем текущий список пользователей из кеша
      users_cache_key = f'users_list_{self.room_token}'
      users_list = cache.get(users_cache_key)
      # print('Список пользователей сохранен в кеше:', users_list)

      # Запрашиваем текущего пользователя из базы данных
      user = await sync_to_async(MyUser.objects.get)(id=self.user)
      user_data = {'id': user.id, 'name': user.get_full_name()}
      # print('Текущий пользователь:', user_data)

      # Если список пользователей в кеше не пустой, добавляем текущего пользователя
      if users_list is not None:
         # Проверяем, есть ли пользователь уже в списке
        user_ids = [u['id'] for u in users_list]
      #   print('Список пользователей в кеше:', user_ids)
      #   print('Текущий пользователь:', self.user)
        if self.user not in user_ids:
            users_list.append(user_data)
      else:
         # Если список пустой, создаем новый список с текущим пользователем
         users_list = [user_data]

      # print('Текущий пользователь добавлен в список:', user_data)

      # Сохраняем обновленный список пользователей в кеше, только если список существует
      if users_list:
         await sync_to_async(cache.set)(users_cache_key, users_list, timeout=3600)
         # print('Обновленный список пользователей сохранен в кеше:', users_list)
         await self.send_users_list_to_group(users_list)
         return users_list
      else:
         print('Список пользователей пуст, ничего не сохранено в кеше')

      


   async def send_users_list_to_group(self, users_list):
      await self.channel_layer.group_send(
         self.room_group_name,
         {
               'type': 'group.users_list',
               'users': users_list
         }
      )

   async def group_users_list(self, event):
      # Отправляем список пользователей всем участникам группы
      users_list = event['users']
      await self.send(text_data=json.dumps({
         'type': 'users_list',
         'users': users_list
      }))


   async def remove_user_from_list_and_cache(self):
      # Получаем текущий список пользователей из кеша
      users_cache_key = f'users_list_{self.room_token}'
      users_list = cache.get(users_cache_key)

      # Если список пользователей есть в кеше
      if users_list:
         # Ищем индекс пользователя в списке по его ID
         user_index = next((index for index, user in enumerate(users_list) if user['id'] == self.user), None)

         # Если пользователь найден в списке, удаляем его
         if user_index is not None:
               del users_list[user_index]

               # Обновляем кеш без отключившегося пользователя
               await sync_to_async(cache.set)(users_cache_key, users_list, timeout=3600)
               # print('Пользователь удален из списка и кеша')

               # Отправляем обновленный список пользователей всем участникам группы
               await self.send_users_list_to_group(users_list)

               # Отправляем событие на клиентскую сторону для обновления списка пользователей
               await self.send(text_data=json.dumps({
                  'type': 'update_users_list',
                  'users': users_list
               }))
         else:
               print('Пользователь не найден в списке')
      else:
         print('Список пользователей в кеше отсутствует')



   async def disconnect(self, close_code):
      # print('Отключение')
      await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
      self.room = await sync_to_async(Room.objects.get)(token=self.room_token)
      if self.room.state == 'hub':
         # print('Отключение от хаба')
         await sync_to_async(cache.delete)(f'Index_{self.user}_{self.room_token}')
         await self.remove_user_from_list_and_cache()
      elif self.room.state == 'active':
         print('Отключение от активной комнаты')

   async def receive(self, text_data):
      # print('Получено сообщение', text_data)
      # Обработка сообщения, полученного от пользователя
      text_data_json = json.loads(text_data)
      message = text_data_json['message']
      # print('Сообщение', message)



   async def send_question(self):
      print('Текущий индекс вопроса', self.current_question_index)
      question_data = cache.get(self.room_token)
      if not question_data or self.current_question_index >= len(question_data):
         await self.send(text_data=json.dumps({'type': 'end_of_questions'}))
         return 'end'
      
      question = question_data[self.current_question_index]
 
      
      question_answers = question_data[self.current_question_index]['answers']
      question_data_send = {
         'type': 'question',
         'question_number': self.current_question_index ,
         'question_text': question['text'],
         'full_text': question['full_text'],
         'quiz_type': question['quiz_type'],
         'answers': question_answers,
         'time': question['time'],
      }

      # Добавляем ссылку на изображение, если оно есть
      if 'image_url' in question:
         question_data_send['image_url'] = question['image_url']
         # print('Ссылка на изображение', question_data_send['image_url'])

      # print('Отправляем вопрос', question_data_send)
      await self.send(text_data=json.dumps(question_data_send))
      await sync_to_async(cache.set)(f'Index_{self.room_token}', {'user':self.user,'current_question_index': self.current_question_index + 1})
      
      self.current_question_index += 1
      return 'sent', question['time']

   async def send_questions_periodically(self):
      while True:
         status = await self.send_question()
         # print('status',status)
         if status == 'end':
               break
         elif status[0] == 'sent':
               await asyncio.sleep(status[1]+1)
         