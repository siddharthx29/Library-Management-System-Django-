from django.test import TestCase
from datetime import date, timedelta
from decimal import Decimal
from myapp.models import Category, Book, Student, IssueBook, FineLedger
from myapp.services.analytics_service import AnalyticsService


class AnalyticsServiceTests(TestCase):
    def setUp(self):
        self.cat_cs = Category.objects.create(code="004", name="Computer Science")
        self.cat_lit = Category.objects.create(code="800", name="Literature")

        self.book1 = Book.objects.create(
            title="Clean Code",
            author="Robert C. Martin",
            isbn="9780132350884",
            category=self.cat_cs,
            quantity=5,
            available_copies=2
        )
        self.book2 = Book.objects.create(
            title="Hamlet",
            author="William Shakespeare",
            isbn="9780743477123",
            category=self.cat_lit,
            quantity=3,
            available_copies=3
        )

        self.patron1 = Student.objects.create(
            patron_id="PAT-A1",
            name="Charlie Brown",
            email="charlie@test.edu",
            department="Computer Science",
            role="UNDERGRADUATE"
        )

        # Issue 2 loans
        IssueBook.objects.create(
            book=self.book1,
            student=self.patron1,
            issue_date=date.today() - timedelta(days=2),
            due_date=date.today() + timedelta(days=12),
            status='ACTIVE'
        )

    def test_dashboard_summary_computation(self):
        summary = AnalyticsService.get_dashboard_summary()
        self.assertEqual(summary['total_titles'], 2)
        self.assertEqual(summary['total_copies'], 8)
        self.assertEqual(summary['available_copies'], 5)
        self.assertEqual(summary['borrowed_copies'], 3)
        self.assertEqual(summary['active_loans'], 1)

    def test_genre_distribution_computation(self):
        genres = AnalyticsService.get_genre_distribution()
        self.assertEqual(len(genres), 2)
        cs_genre = next(g for g in genres if g['code'] == '004')
        self.assertEqual(cs_genre['book_count'], 1)
        self.assertEqual(cs_genre['total_copies'], 5)

    def test_acquisition_recommendations_filters_high_demand(self):
        # Create a book with 0 available copies and active demand
        hot_book = Book.objects.create(
            title="Design Patterns",
            author="Gang of Four",
            isbn="9780201633610",
            category=self.cat_cs,
            quantity=2,
            available_copies=0
        )
        IssueBook.objects.create(book=hot_book, student=self.patron1, issue_date=date.today())

        recs = AnalyticsService.get_acquisition_recommendations()
        self.assertTrue(any(r['book'].id == hot_book.id for r in recs))
