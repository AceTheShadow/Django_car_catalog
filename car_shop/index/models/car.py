from django.db import models
from .make import Make
from .model import Model
from .body_type import BodyType
from .color import Color
from .fuel_type import FuelType
from .gearbox_type import GearboxType
from django.contrib.auth.models import User


class Car(models.Model):
    make = models.ForeignKey(Make, on_delete=models.CASCADE, related_name="cars")
    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name="cars")
    body_type = models.ForeignKey(BodyType, on_delete=models.SET_NULL, null=True, related_name="cars")
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, related_name="cars")
    fuel_type = models.ForeignKey(FuelType, on_delete=models.SET_NULL, null=True, related_name="cars")
    gearbox_type = models.ForeignKey(GearboxType, on_delete=models.SET_NULL, null=True, related_name="cars")

    mileage = models.IntegerField()
    engine_capacity = models.DecimalField(max_digits=10, decimal_places=2)
    year = models.IntegerField()
    price = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cars")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.make.name} {self.model.name} ({self.year})"

    @property
    def primary_image(self):
        # Returns the primary Image or None
        return self.images.filter(is_primary=True).first()

