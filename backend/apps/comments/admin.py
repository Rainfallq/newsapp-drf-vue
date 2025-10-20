from django.contrib import admin
from django.utils.html import format_html
from .models import Comment

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'post_title', 'author', 'content_preview',
        'created_at', 'parent_comment', 'is_active'
        )
    list_filter = ('created_at', 'updated_at', 'is_active')
    search_fields = ('content', 'post__title', 'author__username')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('author', 'post', 'parent')
    list_editable = ('is_active',)
    
    fieldsets = (
        (None, {
            'fields': ('post', 'author', 'parent', 'content')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def post_title(self, obj):
        return obj.post.title if obj.post else 'No post'
    post_title.short_description = 'Post Title'

    def content_preview(self, obj):
        if not obj.content:
            return 'No content'
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'

    def parent_comment(self, obj):
        if obj.parent: 
            return f'reply to comment #{obj.parent.id}'
        return 'No parent'
    parent_comment.short_description = 'Parent Comment'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('post', 'author', 'parent')
    
    actions = ['activate_comments', 'deactivate_comments']

    def activate_comments(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} comments were marked as active.')
    activate_comments.short_description = 'Mark selected comments as active'

    def deactivate_comments(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} comments were marked as inactive.')
    deactivate_comments.short_description = 'Mark selected comments as inactive'