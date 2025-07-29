from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import uuid
import os

def repair_photo_upload_path(instance, filename):
    """Generate upload path for repair photos"""
    return f'repair_photos/{instance.repair_job.job_id}/{filename}'

class RepairJob(models.Model):
    STATUS_CHOICES = [
        ('RECEIVED', 'Received'),
        ('DIAGNOSED', 'Diagnosed'),
        ('IN_PROGRESS', 'In Progress'),
        ('WAITING_PARTS', 'Waiting for Parts'),
        ('READY', 'Ready for Pickup'),
        ('COMPLETED', 'Completed'),
    ]
    
    ESTIMATED_TIME_CHOICES = [
        ('TODAY', 'Today'),
        ('1-2_DAYS', '1-2 Days'),
        ('3-5_DAYS', '3-5 Days'),
        ('1_WEEK', '1 Week'),
        ('2_WEEKS', '2 Weeks'),
        ('3_WEEKS', '3 Weeks'),
        ('1_MONTH', '1 Month'),
        ('UNKNOWN', 'To Be Determined'),
    ]
    
    job_id = models.CharField(max_length=20, unique=True, blank=True)
    customer_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    bike_description = models.TextField(blank=True, help_text="Optional bike description")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RECEIVED')
    estimated_repair_time = models.CharField(max_length=20, choices=ESTIMATED_TIME_CHOICES, default='UNKNOWN', help_text="Estimated repair completion time")
    internal_notes = models.TextField(blank=True, help_text="Internal staff notes")
    repair_details = models.TextField(blank=True, help_text="What was repaired/fixed")
    estimated_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, help_text="User who created this job")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ready_notified_at = models.DateTimeField(null=True, blank=True, help_text="When ready SMS was sent")
    
    def save(self, *args, **kwargs):
        if not self.job_id:
            last_job = RepairJob.objects.order_by('-id').first()
            if last_job:
                last_number = int(last_job.job_id.split('-')[1])
                new_number = last_number + 1
            else:
                new_number = 1001
            self.job_id = f"AJ-{new_number}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.job_id} - {self.customer_name}"
    
    def get_status_display_color(self):
        status_colors = {
            'RECEIVED': 'bg-blue-100 text-blue-800',
            'DIAGNOSED': 'bg-yellow-100 text-yellow-800',
            'IN_PROGRESS': 'bg-orange-100 text-orange-800',
            'WAITING_PARTS': 'bg-purple-100 text-purple-800',
            'READY': 'bg-green-100 text-green-800',
            'COMPLETED': 'bg-gray-100 text-gray-800',
        }
        return status_colors.get(self.status, 'bg-gray-100 text-gray-800')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Repair Job"
        verbose_name_plural = "Repair Jobs"

class RepairJobPhoto(models.Model):
    """Photos attached to repair jobs"""
    repair_job = models.ForeignKey(RepairJob, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to=repair_photo_upload_path)
    description = models.CharField(max_length=200, blank=True, help_text="Optional photo description")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Photo for {self.repair_job.job_id}"
    
    class Meta:
        ordering = ['uploaded_at']
