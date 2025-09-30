from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from .car import Car
import os
import uuid
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image as PILImage
from django.db.models import Q


# ... existing code ...


def image_upload_to(instance, filename):
    """
    Side-effect-free path generator for the original image.
    """
    base_dir = "cars"
    ext = os.path.splitext(filename)[1].lower() or ".jpg"
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"]:
        ext = ".jpg"
    # Use UUID to avoid collisions
    return f"{base_dir}/{uuid.uuid4().hex}{ext}"


class Image(models.Model):
    name = models.ImageField(upload_to=image_upload_to, blank=True, null=True)
    car = models.ForeignKey('index.Car', on_delete=models.CASCADE, related_name='images')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image of {self.car} ({'Primary' if self.is_primary else 'Secondary'})"

    def _thumbnail_storage_path(self):
        """
        Compute storage path for the thumbnail, derived from self.name.
        Example: cars/thumbnails/<basename>_thumb.jpg
        """
        if not self.name:
            return None
        base, _ext = os.path.splitext(self.name.name)  # e.g., cars/abc123.png -> cars/abc123
        base_name = os.path.basename(base)  # abc123
        return f"cars/thumbnails/{base_name}_thumb.jpg"

    @property
    def thumbnail_url(self):
        """
        Public URL for the thumbnail (whether it exists or not).
        You can check existence with default_storage.exists(self._thumbnail_storage_path()) if needed.
        """
        thumb_path = self._thumbnail_storage_path()
        if not thumb_path:
            return None
        # If using default FileSystemStorage, MEDIA_URL + path is fine.
        return f"{settings.MEDIA_URL.rstrip('/')}/{thumb_path}"

    def _ensure_thumbnail(self, max_size=(400, 400)):
        """
        Generate and save a thumbnail file in storage without touching the database.
        Safe to call multiple times; it skips work if thumbnail already exists.
        """
        if not self.name:
            return
        thumb_path = self._thumbnail_storage_path()
        if not thumb_path:
            return
        if default_storage.exists(thumb_path):
            return  # already generated

        self._save_and_resize_image(max_size, thumb_path)

    def _save_and_resize_image(self, max_size, image_path):
        # Open original from storage
        with default_storage.open(self.name.name, "rb") as f:
            with PILImage.open(f) as im:
                # Convert to a mode safe for JPEG
                if im.mode not in ("RGB", "L"):
                    im = im.convert("RGB")
                im.thumbnail(max_size, resample=PILImage.Resampling.LANCZOS)

                buffer = BytesIO()
                im.save(buffer, format="JPEG", quality=85, optimize=True)
                buffer.seek(0)

                # Save image file to storage
                default_storage.save(image_path, ContentFile(buffer.read()))

    def _resize_original_before_save(self, max_size=(1200, 1200), quality=85):
        """
        Resize the original upload in-memory and replace the field's file.
        Keeps aspect ratio using thumbnail(). Converts to RGB if needed.
        Set force_format to None to try preserving the original format.
        """
        if not self.name or not hasattr(self.name, "file"):
            return

        try:
            # Open from the in-memory/temporary uploaded file
            self.name.file.seek(0)
            with PILImage.open(self.name.file) as im:
                # Convert to safe mode
                if im.mode not in ("RGB", "L"):
                    im = im.convert("RGB")

                # Resize in-place while keeping aspect ratio
                im.thumbnail(max_size, resample=PILImage.Resampling.LANCZOS)

                # Build a filename with the right extension (upload_to will already have generated a name;
                # we only adjust the extension if necessary)
                base_no_ext = os.path.splitext(self.name.name)[0] if getattr(self.name, "name", None) else "image"
                new_name = f"{base_no_ext}{".jpg"}"
                if default_storage.exists(os.path.basename(new_name)):
                    return

                # Encode into memory
                buffer = BytesIO()
                save_kwargs = {"format": "JPEG", "quality": quality, "optimize": True}
                im.save(buffer, **save_kwargs)
                buffer.seek(0)

                # Replace the field's file with an in-memory file (no DB write yet)
                in_mem = InMemoryUploadedFile(
                    buffer,
                    field_name="name",
                    name=os.path.basename(new_name),
                    content_type="image/jpeg",
                    size=buffer.getbuffer().nbytes,
                    charset=None,
                )
                self.name = in_mem
        except Exception:
            # Optional: log the error and proceed without resizing
            # import logging; logging.getLogger(__name__).exception("Resize failed")
            pass

    def save(self, *args, **kwargs):
        # Resize the original image before it’s written to storage
        if self.name and not getattr(self, "_original_resized", False):
            self._resize_original_before_save(max_size=(1200, 1200), quality=85)
            # Avoid repeated resizing on subsequent saves
            setattr(self, "_original_resized", True)
        if self.is_primary and self.car_id:
            Image.objects.filter(car_id=self.car_id, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

        try:
            self._ensure_thumbnail()
        except Exception:
            # Optional: log this instead of raising to avoid breaking admin creates
            # import logging; logging.getLogger(__name__).exception("Thumbnail generation failed")
            pass

    class Meta:
        # DB-level guard to prevent multiple primaries per car
        constraints = [
            models.UniqueConstraint(
                fields=['car'],
                condition=Q(is_primary=True),
                name='unique_primary_image_per_car'
            )
        ]


