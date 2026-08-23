import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from datetime import date

from myapp.models import Book, Student, IssueBook, FineLedger, Category
from myapp.forms import BookForm, StudentForm, CirculationIssueForm, ReturnBookForm, FineSettlementForm
from myapp.services.circulation_service import CirculationService, CirculationError
from myapp.services.analytics_service import AnalyticsService


def global_context(request):
    """Context processor providing operational stats and platform metadata to all templates."""
    today = date.today()
    overdue_count = IssueBook.objects.filter(return_date__isnull=True, due_date__lt=today).count()
    categories_list = Category.objects.all()[:12]
    return {
        'platform_name': 'The Archive',
        'institution_name': 'University Research Library',
        'global_overdue_count': overdue_count,
        'global_categories': categories_list,
        'current_year': timezone.now().year,
    }


def home(request):
    """
    Primary Operations & Intelligence Dashboard.
    Presents real-time KPIs, circulation activity, overdue notices, and quick-action modals.
    """
    summary = AnalyticsService.get_dashboard_summary()
    categories_data = AnalyticsService.get_genre_distribution()[:6]
    circulation_trends = AnalyticsService.get_monthly_circulation_trends(months_back=6)
    recommendations = AnalyticsService.get_acquisition_recommendations(limit=4)

    # Categories for quick filter
    categories = Category.objects.all()

    context = {
        'summary': summary,
        'categories_data': categories_data,
        'circulation_trends_json': json.dumps(circulation_trends),
        'categories_json': json.dumps(categories_data),
        'recommendations': recommendations,
        'categories': categories,
    }
    return render(request, 'lms/home.html', context)


# ==============================================================================
# CATALOG & BOOKS VIEWS
# ==============================================================================

def catalog_list_view(request):
    """Searchable, filterable, and paginated scholarly catalog."""
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    availability = request.GET.get('availability', '')
    sort_by = request.GET.get('sort', 'title')

    books = Book.objects.select_related('category').all()

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query) |
            Q(call_number__icontains=query) |
            Q(publisher__icontains=query)
        )

    if category_id and category_id.isdigit():
        books = books.filter(category_id=int(category_id))

    if availability == 'available':
        books = books.filter(available_copies__gt=0)
    elif availability == 'borrowed':
        books = books.filter(available_copies=0)

    # Sorting
    if sort_by == 'author':
        books = books.order_by('author', 'title')
    elif sort_by == 'newest':
        books = books.order_by('-created_at')
    elif sort_by == 'year':
        books = books.order_by('-publication_year', 'title')
    elif sort_by == 'copies':
        books = books.order_by('-quantity')
    else:
        books = books.order_by('title')

    # Pagination: 12 items per page
    paginator = Paginator(books, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    context = {
        'page_obj': page_obj,
        'books': page_obj.object_list,
        'query': query,
        'selected_category': category_id,
        'selected_availability': availability,
        'selected_sort': sort_by,
        'categories': categories,
        'total_count': paginator.count,
    }
    return render(request, 'lms/catalog/book_list.html', context)


def book_detail_view(request, id):
    """Detailed view for a catalog title with shelf coordinates, spine cover, and circulation history."""
    book = get_object_or_404(Book.objects.select_related('category'), pk=id)
    loans = IssueBook.objects.filter(book=book).select_related('student').order_by('-issue_date')[:10]
    active_loan = IssueBook.objects.filter(book=book, return_date__isnull=True).select_related('student').first()
    
    # Related works from the same category or general collection
    related_books = Book.objects.filter(category=book.category).exclude(pk=book.pk)[:3] if book.category else Book.objects.exclude(pk=book.pk)[:3]

    context = {
        'book': book,
        'loans': loans,
        'active_loan': active_loan,
        'related_books': related_books,
    }
    return render(request, 'lms/catalog/book_detail.html', context)


def add_book(request):
    """Add a new book to the catalog (backward compatible url name 'add_book')."""
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save()
            messages.success(request, f"'{book.title}' was successfully added to the catalog.")
            return redirect('book_detail', id=book.id)
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        form = BookForm()

    return render(request, 'lms/catalog/book_form.html', {
        'form': form,
        'action_title': 'Add New Catalog Acquisition',
        'is_edit': False,
    })


def edit_book(request, id):
    """Edit catalog book details (backward compatible url name 'edit_book')."""
    book = get_object_or_404(Book, pk=id)

    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            updated_book = form.save()
            messages.success(request, f"Updated details for '{updated_book.title}'.")
            return redirect('book_detail', id=updated_book.id)
        else:
            messages.error(request, "Please review form errors.")
    else:
        form = BookForm(instance=book)

    return render(request, 'lms/catalog/book_form.html', {
        'form': form,
        'book': book,
        'action_title': f"Edit Catalog Item — {book.title}",
        'is_edit': True,
    })


@require_POST
def delete_book(request, id):
    """Safely delete book if there are no active outstanding loans."""
    book = get_object_or_404(Book, pk=id)
    
    active_loans = IssueBook.objects.filter(book=book, return_date__isnull=True).exists()
    if active_loans:
        messages.error(request, f"Cannot delete '{book.title}' because it has active circulation loans.")
        return redirect('book_detail', id=book.id)

    book_title = book.title
    book.delete()
    messages.success(request, f"'{book_title}' has been removed from the catalog.")
    return redirect('catalog_list')


# ==============================================================================
# CIRCULATION & LOAN OPERATIONS
# ==============================================================================

def loan_list_view(request):
    """Circulation desk register: active loans, overdue items, and return history."""
    filter_status = request.GET.get('status', 'ACTIVE')
    search_q = request.GET.get('q', '').strip()

    loans = IssueBook.objects.select_related('book', 'student').all()

    today = date.today()
    if filter_status == 'ACTIVE':
        loans = loans.filter(return_date__isnull=True)
    elif filter_status == 'OVERDUE':
        loans = loans.filter(return_date__isnull=True, due_date__lt=today)
    elif filter_status == 'RETURNED':
        loans = loans.filter(return_date__isnull=False)

    if search_q:
        loans = loans.filter(
            Q(book__title__icontains=search_q) |
            Q(student__name__icontains=search_q) |
            Q(student__patron_id__icontains=search_q) |
            Q(book__call_number__icontains=search_q)
        )

    paginator = Paginator(loans, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    active_count = IssueBook.objects.filter(return_date__isnull=True).count()
    overdue_count = IssueBook.objects.filter(return_date__isnull=True, due_date__lt=today).count()
    returned_count = IssueBook.objects.filter(return_date__isnull=False).count()

    context = {
        'page_obj': page_obj,
        'loans': page_obj.object_list,
        'filter_status': filter_status,
        'search_q': search_q,
        'active_count': active_count,
        'overdue_count': overdue_count,
        'returned_count': returned_count,
    }
    return render(request, 'lms/circulation/loan_list.html', context)


def issue_book_view(request):
    """Issue / checkout a book to an active patron."""
    prefill_book_id = request.GET.get('book_id')
    prefill_student_id = request.GET.get('student_id')

    if request.method == 'POST':
        form = CirculationIssueForm(request.POST)
        if form.is_valid():
            book = form.cleaned_data['book']
            student = form.cleaned_data['student']
            loan_period_days = form.cleaned_data['loan_period_days']
            notes = form.cleaned_data['notes']

            try:
                loan = CirculationService.issue_book(
                    book_id=book.id,
                    student_id=student.id,
                    issued_by=request.user if request.user.is_authenticated else None,
                    due_days=loan_period_days,
                    notes=notes
                )
                messages.success(request, f"Successfully issued '{book.title}' to {student.name}. Due on {loan.due_date}.")
                return redirect('loan_list')
            except CirculationError as e:
                messages.error(request, str(e))
    else:
        initial = {'loan_period_days': 14}
        if prefill_book_id:
            initial['book'] = prefill_book_id
        if prefill_student_id:
            initial['student'] = prefill_student_id
        form = CirculationIssueForm(initial=initial)

    return render(request, 'lms/circulation/issue_form.html', {'form': form})


@require_POST
def return_book_view(request, loan_id):
    """Process an atomic book checkin / return."""
    notes = request.POST.get('return_notes', '')
    try:
        loan, fine = CirculationService.return_book(
            issue_id=loan_id,
            user=request.user if request.user.is_authenticated else None,
            notes=notes
        )
        if fine:
            messages.warning(
                request,
                f"'{loan.book.title}' returned. An overdue fine of ${fine.amount:.2f} was assessed ({fine.notes})."
            )
        else:
            messages.success(request, f"'{loan.book.title}' was successfully returned and restocked.")
    except CirculationError as e:
        messages.error(request, str(e))

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'loan_list'
    return redirect(next_url)


@require_POST
def renew_book_view(request, loan_id):
    """Extend due date of an active borrowing."""
    try:
        loan = CirculationService.renew_book(
            issue_id=loan_id,
            additional_days=14,
            user=request.user if request.user.is_authenticated else None
        )
        messages.success(request, f"Loan for '{loan.book.title}' renewed until {loan.due_date} (Renewal #{loan.renewal_count}).")
    except CirculationError as e:
        messages.error(request, str(e))

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'loan_list'
    return redirect(next_url)


# ==============================================================================
# PATRONS & MEMBERS VIEWS
# ==============================================================================

def patron_list_view(request):
    """Patron directory with department, role, and compliance status."""
    query = request.GET.get('q', '').strip()
    role = request.GET.get('role', '')
    dept = request.GET.get('dept', '')

    patrons = Student.objects.all()

    if query:
        patrons = patrons.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(patron_id__icontains=query) |
            Q(department__icontains=query)
        )

    if role:
        patrons = patrons.filter(role=role)
    if dept:
        patrons = patrons.filter(department=dept)

    patrons = patrons.order_by('name')

    paginator = Paginator(patrons, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    departments = Student.objects.values_list('department', flat=True).distinct().order_by('department')

    context = {
        'page_obj': page_obj,
        'patrons': page_obj.object_list,
        'query': query,
        'selected_role': role,
        'selected_dept': dept,
        'departments': departments,
        'roles': Student.ROLE_CHOICES,
        'total_count': paginator.count,
    }
    return render(request, 'lms/patrons/patron_list.html', context)


def patron_detail_view(request, id):
    """Patron profile, active loans, borrowing history, and fine balance."""
    patron = get_object_or_404(Student, pk=id)
    active_loans = IssueBook.objects.filter(student=patron, return_date__isnull=True).select_related('book').order_by('due_date')
    history_loans = IssueBook.objects.filter(student=patron, return_date__isnull=False).select_related('book').order_by('-return_date')[:15]
    fines = FineLedger.objects.filter(student=patron).select_related('issue__book').order_by('-created_at')

    context = {
        'patron': patron,
        'active_loans': active_loans,
        'history_loans': history_loans,
        'fines': fines,
    }
    return render(request, 'lms/patrons/patron_detail.html', context)


def patron_create_view(request):
    """Register a new patron."""
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            patron = form.save()
            messages.success(request, f"Patron '{patron.name}' ({patron.patron_id}) registered successfully.")
            return redirect('patron_detail', id=patron.id)
        else:
            messages.error(request, "Please check the form for errors.")
    else:
        form = StudentForm()

    return render(request, 'lms/patrons/patron_form.html', {
        'form': form,
        'action_title': 'Register New Library Member',
        'is_edit': False,
    })


def patron_edit_view(request, id):
    """Edit patron profile."""
    patron = get_object_or_404(Student, pk=id)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=patron)
        if form.is_valid():
            updated = form.save()
            messages.success(request, f"Updated record for {updated.name}.")
            return redirect('patron_detail', id=updated.id)
        else:
            messages.error(request, "Please review form errors.")
    else:
        form = StudentForm(instance=patron)

    return render(request, 'lms/patrons/patron_form.html', {
        'form': form,
        'patron': patron,
        'action_title': f"Edit Patron — {patron.name}",
        'is_edit': True,
    })


@require_POST
def settle_fine_view(request, fine_id):
    """Settle or waive a patron fine."""
    form = FineSettlementForm(request.POST)
    if form.is_valid():
        action = form.cleaned_data['action']
        payment_amount = form.cleaned_data['payment_amount']
        notes = form.cleaned_data['notes']

        try:
            fine = CirculationService.settle_fine(
                fine_id=fine_id,
                action=action,
                paid_amount=payment_amount,
                user=request.user if request.user.is_authenticated else None,
                notes=notes
            )
            messages.success(request, f"Fine status updated to {fine.status}.")
        except CirculationError as e:
            messages.error(request, str(e))
    else:
        messages.error(request, "Invalid fine settlement input.")

    return redirect(request.META.get('HTTP_REFERER') or 'home')


# ==============================================================================
# ANALYTICS & INTELLIGENCE
# ==============================================================================

def analytics_view(request):
    """Dedicated Intelligence & Reporting dashboard."""
    summary = AnalyticsService.get_dashboard_summary()
    genre_data = AnalyticsService.get_genre_distribution()
    trend_data = AnalyticsService.get_monthly_circulation_trends(months_back=6)
    recommendations = AnalyticsService.get_acquisition_recommendations(limit=10)
    top_patrons = AnalyticsService.get_top_engaged_patrons(limit=8)
    dept_breakdown = AnalyticsService.get_department_circulation_breakdown()

    context = {
        'summary': summary,
        'genre_data': genre_data,
        'trend_data_json': json.dumps(trend_data),
        'genre_data_json': json.dumps(genre_data),
        'dept_breakdown_json': json.dumps(dept_breakdown),
        'recommendations': recommendations,
        'top_patrons': top_patrons,
        'dept_breakdown': dept_breakdown,
    }
    return render(request, 'lms/analytics/analytics.html', context)


@require_GET
def api_chart_data(request):
    """JSON API endpoint supplying structured metrics for visualizations."""
    trend_data = AnalyticsService.get_monthly_circulation_trends(months_back=6)
    genre_data = AnalyticsService.get_genre_distribution()
    dept_data = AnalyticsService.get_department_circulation_breakdown()

    return JsonResponse({
        'status': 'success',
        'circulation_trends': trend_data,
        'genre_distribution': genre_data,
        'department_breakdown': dept_data,
    })


# ==============================================================================
# AUTHENTICATION
# ==============================================================================

def login_view(request):
    """Secure staff login portal."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}.")
            next_url = request.GET.get('next') or 'home'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'lms/auth/login.html', {'form': form})


def logout_view(request):
    """Logout staff session."""
    logout(request)
    messages.info(request, "You have been securely signed out.")
    return redirect('home')


# ==============================================================================
# ERROR HANDLERS
# ==============================================================================

def handler404(request, exception=None):
    return render(request, 'lms/errors/404.html', status=404)


def handler500(request):
    return render(request, 'lms/errors/500.html', status=500)
