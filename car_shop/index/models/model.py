from django.db import models
from .make import Make


class Model(models.Model):
    name = models.TextField()
    make = models.ForeignKey(Make, on_delete=models.CASCADE, related_name="models")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.make.name} {self.name}"
