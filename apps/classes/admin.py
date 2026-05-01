from django.contrib import admin
from .models import Assignment, Class, Enrollment

# Register your models here.

admin.site.register(Class)
admin.site.register(Enrollment)
admin.site.register(Assignment)