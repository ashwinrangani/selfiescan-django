from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Blog(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    published_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blogs')

    def __str__(self):
        return self.title

class Comment(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='comments')  # better field name
    comment = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')  # use plural
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # auto_now=True for updated_at

    def __str__(self):
        return f"Comment by {self.author.username} on {self.blog.title}"
