from django.contrib.admin import ModelAdmin, register, TabularInline, StackedInline,site
from django.db import models
from django.contrib.admin.widgets import AdminTextInputWidget, AdminTextareaWidget
from django import forms
# Register your models here.
from datetime import timedelta
from django.utils import timezone
from quiz.models import  Quiz, Question,Answer, Room

from django.utils.html import mark_safe






@register(Quiz)
class AccauntmodelAdmin(ModelAdmin):    
    prepopulated_fields = {"slug": ("title",)}



class answerInline(TabularInline):
    
    formfield_overrides = {
        models.TextField: {'widget': AdminTextInputWidget(attrs={'size':'70'})},
        models.TextField: {'widget': AdminTextareaWidget(attrs={'rows': 5})},
    }

    model = Answer
    min_num = 2
    extra = 0

@register(Question)
class AccauntmodelAdmin(ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': AdminTextInputWidget(attrs={'size':'70'})},
        models.TextField: {'widget': AdminTextareaWidget(attrs={'rows': 5})},
    }
    inlines = (
        answerInline,
    )
    list_display = ['quiz','text','tupe_question','time']
    readonly_fields = ('display_image',)

    def display_image(self, obj):
        if obj.Images:
            return mark_safe('<img src="{url}" width="{width}" height={height} />'.format(
                url=obj.Images.url,
                width=obj.Images.width,
                height=obj.Images.height,
            ))
        else:
            return "No Image"

    display_image.short_description = 'Изображение'

class RoomAdminForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Устанавливаем стандартные значения для полей t_start, t_reg и t_end
        self.fields['t_start'].initial = timezone.now()
        self.fields['t_reg'].initial = timezone.now() + timedelta(minutes=5)
        self.fields['t_end'].initial = timezone.now() + timedelta(minutes=20)


@register(Room)
class RoomAdmin(ModelAdmin):
    form = RoomAdminForm
    readonly_fields = ('token', 'key')