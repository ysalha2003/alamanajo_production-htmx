from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg, Max, Min
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import datetime, timedelta, date
from urllib.parse import urlencode
import qrcode
import io
import base64
import requests
import json
import os
import statistics
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from .models import RepairJob, RepairJobPhoto
from .forms import DropOffForm, TrackingForm, AdminStatusUpdateForm

def is_htmx_request(request):
    """Helper function to check if request is from HTMX"""
    return request.headers.get('HX-Request') == 'true'

def get_date_range(filter_type, start_date=None, end_date=None):
    """Helper function to get date ranges for filtering"""
    today = timezone.now().date()
    
    if filter_type == 'today':
        return today, today
    elif filter_type == 'week':
        # Start of week (Monday)
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        return start, end
    elif filter_type == 'month':
        start = today.replace(day=1)
        # Last day of month
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1) - timedelta(days=1)
        else:
            end = start.replace(month=start.month + 1) - timedelta(days=1)
        return start, end
    elif filter_type == 'quarter':
        # Current quarter
        quarter = (today.month - 1) // 3 + 1
        start = today.replace(month=(quarter - 1) * 3 + 1, day=1)
        if quarter == 4:
            end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = today.replace(month=quarter * 3 + 1, day=1) - timedelta(days=1)
        return start, end
    elif filter_type == 'year':
        start = today.replace(month=1, day=1)
        end = today.replace(month=12, day=31)
        return start, end
    elif filter_type == 'custom' and start_date and end_date:
        return start_date, end_date
    else:
        # All time - return None to indicate no filtering
        return None, None

def custom_login(request):
    """Custom login view with same styling"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                
                # Redirect to next page or dashboard
                next_page = request.POST.get('next') or request.GET.get('next')
                if next_page:
                    return redirect(next_page)
                elif user.is_staff:
                    return redirect('dashboard')
                else:
                    return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AuthenticationForm()
    
    context = {
        'form': form,
        'redirect_field_name': 'next',
        'redirect_field_value': request.GET.get('next', ''),
    }
    return render(request, 'repairs/login.html', context)

def custom_logout(request):
    """Custom logout view that handles both GET and POST"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

def generate_qr_code(data):
    """Generate QR code and return as base64 string"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    qr_image = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    qr_image.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    return qr_code_base64

def home(request):
    """Home page"""
    return render(request, 'repairs/home.html', {
        'shop_name': settings.SHOP_NAME,
        'shop_address': settings.SHOP_ADDRESS,
        'shop_phone': settings.SHOP_PHONE,
        'shop_email': settings.SHOP_EMAIL,
    })

@login_required
def drop_off(request):
    """Customer drop-off form - requires login"""
    if request.method == 'POST':
        form = DropOffForm(request.POST)
        if form.is_valid():
            repair_job = form.save(commit=False)
            repair_job.created_by = request.user  # Track who created the job
            repair_job.save()
            
            # Handle multiple photo uploads directly from request.FILES
            photos = request.FILES.getlist('photos')
            for photo in photos:
                RepairJobPhoto.objects.create(
                    repair_job=repair_job,
                    photo=photo,
                    description=f"Drop-off photo - {photo.name}"
                )
            
            success_message = f'Drop-off recorded successfully! Job ID: {repair_job.job_id}'
            
            if is_htmx_request(request):
                # Return success message for HTMX
                messages.success(request, success_message)
                return render(request, 'repairs/partials/messages.html')
            else:
                messages.success(request, success_message)
                return redirect('receipt', job_id=repair_job.job_id)
        else:
            if is_htmx_request(request):
                # Return form errors for HTMX
                return render(request, 'repairs/partials/form_errors.html', {'form': form})
    else:
        form = DropOffForm()
    
    return render(request, 'repairs/drop_off.html', {'form': form})

@login_required
def receipt(request, job_id):
    """Display receipt with QR code that directly links to tracking with pre-filled data - Login Required"""
    repair_job = get_object_or_404(RepairJob, job_id=job_id)
    
    # Create direct tracking URL with pre-filled parameters
    tracking_params = {
        'job_id': repair_job.job_id,
        'phone': repair_job.phone_number
    }
    tracking_url = request.build_absolute_uri(
        reverse('track_repair') + '?' + urlencode(tracking_params)
    )
    
    # QR code now contains the direct tracking URL with parameters
    qr_code_base64 = generate_qr_code(tracking_url)
    
    context = {
        'repair_job': repair_job,
        'qr_code': qr_code_base64,
        'shop_name': settings.SHOP_NAME,
        'shop_address': settings.SHOP_ADDRESS,
        'shop_phone': settings.SHOP_PHONE,
        'shop_email': settings.SHOP_EMAIL,
        'tracking_url': tracking_url,
    }
    
    return render(request, 'repairs/receipt.html', context)

def track_repair(request):
    """Public tracking page with customer verification and QR code auto-lookup"""
    repair_job = None
    form = TrackingForm()
    auto_lookup = False
    
    # Check if we have URL parameters from QR code scan
    qr_job_id = request.GET.get('job_id')
    qr_phone = request.GET.get('phone')
    
    if qr_job_id and qr_phone:
        # Auto-lookup from QR code parameters
        try:
            repair_job = RepairJob.objects.get(job_id=qr_job_id.upper(), phone_number=qr_phone)
            auto_lookup = True
            # Pre-fill the form with QR code data
            form = TrackingForm(initial={'job_id': qr_job_id, 'phone_number': qr_phone})
        except RepairJob.DoesNotExist:
            messages.error(request, 'Invalid QR code or repair job not found. Please enter your details manually.')
    
    if request.method == 'POST':
        form = TrackingForm(request.POST)
        if form.is_valid():
            job_id = form.cleaned_data['job_id'].upper()
            phone_number = form.cleaned_data['phone_number']
            
            try:
                repair_job = RepairJob.objects.get(job_id=job_id, phone_number=phone_number)
                
                if is_htmx_request(request):
                    # Return the tracking result for HTMX
                    context = {
                        'repair_job': repair_job,
                        'auto_lookup': False,
                        'shop_name': settings.SHOP_NAME,
                        'shop_phone': settings.SHOP_PHONE,
                    }
                    return render(request, 'repairs/partials/tracking_result.html', context)
                    
            except RepairJob.DoesNotExist:
                messages.error(request, 'Job ID and phone number combination not found. Please check your details.')
                if is_htmx_request(request):
                    return render(request, 'repairs/partials/messages.html')
    
    context = {
        'form': form,
        'repair_job': repair_job,
        'auto_lookup': auto_lookup,
        'shop_name': settings.SHOP_NAME,
        'shop_phone': settings.SHOP_PHONE,
    }
    
    return render(request, 'repairs/track.html', context)

@staff_member_required
def dashboard(request):
    """Admin dashboard for managing repair jobs with sorting - Hide completed jobs by default"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    sort_by = request.GET.get('sort', '-created_at')  # Default sort by newest first
    show_completed = request.GET.get('show_completed', 'false')  # New parameter to show completed jobs
    
    jobs = RepairJob.objects.select_related('created_by').all()
    
    # Hide completed jobs by default unless specifically requested
    if show_completed.lower() != 'true':
        jobs = jobs.exclude(status='COMPLETED')
    
    if search_query:
        jobs = jobs.filter(
            Q(job_id__icontains=search_query) |
            Q(customer_name__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(created_by__username__icontains=search_query)
        )
    
    if status_filter:
        jobs = jobs.filter(status=status_filter)
    
    # Handle sorting with more options
    valid_sorts = [
        'created_at', '-created_at', 
        'job_id', '-job_id', 
        'customer_name', '-customer_name', 
        'status', '-status', 
        'estimated_repair_time', '-estimated_repair_time',
        'estimated_cost', '-estimated_cost',
        'created_by__username', '-created_by__username'
    ]
    if sort_by in valid_sorts:
        jobs = jobs.order_by(sort_by)
    else:
        jobs = jobs.order_by('-created_at')  # Default fallback
    
    paginator = Paginator(jobs, 20)  # Show 20 jobs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate stats based on whether completed jobs are shown
    if show_completed.lower() == 'true':
        total_jobs = RepairJob.objects.count()
        pending_jobs = RepairJob.objects.exclude(status='COMPLETED').count()
    else:
        total_jobs = RepairJob.objects.exclude(status='COMPLETED').count()
        pending_jobs = total_jobs
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'show_completed': show_completed,
        'status_choices': RepairJob.STATUS_CHOICES,
        'total_jobs': total_jobs,
        'pending_jobs': pending_jobs,
        'ready_jobs': RepairJob.objects.filter(status='READY').count(),
        'completed_jobs': RepairJob.objects.filter(status='COMPLETED').count(),
    }
    
    return render(request, 'repairs/dashboard.html', context)

@staff_member_required
def dashboard_content(request):
    """HTMX endpoint for dashboard content updates"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    sort_by = request.GET.get('sort', '-created_at')
    show_completed = request.GET.get('show_completed', 'false')
    
    jobs = RepairJob.objects.select_related('created_by').all()
    
    # Hide completed jobs by default unless specifically requested
    if show_completed.lower() != 'true':
        jobs = jobs.exclude(status='COMPLETED')
    
    if search_query:
        jobs = jobs.filter(
            Q(job_id__icontains=search_query) |
            Q(customer_name__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(created_by__username__icontains=search_query)
        )
    
    if status_filter:
        jobs = jobs.filter(status=status_filter)
    
    # Handle sorting
    valid_sorts = [
        'created_at', '-created_at', 
        'job_id', '-job_id', 
        'customer_name', '-customer_name', 
        'status', '-status', 
        'estimated_repair_time', '-estimated_repair_time',
        'estimated_cost', '-estimated_cost',
        'created_by__username', '-created_by__username'
    ]
    if sort_by in valid_sorts:
        jobs = jobs.order_by(sort_by)
    else:
        jobs = jobs.order_by('-created_at')
    
    paginator = Paginator(jobs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'show_completed': show_completed,
        'status_choices': RepairJob.STATUS_CHOICES,
    }
    
    return render(request, 'repairs/partials/jobs_table.html', context)

@staff_member_required
def dashboard_stats(request):
    """HTMX endpoint for dashboard stats updates"""
    show_completed = request.GET.get('show_completed', 'false')
    
    # Calculate stats based on whether completed jobs are shown
    if show_completed.lower() == 'true':
        total_jobs = RepairJob.objects.count()
        pending_jobs = RepairJob.objects.exclude(status='COMPLETED').count()
    else:
        total_jobs = RepairJob.objects.exclude(status='COMPLETED').count()
        pending_jobs = total_jobs
    
    context = {
        'total_jobs': total_jobs,
        'pending_jobs': pending_jobs,
        'ready_jobs': RepairJob.objects.filter(status='READY').count(),
        'completed_jobs': RepairJob.objects.filter(status='COMPLETED').count(),
    }
    
    return render(request, 'repairs/partials/stats_cards.html', context)

@staff_member_required
def job_detail(request, job_id):
    """Detailed view of a repair job with update form"""
    repair_job = get_object_or_404(RepairJob, job_id=job_id)
    
    if request.method == 'POST':
        # Pass request.FILES to the form
        form = AdminStatusUpdateForm(request.POST, request.FILES, instance=repair_job)
        if form.is_valid():
            form.save()
            
            # Handle additional photo uploads
            photos = request.FILES.getlist('additional_photos')
            photo_count = 0
            for photo in photos:
                RepairJobPhoto.objects.create(
                    repair_job=repair_job,
                    photo=photo,
                    description=f"Staff upload - {photo.name}"
                )
                photo_count += 1

            success_message = f'Job {job_id} updated successfully!'
            if photo_count > 0:
                success_message += f' Added {photo_count} new photo(s).'

            if is_htmx_request(request):
                # Return updated form and sidebar for HTMX
                messages.success(request, success_message)
                context = {
                    'repair_job': repair_job,
                    'form': AdminStatusUpdateForm(instance=repair_job),
                    'photos': repair_job.photos.all(),
                }
                # To refresh the whole detail page content, we can re-render the main template part
                return render(request, 'repairs/job_detail.html', context)
            else:
                messages.success(request, success_message)
                return redirect('job_detail', job_id=job_id)
        else:
            if is_htmx_request(request):
                # Return form with errors for HTMX
                context = {
                    'repair_job': repair_job,
                    'form': form,
                    'photos': repair_job.photos.all(),
                }
                return render(request, 'repairs/partials/job_update_form.html', context)
    else:
        form = AdminStatusUpdateForm(instance=repair_job)
    
    context = {
        'repair_job': repair_job,
        'form': form,
        'photos': repair_job.photos.all(),
    }
    
    return render(request, 'repairs/job_detail.html', context)

@staff_member_required
def job_quick_action(request, job_id):
    """HTMX endpoint for quick job actions"""
    repair_job = get_object_or_404(RepairJob, job_id=job_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'mark_ready':
            repair_job.status = 'READY'
            repair_job.save()
            messages.success(request, f'Job {job_id} marked as ready for pickup!')
            
        elif action == 'mark_completed':
            repair_job.status = 'COMPLETED'
            repair_job.save()
            messages.success(request, f'Job {job_id} marked as completed!')
        
        # We need to re-render the whole job detail view to update everything
        form = AdminStatusUpdateForm(instance=repair_job)
        context = {
            'repair_job': repair_job,
            'form': form,
            'photos': repair_job.photos.all(),
        }
        return render(request, 'repairs/job_detail.html', context)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@staff_member_required
def job_delete_confirm(request, job_id):
    """HTMX endpoint for job deletion confirmation modal"""
    repair_job = get_object_or_404(RepairJob, job_id=job_id)
    photo_count = repair_job.photos.count()
    
    context = {
        'repair_job': repair_job,
        'photo_count': photo_count,
    }
    
    return render(request, 'repairs/partials/delete_confirmation_modal.html', context)

@staff_member_required
@require_http_methods(["DELETE"])
def job_delete(request, job_id):
    """Delete a repair job and all associated data"""
    repair_job = get_object_or_404(RepairJob, job_id=job_id)
    
    try:
        # Store info for success message
        customer_name = repair_job.customer_name
        photo_count = repair_job.photos.count()
        
        # Get all photo files for deletion
        photo_files = []
        for photo in repair_job.photos.all():
            if photo.photo and os.path.exists(photo.photo.path):
                photo_files.append(photo.photo.path)
        
        # Delete the repair job (this will cascade delete photos due to ForeignKey)
        repair_job.delete()
        
        # Delete physical photo files
        deleted_files = 0
        for file_path in photo_files:
            try:
                os.remove(file_path)
                deleted_files += 1
            except OSError:
                pass  # File might already be deleted or inaccessible
        
        # Create success message
        success_message = f'Job {job_id} ({customer_name}) has been permanently deleted.'
        if photo_count > 0:
            success_message += f' Removed {photo_count} photo(s) and {deleted_files} file(s).'
        
        messages.success(request, success_message)
        
        # For HTMX request, redirect to dashboard
        if is_htmx_request(request):
            response = HttpResponse()
            response['HX-Redirect'] = reverse('dashboard')
            return response
        else:
            return redirect('dashboard')
            
    except Exception as e:
        error_message = f'Error deleting job {job_id}: {str(e)}'
        messages.error(request, error_message)
        
        if is_htmx_request(request):
            response = HttpResponse()
            response['HX-Redirect'] = reverse('job_detail', kwargs={'job_id': job_id})
            return response
        else:
            return redirect('job_detail', job_id=job_id)

@staff_member_required
def total_summary(request):
    """Enhanced total summary page with date filtering"""
    filter_type = request.GET.get('filter', 'all')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    # Parse custom dates if provided
    start_date = None
    end_date = None
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Get date range based on filter type
    filter_start, filter_end = get_date_range(filter_type, start_date, end_date)
    
    # Set default dates for display
    if filter_start and filter_end:
        start_date = filter_start
        end_date = filter_end
    elif not start_date or not end_date:
        # Default to this month if no dates specified
        today = timezone.now().date()
        start_date = today.replace(day=1)
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1) - timedelta(days=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1) - timedelta(days=1)
        if filter_type == 'all':
            filter_type = 'month'
    
    context = {
        'filter_type': filter_type,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'repairs/total_summary.html', context)

@staff_member_required
def total_summary_filtered(request):
    """HTMX endpoint for filtered summary data"""
    filter_type = request.GET.get('filter', 'all')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    # Parse custom dates if provided
    start_date = None
    end_date = None
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Get date range based on filter type
    filter_start, filter_end = get_date_range(filter_type, start_date, end_date)
    
    # Base queryset
    jobs = RepairJob.objects.all()
    
    # Apply date filtering
    if filter_start and filter_end:
        jobs = jobs.filter(created_at__date__gte=filter_start, created_at__date__lte=filter_end)
    
    # Calculate totals
    jobs_with_cost = jobs.filter(estimated_cost__isnull=False)
    total_cost = jobs_with_cost.aggregate(Sum('estimated_cost'))['estimated_cost__sum'] or 0
    jobs_with_cost_count = jobs_with_cost.count()
    total_jobs_count = jobs.count()
    
    # Calculate average cost
    average_cost = jobs_with_cost.aggregate(Avg('estimated_cost'))['estimated_cost__avg'] or 0
    
    # Daily breakdown for shorter periods
    daily_breakdown = None
    if filter_start and filter_end and (filter_end - filter_start).days <= 31:
        daily_data = jobs.filter(estimated_cost__isnull=False).extra({
            'date': 'DATE(created_at)'
        }).values('date').annotate(
            total=Sum('estimated_cost'),
            count=Count('id')
        ).order_by('date')
        
        daily_breakdown = []
        for item in daily_data:
            daily_breakdown.append({
                'date': datetime.strptime(item['date'], '%Y-%m-%d').date(),
                'total': item['total'],
                'count': item['count']
            })
    
    # High-value jobs (€100+) in the period
    high_value_jobs = jobs.filter(
        estimated_cost__gte=100
    ).order_by('-estimated_cost')[:10]
    
    # Additional statistics
    cost_values = list(jobs_with_cost.values_list('estimated_cost', flat=True))
    highest_job_cost = max(cost_values) if cost_values else 0
    lowest_job_cost = min(cost_values) if cost_values else 0
    median_cost = statistics.median(cost_values) if cost_values else 0
    
    context = {
        'filter_type': filter_type,
        'start_date': filter_start or start_date,
        'end_date': filter_end or end_date,
        'total_cost': total_cost,
        'jobs_with_cost_count': jobs_with_cost_count,
        'total_jobs_count': total_jobs_count,
        'average_cost': average_cost,
        'daily_breakdown': daily_breakdown,
        'high_value_jobs': high_value_jobs,
        'highest_job_cost': highest_job_cost,
        'lowest_job_cost': lowest_job_cost,
        'median_cost': median_cost,
    }
    
    return render(request, 'repairs/partials/summary_content.html', context)

def send_sms_notification(phone_number, message):
    """Send SMS using sms-gate.app"""
    if not settings.SMS_GATEWAY_USERNAME or not settings.SMS_GATEWAY_PASSWORD:
        return False, "SMS credentials not configured"
    
    headers = {'Content-Type': 'application/json'}
    data = {'message': message, 'phoneNumbers': [phone_number]}
    
    try:
        response = requests.post(
            settings.SMS_GATEWAY_URL,
            headers=headers,
            auth=(settings.SMS_GATEWAY_USERNAME, settings.SMS_GATEWAY_PASSWORD),
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return True, "SMS sent successfully"
        else:
            return False, f"SMS failed: {response.status_code}"
            
    except Exception as e:
        return False, f"SMS error: {str(e)}"
