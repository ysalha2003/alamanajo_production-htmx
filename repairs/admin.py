from django.contrib import admin
from django.contrib import messages
from django.utils import timezone
from django.utils.html import format_html
from .models import RepairJob, RepairJobPhoto
from .views import send_sms_notification

class RepairJobPhotoInline(admin.TabularInline):
    model = RepairJobPhoto
    extra = 0
    readonly_fields = ['uploaded_at', 'photo_preview']
    fields = ['photo', 'photo_preview', 'description', 'uploaded_at']
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px; object-fit: cover;" />',
                obj.photo.url
            )
        return "No photo"
    photo_preview.short_description = "Preview"

@admin.register(RepairJob)
class RepairJobAdmin(admin.ModelAdmin):
    list_display = ['job_id', 'customer_name', 'phone_number', 'status', 'estimated_repair_time', 'created_at', 'created_by', 'ready_notified_at', 'photo_count']
    list_filter = ['status', 'estimated_repair_time', 'created_at', 'created_by']
    search_fields = ['job_id', 'customer_name', 'phone_number', 'created_by__username']
    readonly_fields = ['job_id', 'created_at', 'updated_at', 'ready_notified_at']
    inlines = [RepairJobPhotoInline]
    
    fieldsets = (
        ('Job Information', {
            'fields': ('job_id', 'created_at', 'updated_at', 'created_by')
        }),
        ('Customer Details', {
            'fields': ('customer_name', 'phone_number', 'bike_description')
        }),
        ('Repair Status', {
            'fields': ('status', 'estimated_repair_time', 'repair_details', 'estimated_cost', 'internal_notes')
        }),
        ('Notifications', {
            'fields': ('ready_notified_at',)
        }),
    )
    
    actions = ['send_ready_notification', 'mark_completed']
    
    def photo_count(self, obj):
        count = obj.photos.count()
        if count > 0:
            return format_html(
                '<span style="color: #059669;"><i class="fas fa-camera"></i> {}</span>',
                count
            )
        return "-"
    photo_count.short_description = "Photos"
    
    def send_ready_notification(self, request, queryset):
        """Send SMS notification that bike is ready"""
        success_count = 0
        
        for job in queryset:
            if job.status == 'READY':
                message = f"""🚴 Alamana Jo - Your e-bike is ready!

Job ID: {job.job_id}
Customer: {job.customer_name}

Your e-bike repair is complete and ready for pickup.

📍 Quellinstraat 45, 2018 Antwerpen
📞 +32 (499) 89-0237
⏰ Hours: Fri-Wed 11:00-19:00, Thu: Closed

IMPORTANT: After 14 days, €2/day storage fee applies.
Please call ahead to arrange pickup.

Thank you for choosing Alamana Jo!"""
                
                success, error_msg = send_sms_notification(job.phone_number, message)
                if success:
                    success_count += 1
                    job.ready_notified_at = timezone.now()
                    job.save()
                    messages.success(request, f"SMS sent to {job.customer_name}")
        
        if success_count > 0:
            messages.success(request, f"Successfully sent {success_count} notifications")
    
    send_ready_notification.short_description = "📱 Send 'Ready for Pickup' SMS"
    
    def mark_completed(self, request, queryset):
        """Mark jobs as completed"""
        updated = queryset.update(status='COMPLETED')
        messages.success(request, f"Marked {updated} jobs as completed")
    
    mark_completed.short_description = "✅ Mark as Completed"

@admin.register(RepairJobPhoto)
class RepairJobPhotoAdmin(admin.ModelAdmin):
    list_display = ['repair_job', 'photo_preview', 'description', 'uploaded_at']
    list_filter = ['uploaded_at', 'repair_job__status']
    search_fields = ['repair_job__job_id', 'repair_job__customer_name', 'description']
    readonly_fields = ['uploaded_at', 'photo_preview']
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 150px; object-fit: cover;" />',
                obj.photo.url
            )
        return "No photo"
    photo_preview.short_description = "Photo Preview"
