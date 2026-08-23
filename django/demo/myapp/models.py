from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta, date
from decimal import Decimal


class Category(models.Model):
    """Subject classification following academic / Dewey-inspired taxonomies."""
    code = models.CharField(max_length=20, unique=True, help_text="Classification code (e.g. 004, QA, 823)")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['code', 'name']

    def __str__(self):
        return f"{self.code} — {self.name}"


class Book(models.Model):
    """Academic catalog item with inventory and classification metadata."""
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=30, blank=True, null=True, unique=True, help_text="ISBN-10 or ISBN-13")
    call_number = models.CharField(max_length=50, blank=True, null=True, help_text="Shelf call number (e.g. QA76.73 .P98)")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    publisher = models.CharField(max_length=150, blank=True)
    publication_year = models.PositiveIntegerField(null=True, blank=True)
    edition = models.CharField(max_length=50, blank=True)
    
    # Inventory Tracking
    quantity = models.PositiveIntegerField(default=1, help_text="Total physical copies in collection")
    available_copies = models.PositiveIntegerField(default=1, help_text="Available copies for circulation")
    shelf_location = models.CharField(max_length=100, blank=True, help_text="Stack / Shelf coordinate")
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title', 'author']

    def __str__(self):
        return f"{self.title} by {self.author}"

    def clean(self):
        if self.available_copies > self.quantity:
            raise ValidationError({'available_copies': 'Available copies cannot exceed total quantity.'})

    def save(self, *args, **kwargs):
        # On first creation, sync available_copies with quantity if default
        if self.pk is None and self.available_copies == 1 and self.quantity != 1:
            self.available_copies = self.quantity
        super().save(*args, **kwargs)

    @property
    def is_available(self):
        return self.available_copies > 0

    @property
    def borrowed_copies(self):
        return max(0, self.quantity - self.available_copies)


class Student(models.Model):
    """Library member/patron record with institutional role and borrowing privileges."""
    ROLE_CHOICES = [
        ('UNDERGRADUATE', 'Undergraduate Student'),
        ('POSTGRADUATE', 'Postgraduate Student'),
        ('FACULTY', 'Faculty / Professor'),
        ('RESEARCHER', 'Research Fellow'),
        ('STAFF', 'University Staff'),
    ]

    patron_id = models.CharField(max_length=30, unique=True, blank=True, null=True, help_text="Institutional Card ID")
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)
    department = models.CharField(max_length=100, default="General Studies")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='UNDERGRADUATE')
    max_borrow_limit = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.patron_id or self.email})"

    def save(self, *args, **kwargs):
        if not self.patron_id and not self.pk:
            # Generate temporary patron ID if none provided
            super().save(*args, **kwargs)
            self.patron_id = f"PAT-{timezone.now().year}-{self.pk:04d}"
            return super().save(update_fields=['patron_id'])
        super().save(*args, **kwargs)

    @property
    def active_loans_count(self):
        return self.loans.filter(return_date__isnull=True).count()

    @property
    def can_borrow(self):
        return self.is_active and (self.active_loans_count < self.max_borrow_limit)

    @property
    def total_fines_due(self):
        pending = self.fines.filter(status='PENDING')
        total = sum(f.remaining_amount for f in pending)
        return total


class IssueBook(models.Model):
    """Circulation loan record tracking checkout, due date, return, and renewals."""
    STATUS_CHOICES = [
        ('ACTIVE', 'Active Loan'),
        ('RETURNED', 'Returned'),
        ('OVERDUE', 'Overdue'),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='loans')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='loans')
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='issued_loans')
    issue_date = models.DateField(default=date.today)
    due_date = models.DateField(blank=True, null=True)
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ACTIVE')
    renewal_count = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-issue_date', '-id']

    def __str__(self):
        return f"{self.book.title} issued to {self.student.name}"

    def save(self, *args, **kwargs):
        # Normalize date instances
        if not self.issue_date:
            self.issue_date = date.today()
        elif hasattr(self.issue_date, 'date') and callable(getattr(self.issue_date, 'date')):
            self.issue_date = self.issue_date.date()

        if not self.due_date:
            self.due_date = self.issue_date + timedelta(days=14)
        elif hasattr(self.due_date, 'date') and callable(getattr(self.due_date, 'date')):
            self.due_date = self.due_date.date()
            
        if self.return_date and hasattr(self.return_date, 'date') and callable(getattr(self.return_date, 'date')):
            self.return_date = self.return_date.date()
        
        # Automatically update status if returned or overdue
        if self.return_date:
            self.status = 'RETURNED'
        elif self.due_date and date.today() > self.due_date:
            self.status = 'OVERDUE'
        else:
            self.status = 'ACTIVE'
            
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.return_date:
            return False
        target_due = self.due_date.date() if hasattr(self.due_date, 'date') and callable(getattr(self.due_date, 'date')) else self.due_date
        return target_due is not None and date.today() > target_due

    @property
    def overdue_days(self):
        if self.return_date:
            end_date = self.return_date.date() if hasattr(self.return_date, 'date') and callable(getattr(self.return_date, 'date')) else self.return_date
        else:
            end_date = date.today()
        
        target_due = self.due_date.date() if hasattr(self.due_date, 'date') and callable(getattr(self.due_date, 'date')) else self.due_date
        if target_due and end_date > target_due:
            return (end_date - target_due).days
        return 0

    @property
    def calculated_fine(self):
        daily_rate = Decimal('0.50')
        days = self.overdue_days
        return Decimal(days) * daily_rate


class FineLedger(models.Model):
    """Financial tracking of late return fines and administrative settlements."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending Settlement'),
        ('PAID', 'Settled / Paid'),
        ('WAIVED', 'Waived / Excused'),
    ]

    issue = models.ForeignKey(IssueBook, on_delete=models.CASCADE, related_name='fines')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fines')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    settled_at = models.DateTimeField(null=True, blank=True)
    settled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='settled_fines')
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Fine ${self.amount} for {self.student.name} ({self.status})"

    @property
    def remaining_amount(self):
        if self.status in ['PAID', 'WAIVED']:
            return Decimal('0.00')
        return max(Decimal('0.00'), self.amount - self.paid_amount)
