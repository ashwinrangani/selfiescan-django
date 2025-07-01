from django.urls import path
from .views import BlogListCreateAPIView, BlogRetrieveUpdateDestroyAPIView, public_blog_list, public_blog_detail, blog_submit, CommentListCreateAPIView, CommentRetrieveUpdateDestroyAPIView

urlpatterns = [
    # Public template views
    path('blog/', public_blog_list, name='public-blog-list'),
    path('blog/<int:pk>/', public_blog_detail, name='public-blog-detail'),

    # API endpoints
    path('api/blogs/', BlogListCreateAPIView.as_view(), name='api-blog-list'),
    path('api/blogs/<int:pk>/', BlogRetrieveUpdateDestroyAPIView.as_view(), name='api-blog-detail'),
    path('blog/submit/', blog_submit, name='blog-submit'),
    path('api/blogs/<int:pk>/comments/', CommentListCreateAPIView.as_view(), name='blog-comments'),
    path('api/comments/<int:pk>/', CommentRetrieveUpdateDestroyAPIView.as_view(), name='comment-detail'),

]
