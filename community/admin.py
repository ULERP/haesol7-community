from django.contrib import admin
from hello_world.core.models import ManagementDocument

@admin.register(ManagementDocument)
class ManagementDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_active', 'updated_at']
    list_filter = ['category', 'is_active']
    search_fields = ['title', 'content']
    list_editable = ['is_active']
    list_display_links = ['title']
    
    verbose_name = '관리 문서'
    
    def get_queryset(self, request):
        return super().get_queryset(request)
