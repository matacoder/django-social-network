from django.contrib import admin

from .models import Comment, Follow, Group, Post


class PostAdmin(admin.ModelAdmin):
    list_display = ("pk", "text", "pub_date", "author", "group",)
    search_fields = ("text",)
    list_filter = ("pub_date",)
    empty_value_display = "-пусто-"


class GroupAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "slug", "description",)
    search_fields = ("title",)
    empty_value_display = "-пусто-"
    prepopulated_fields = {"slug": ("title",)}


class FollowAdmin(admin.ModelAdmin):
    list_display = ("user", "author",)
    search_fields = ("user",)
    empty_value_display = "-пусто-"


class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "author", "text", "created")
    search_fields = ("text",)
    empty_value_display = "-пусто-"


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(Comment, CommentAdmin)
