from rest_framework import serializers
from .models import Blog, Comment

class BlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = ['id', 'title', 'content', 'published_at', 'author']
        read_only_fields = ['id', 'published_at', 'author']

class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'comment', 'author', 'author_name', 'created_at']
        read_only_fields = ['author', 'created_at', 'author_name']

