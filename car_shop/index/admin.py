from django.contrib import admin

from .models import (
    Make,
    Model,
    BodyType,
    Color,
    FuelType,
    GearboxType,
    Car,
    Image,
)


class ImageInline(admin.TabularInline):
    model = Image
    extra = 1  # how many empty forms to display
    fields = ("is_primary", "name")  # fields to show in the inline
    show_change_link = True


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ("id", "make", "model", "year", "price", "mileage", "owner")
    list_filter = ("make", "model", "year", "fuel_type", "gearbox_type", "body_type", "color")
    search_fields = ("description", "make__name", "model__name")
    inlines = [ImageInline]
    ordering = ("-year", "-created_at")

@admin.register(Make)
class MakeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at", "updated_at")
    search_fields = ("name",)


@admin.register(Model)
class ModelAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "make", "created_at", "updated_at")
    list_filter = ("make",)
    search_fields = ("name", "make__name")


@admin.register(BodyType)
class BodyTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at", "updated_at")
    search_fields = ("name",)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "hex_code", "created_at", "updated_at")
    search_fields = ("name", "hex_code")


@admin.register(FuelType)
class FuelTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at", "updated_at")
    search_fields = ("name",)


@admin.register(GearboxType)
class GearboxTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at", "updated_at")
    search_fields = ("name",)


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ("id", "car", "is_primary", "created_at")
    list_filter = ("is_primary", "car__make", "car__model")
    search_fields = ("name", "car__make__name", "car__model__name")


