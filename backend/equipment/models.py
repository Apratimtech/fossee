from django.db import models
import json


class EquipmentUpload(models.Model):
    """Stores metadata and summary for each CSV upload. Keep last 5 only."""
    filename = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    summary = models.JSONField(default=dict)   # total_count, averages, type_distribution
    data = models.JSONField(default=list)     # list of row dicts for table/charts

    class Meta:
        ordering = ['-created_at']

    @classmethod
    def keep_last_n(cls, n=5):
        qs = cls.objects.order_by('-created_at')
        for obj in qs[n:]:
            obj.delete()
