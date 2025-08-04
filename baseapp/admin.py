# baseapp/admin.py
from django.contrib import admin
from .models import Item

@admin.action(description='Mark selected items as Resolved')
def mark_as_resolved(modeladmin, request, queryset):
    queryset.update(is_resolved=True)

class ItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'item_type', 'location_name', 'created_at', 'is_resolved')
    list_filter = ('status', 'item_type', 'is_resolved', 'created_at')
    search_fields = ('title', 'description', 'location_name', 'user__username')
    list_editable = ('is_resolved',)
    actions = [mark_as_resolved]
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

admin.site.register(Item, ItemAdmin)