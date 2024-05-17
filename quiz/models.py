from django.db import models

from main.models import MyUser,StudentGroup

import uuid
import os
from PIL import Image

class Quiz(models.Model):
    title = models.CharField(verbose_name='Название', max_length=100)
    slug = models.SlugField(verbose_name='URL', max_length=100, unique=False)
    author = models.ForeignKey(MyUser, verbose_name='Автор', on_delete=models.CASCADE)
    description = models.TextField(verbose_name='Описание', blank=True)
    create = models.DateTimeField(verbose_name='Создано', auto_now_add=True)
    modification = models.DateTimeField(verbose_name='Изменено', auto_now=True)

    class Meta:
        db_table = 'quizzes'
        verbose_name = 'Викторина'
        verbose_name_plural = 'Викторины'
        ordering = ['-create']

    def __str__(self):
        return self.title




class Question(models.Model):
    STATE_CHOICES = (
        (1, '1 Вариант ответа'),
        (2, 'Несколько вариант ответа'),
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    text = models.TextField('Текст вопроса', max_length=150)
    full_text = models.TextField('Полное описание', blank=True)
    Images = models.ImageField(upload_to='quiz/%Y/', blank=True, null=True)
    tupe_question = models.IntegerField('Тип вопроса', default=1, choices=STATE_CHOICES)
    time = models.IntegerField('Время ответа', default=20)

    def save(self, *args, **kwargs):

        max_width = 800
        max_height = 600
        if self.Images:
            with Image.open(self.Images) as img:
                print(img.width, img.height)
                if img.width > max_width or img.height > max_height:
                    # Изменяем размер изображения
                    print(1)
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                    print(2)
                    print(img.width, img.height)
                    # Сохраняем измененное изображение на диск
                    img.save(self.Images.path)
                    print(3)

        if self.pk:
            try:
                old_question = Question.objects.get(pk=self.pk)
                if self.Images and old_question.Images and old_question.Images.name != self.Images.name:
                    if os.path.exists(old_question.Images.path):
                        os.remove(old_question.Images.path)
            except Question.DoesNotExist:
                pass
        # Проверяем размер изображения
        print(4)
        super(Question, self).save(*args, **kwargs)

    class Meta:
        db_table = 'questions'
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'

    def __str__(self):
        return self.text[0:50]

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.TextField('Текст ответа', max_length=150)
    is_correct = models.BooleanField('Правильный', default=False)

    class Meta:
        db_table = 'answers'
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'

    def __str__(self):
        return self.text




class Room(models.Model):

    STATE_CHOICES = (
        ('hub', 'Хаб'),
        ('active', 'Активная'),
        ('finished', 'Завершена'),
    )
    group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    token = models.CharField(max_length=16, unique=True, blank=True)
    key = models.CharField(max_length=6, unique=True, blank=True) 
    is_visible = models.BooleanField(default=False)
    state = models.CharField(max_length=10, choices=STATE_CHOICES, default='hub')
    Display_errors = models.BooleanField(verbose_name='Отображать ошибки',default=True) # Показывать ли errors
    
    t_start = models.DateTimeField('Время начала', )
    t_reg = models.DateTimeField('Время регистрации', )
    t_end = models.DateTimeField('Время окончания', )



    def save(self, *args, **kwargs):
        if not self.pk:  
            self.token = uuid.uuid4().hex[:16]
            self.key = uuid.uuid4().hex[:6]
        super(Room, self).save(*args, **kwargs)
    
    class Meta:
        db_table = 'rooms'
        verbose_name = 'Комната'
        verbose_name_plural = 'Комнаты'

    def __str__(self):
        return f'{self.quiz.title} - {self.token}'





class Result(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    score = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'results'
        verbose_name = 'Результат'
        verbose_name_plural = 'Результаты'

    def __str__(self):  
        return str(self.user)


class history(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    position = models.IntegerField()
    skore = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)

    def Meta(self):
        db_table = 'history'
        verbose_name = 'История'
        verbose_name_plural = 'История'
        ordering = ['-data']
        unique_together = ('user', 'room')


    def __str__(self):
        return str(self.user)