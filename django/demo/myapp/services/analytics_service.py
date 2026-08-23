from django.db.models import Count, Sum, Q, F, Avg, Case, When, Value, IntegerField
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from myapp.models import Book, Student, IssueBook, FineLedger, Category


class AnalyticsService:
    """
    Dedicated intelligence and reporting service.
    Aggregates operational metrics, circulation velocity, demand alerts, and patron engagement.
    """

    @classmethod
    def get_dashboard_summary(cls):
        """
        Calculates executive operational KPIs for the primary dashboard.
        """
        today = date.today()

        # Catalog Metrics
        catalog_aggregate = Book.objects.aggregate(
            total_titles=Count('id'),
            total_copies=Sum('quantity'),
            available_copies=Sum('available_copies')
        )
        total_titles = catalog_aggregate['total_titles'] or 0
        total_copies = catalog_aggregate['total_copies'] or 0
        available_copies = catalog_aggregate['available_copies'] or 0
        borrowed_copies = max(0, total_copies - available_copies)

        utilization_rate = round((borrowed_copies / total_copies * 100), 1) if total_copies > 0 else 0.0

        # Circulation Metrics
        total_patrons = Student.objects.filter(is_active=True).count()
        active_loans = IssueBook.objects.filter(return_date__isnull=True).count()
        overdue_loans = IssueBook.objects.filter(
            return_date__isnull=True,
            due_date__lt=today
        ).count()
        overdue_rate = round((overdue_loans / active_loans * 100), 1) if active_loans > 0 else 0.0

        # Fine Financials
        fine_aggregate = FineLedger.objects.aggregate(
            total_billed=Sum('amount'),
            total_collected=Sum('paid_amount'),
            pending_count=Count('id', filter=Q(status='PENDING'))
        )
        total_billed = fine_aggregate['total_billed'] or Decimal('0.00')
        total_collected = fine_aggregate['total_collected'] or Decimal('0.00')
        outstanding_fines = max(Decimal('0.00'), total_billed - total_collected)

        # Recent activities
        recent_loans = IssueBook.objects.select_related('book', 'student').order_by('-id')[:6]
        critical_overdue = IssueBook.objects.filter(
            return_date__isnull=True,
            due_date__lt=today
        ).select_related('book', 'student').order_by('due_date')[:5]

        return {
            'total_titles': total_titles,
            'total_copies': total_copies,
            'available_copies': available_copies,
            'borrowed_copies': borrowed_copies,
            'utilization_rate': utilization_rate,
            'total_patrons': total_patrons,
            'active_loans': active_loans,
            'overdue_loans': overdue_loans,
            'overdue_rate': overdue_rate,
            'total_billed_fines': total_billed,
            'total_collected_fines': total_collected,
            'outstanding_fines': outstanding_fines,
            'recent_loans': recent_loans,
            'critical_overdue': critical_overdue,
        }

    @classmethod
    def get_genre_distribution(cls):
        """
        Answers: 'What is being borrowed and held?'
        Breakdown of holdings and circulation count by Category.
        """
        categories = Category.objects.annotate(
            book_count=Count('books', distinct=True),
            total_copies=Sum('books__quantity'),
            loan_count=Count('books__loans', distinct=True)
        ).order_by('-loan_count')

        data = []
        for cat in categories:
            data.append({
                'id': cat.id,
                'code': cat.code,
                'name': cat.name,
                'book_count': cat.book_count,
                'total_copies': cat.total_copies or 0,
                'loan_count': cat.loan_count,
            })
        return data

    @classmethod
    def get_monthly_circulation_trends(cls, months_back=6):
        """
        Answers: 'When are books being borrowed?'
        Aggregates checkouts and returns across rolling months.
        """
        today = date.today()
        trend_data = []

        # Generate month slots
        for i in range(months_back - 1, -1, -1):
            # Calculate target month date
            year = today.year
            month = today.month - i
            while month <= 0:
                month += 12
                year -= 1

            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)

            month_label = start_date.strftime("%b %Y")

            issues_count = IssueBook.objects.filter(
                issue_date__gte=start_date,
                issue_date__lte=end_date
            ).count()

            returns_count = IssueBook.objects.filter(
                return_date__gte=start_date,
                return_date__lte=end_date
            ).count()

            trend_data.append({
                'label': month_label,
                'issues': issues_count,
                'returns': returns_count,
            })

        return trend_data

    @classmethod
    def get_acquisition_recommendations(cls, limit=10):
        """
        Answers: 'What should we buy more of?'
        Identifies high-demand titles with critically low availability ratios.
        """
        # Annotate books with total loan frequency
        books = Book.objects.annotate(
            total_borrows=Count('loans')
        ).filter(total_borrows__gt=0).order_by('-total_borrows', 'available_copies')

        recommendations = []
        for book in books:
            # Check availability stress
            avail_ratio = (book.available_copies / book.quantity) if book.quantity > 0 else 0
            if book.available_copies == 0 or (book.total_borrows >= book.quantity and avail_ratio < 0.4):
                urgency = 'CRITICAL' if book.available_copies == 0 else 'HIGH'
                suggested_copies = max(2, int(book.total_borrows * 0.5) - book.available_copies)
                recommendations.append({
                    'book': book,
                    'total_borrows': book.total_borrows,
                    'quantity': book.quantity,
                    'available_copies': book.available_copies,
                    'avail_ratio_percent': round(avail_ratio * 100, 1),
                    'urgency': urgency,
                    'suggested_copies': suggested_copies,
                })

        return recommendations[:limit]

    @classmethod
    def get_top_engaged_patrons(cls, limit=8):
        """
        Answers: 'Who are our most engaged members?'
        Ranks patrons by circulation engagement and compliance.
        """
        patrons = Student.objects.annotate(
            total_loans=Count('loans'),
            active_loans=Count('loans', filter=Q(loans__return_date__isnull=True))
        ).order_by('-total_loans')[:limit]

        return patrons

    @classmethod
    def get_department_circulation_breakdown(cls):
        """
        Answers: 'Where is library usage strongest?'
        Aggregates circulation by academic department and patron role.
        """
        dept_data = Student.objects.values('department').annotate(
            member_count=Count('id'),
            total_loans=Count('loans')
        ).order_by('-total_loans')

        role_data = Student.objects.values('role').annotate(
            member_count=Count('id'),
            total_loans=Count('loans')
        ).order_by('-total_loans')

        return {
            'by_department': list(dept_data),
            'by_role': list(role_data),
        }
