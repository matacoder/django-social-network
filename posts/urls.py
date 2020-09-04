from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("group/<slug:slug>/", views.group_posts, name="group_url"),
    path("new/", views.new_post, name="new_post"),
    path("404/", views.page_not_found, name="e404"),
    path("500/", views.server_error, name="e500"),
    path("<str:username>/", views.profile, name="profile"),
    path(
        "<str:username>/<int:post_id>/",
        views.post_view,
        name="post_single"
    ),
    path(
        "<str:username>/<int:post_id>/edit/",
        views.post_edit,
        name="post_edit"
    ),
    path(
        "<username>/<int:post_id>/comment",
        views.add_comment,
        name="add_comment"
    )
]
