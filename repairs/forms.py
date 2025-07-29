from django import forms
from .models import RepairJob, RepairJobPhoto

class DropOffForm(forms.ModelForm):
    class Meta:
        model = RepairJob
        fields = ['customer_name', 'phone_number', 'bike_description', 'estimated_repair_time']
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent',
                'placeholder': 'Enter your full name',
                'required': True
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent',
                'placeholder': '+32 499 12 34 56',
                'required': True,
                'type': 'tel'
            }),
            'bike_description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent',
                'placeholder': 'Brand, model, color, issues you\'ve noticed...',
                'rows': 4
            }),
            'estimated_repair_time': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent'
            }),
        }
        labels = {
            'customer_name': 'Customer Name *',
            'phone_number': 'Phone Number *',
            'bike_description': 'Bike Description (Optional)',
            'estimated_repair_time': 'Estimated Repair Time',
        }

class TrackingForm(forms.Form):
    job_id = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent',
            'placeholder': 'AJ-1001',
            'required': True
        }),
        label='Job ID *'
    )
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent',
            'placeholder': '+32 499 12 34 56',
            'required': True,
            'type': 'tel'
        }),
        label='Phone Number *'
    )

class AdminStatusUpdateForm(forms.ModelForm):
    # The 'additional_photos' field has been REMOVED from this form.
    # File uploads will be handled manually in the view and template.
    class Meta:
        model = RepairJob
        fields = ['status', 'estimated_repair_time', 'estimated_cost', 'repair_details', 'internal_notes']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500'
            }),
            'estimated_repair_time': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500'
            }),
            'estimated_cost': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'step': '0.01'
            }),
            'repair_details': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'rows': 3
            }),
            'internal_notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'rows': 2
            }),
        }
