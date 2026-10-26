from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import Allotment, Bed


@receiver(post_delete, sender=Allotment)
def release_bed_on_allotment_delete(sender, instance, **kwargs):
    """
    Ensure the bed is marked as AVAILABLE if an active allotment record is deleted.
    """
    if instance.bed:
        # Check if there are other active allotments for this bed
        has_active = Allotment.objects.filter(bed=instance.bed, is_active=True).exists()
        if not has_active:
            instance.bed.status = Bed.Status.AVAILABLE
            instance.bed.save(update_fields=['status'])
