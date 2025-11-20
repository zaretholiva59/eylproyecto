from django.contrib import admin
from .models import Task, WorkLog

# Register your models here.
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'assigned_to', 'status', 'units_completed', 'units_planned']
    list_filter = ['status', 'project']
    search_fields = ['title', 'project__name']
    date_hierarchy = 'planned_start'

@admin.register(WorkLog)
class WorkLogAdmin(admin.ModelAdmin):
    list_display = ['worker', 'task', 'date', 'units_completed', 'status']
    list_filter = ['status', 'date', 'worker']
    search_fields = ['worker__username', 'task__title']
    readonly_fields = ['created_at', 'updated_at']