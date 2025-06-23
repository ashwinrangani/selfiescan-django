from rest_framework import generics
from .models import Blog,Comment
from .serializers import BlogSerializer, CommentSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.shortcuts import render
from django.shortcuts import render, get_object_or_404

# blog apis
class BlogListCreateAPIView(generics.ListCreateAPIView):
    queryset = Blog.objects.all().order_by('-published_at')
    serializer_class = BlogSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class BlogRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

# comment apis
class CommentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        blog_id = self.kwargs['pk']
        return Comment.objects.filter(blog_id=blog_id).order_by('-created_at')

    def perform_create(self, serializer):
        blog_id = self.kwargs['pk']
        blog = get_object_or_404(Blog, pk=blog_id)
        serializer.save(author=self.request.user, blog=blog)


class CommentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

# blog views
def public_blog_list(request):
    blogs = Blog.objects.all().order_by('-published_at')
    return render(request, 'public_blog_list.html', {'blogs': blogs})

def public_blog_detail(request, pk):
    blog = get_object_or_404(Blog, pk=pk)
    comments = blog.comments.all().order_by('-created_at')  # related_name = 'comments'
    return render(request, 'public_blog_detail.html', {'blog': blog, 'comments': comments})

def blog_submit(request):
    blog_id = request.GET.get('edit')
    blog = None
    if blog_id:
        blog = get_object_or_404(Blog, pk=blog_id)
        if blog.author != request.user:
            blog = None  # Prevent editing others’ blogs

    return render(request, 'blog_submit.html', {'edit_blog': blog})

# comment view

def comment_edit(request):
    comment_id = request.GET.get('edit')
    comment = None
    if comment_id:
        comment = get_object_or_404(Comment, pk=comment_id)
        if comment.author != request.user:
            comment = None
    return render(request, 'comment_edit.html', {'comment': comment})
