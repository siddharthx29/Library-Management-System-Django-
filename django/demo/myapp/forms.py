import re
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from myapp.models import Book, Student, IssueBook, FineLedger, Category


class BookForm(forms.ModelForm):
    """Secure, validated form for creating and updating catalog items."""
    
    class Meta:
        model = Book
        fields = [
            'title', 'author', 'isbn', 'call_number', 'category',
            'publisher', 'publication_year', 'edition',
            'quantity', 'available_copies', 'shelf_location', 'description'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Introduction to Algorithms'}),
            'author': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Thomas H. Cormen, Charles E. Leiserson'}),
            'isbn': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 978-0262033848'}),
            'call_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. QA76.6 .C662 2009'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'publisher': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. MIT Press'}),
            'publication_year': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 2022', 'min': 1400, 'max': 2030}),
            'edition': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 4th Edition'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'available_copies': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'shelf_location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Stacks 4B, Shelf 12'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'Scholarly overview, table of contents summary...'}),
        }

    def clean_title(self):
        title = (self.cleaned_data.get('title') or '').strip()
        if not title:
            raise ValidationError("Title is mandatory.")
        return title

    def clean_author(self):
        author = (self.cleaned_data.get('author') or '').strip()
        if not author:
            raise ValidationError("Author name is mandatory.")
        return author

    def clean_isbn(self):
        isbn = (self.cleaned_data.get('isbn') or '').strip()
        if not isbn:
            return None
        # Remove hyphens and spaces
        cleaned_isbn = re.sub(r'[\s\-]', '', isbn)
        if len(cleaned_isbn) not in [10, 13]:
            raise ValidationError("ISBN must be 10 or 13 digits (hyphens are optional).")
        
        # Check uniqueness excluding self
        existing = Book.objects.filter(isbn=cleaned_isbn)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise ValidationError(f"A book with ISBN '{isbn}' is already registered in the catalog.")
        return cleaned_isbn

    def clean_publication_year(self):
        year = self.cleaned_data.get('publication_year')
        current_year = timezone.now().year
        if year is not None:
            if year < 1000 or year > current_year + 2:
                raise ValidationError(f"Publication year must be between 1000 and {current_year + 2}.")
        return year

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity') or 1
        available = cleaned_data.get('available_copies')
        
        if available is None:
            cleaned_data['available_copies'] = quantity
        elif available > quantity:
            self.add_error('available_copies', 'Available copies cannot exceed total inventory quantity.')
        return cleaned_data


class StudentForm(forms.ModelForm):
    """Secure form for registering and updating library patrons / students."""
    
    class Meta:
        model = Student
        fields = [
            'patron_id', 'name', 'email', 'phone',
            'department', 'role', 'max_borrow_limit', 'is_active'
        ]
        widgets = {
            'patron_id': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. PAT-2026-0812'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Dr. Eleanor Vance'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'e.g. e.vance@university.edu'}),
            'phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. +1 (555) 234-5678'}),
            'department': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Dept of Computer Science'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'max_borrow_limit': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 25}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if len(name) < 2:
            raise ValidationError("Please provide a valid full name.")
        return name

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        existing = Student.objects.filter(email=email)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise ValidationError("A patron with this institutional email is already registered.")
        return email

    def clean_patron_id(self):
        patron_id = (self.cleaned_data.get('patron_id') or '').strip()
        if not patron_id:
            return None
        existing = Student.objects.filter(patron_id=patron_id)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise ValidationError("A patron with this ID already exists.")
        return patron_id


class CirculationIssueForm(forms.Form):
    """Circulation desk form to issue an item."""
    book = forms.ModelChoiceField(
        queryset=Book.objects.filter(available_copies__gt=0).order_by('title'),
        widget=forms.Select(attrs={'class': 'form-select select2-enable'}),
        empty_label="-- Select Available Catalog Title --"
    )
    student = forms.ModelChoiceField(
        queryset=Student.objects.filter(is_active=True).order_by('name'),
        widget=forms.Select(attrs={'class': 'form-select select2-enable'}),
        empty_label="-- Select Registered Patron --"
    )
    loan_period_days = forms.IntegerField(
        initial=14,
        min_value=1,
        max_value=90,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 90})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-textarea', 'rows': 2, 'placeholder': 'Optional desk notes, special course reserve note...'})
    )


class ReturnBookForm(forms.Form):
    """Form for processing returns with custom dates or settlement notes."""
    return_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-textarea', 'rows': 2, 'placeholder': 'Condition upon return, notes...'})
    )


class FineSettlementForm(forms.Form):
    """Form to process fine payments or administrative waivers."""
    ACTION_CHOICES = [
        ('PAID', 'Settle / Record Payment'),
        ('WAIVED', 'Waive Fine (Dean/Librarian Exception)'),
    ]
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    payment_amount = forms.DecimalField(
        min_value=Decimal('0.01'),
        max_digits=8,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Receipt #, authorization reason...'})
    )
