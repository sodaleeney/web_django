from django.contrib.auth.models import User
from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    readers = models.ManyToManyField(User, related_name='read_books', blank=True)

    def __str__(self):
        return f"{self.title} by {self.author}"
