"""
Django forms for the shopperz application.

This module contains form classes for handling user inputs related to product
reviews and other e-commerce operations.
"""
from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    """
    A ModelForm for creating and editing product reviews.

    This form handles the submission of customer reviews including ratings and
    content.
    It automatically integrates with the Review model and provides customized
    widgets for an improved user experience.
    """

    class Meta:
        """
        Metadata configuration for the ReviewForm.

        Attributes:
            model: The Review model this form is based on.
            fields: The model fields to include in the form
                (rating and content).
            widgets: Custom widgets for form fields to enhance user interface.
        """
        model = Review
        fields = ['rating', 'content']
        widgets = {
            'rating': forms.Select(choices=[(i, str(i)) for i in range(1, 6)]),
            'content': forms.Textarea(
                attrs={'rows': 4, 'placeholder': 'Write your review here...'}
            ),
        }
