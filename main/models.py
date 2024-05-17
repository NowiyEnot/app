from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, Group
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save

import uuid
import os

class StudentGroup(models.Model):
    name = models.CharField('Название',max_length=20)
    slug = models.SlugField('Url',max_length=20, unique=True)

    class Meta:
        db_table = 'student_groups'
        verbose_name = 'студентская группа'
        verbose_name_plural = 'студентские группы'


    def __str__(self):
        return f'{self.name}'




class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email):
        return self.get(email=email)


class MyUser(AbstractBaseUser):
    avatar = models.ImageField('Аватар', upload_to='avatars/', null=True, blank=True, default='avatars/user-favicon.svg')
    first_name = models.CharField(verbose_name='Имя',max_length=30)
    last_name = models.CharField(verbose_name='Фамилия',max_length=30)
    surname = models.CharField(verbose_name='Отчество',max_length=30,default='', blank=True)
    email = models.EmailField(verbose_name='Электронная почта',unique=True)
    course = models.IntegerField(verbose_name='Курс',default=1)
    group = models.ForeignKey(verbose_name='Группа',to=StudentGroup, on_delete=models.CASCADE, related_name='users', null=True)
    registration_date = models.DateTimeField(verbose_name='Дата регистрации', auto_now_add=True)

    can_create = models.BooleanField(verbose_name='Может создавать',default=True)
    is_active = models.BooleanField(verbose_name='Активирован',default=True)
    is_staff = models.BooleanField(verbose_name='Администратор', default=False)

    
    objects = MyUserManager()

    USERNAME_FIELD = 'email'  # Поле, по которому будет осуществляться аутентификация
    REQUIRED_FIELDS = ['first_name', 'last_name', 'course','group'] # Список полей, которые необходимо заполнить при создании пользователя

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    def get_full_name(self):
        # Объединяем поля имени, фамилии и отчества для формирования полного имени
        full_name = f"{self.last_name} {self.first_name}"
        if self.surname:
            full_name += f" {self.surname}"
            print(full_name)
        return full_name
    def save(self, *args, **kwargs):
        # Проверяем, есть ли у пользователя аватар и он не равен значению по умолчанию
        if self.pk:
            try:
                old_user = MyUser.objects.get(pk=self.pk)
                if self.avatar and old_user.avatar.name != self.avatar.name:
                    # Удаляем предыдущий аватар
                    if os.path.exists(old_user.avatar.path):
                        os.remove(old_user.avatar.path)
            except MyUser.DoesNotExist:
                pass
        super(MyUser, self).save(*args, **kwargs)
    def Meta(self):
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-registration_date'] # Сортировка по дате регистрации
        
    
    def __str__(self):
        return f'{self.email} {self.last_name} {self.first_name}'
    


class UserUUID(models.Model):
    UUID = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE, related_name='UUID')

    def Meta(self):
        db_table = 'user_uuid'
        verbose_name = 'Уникальный идентификатор пользователя'
        verbose_name_plural = 'Уникальные идентификаторы пользователей'

    def __str__(self):
        return str(self.UUID)


@receiver(post_save, sender=MyUser)
def create_UserUUID(sender, instance, created, **kwargs):
    if created:
        UserUUID.objects.create(user=instance)
