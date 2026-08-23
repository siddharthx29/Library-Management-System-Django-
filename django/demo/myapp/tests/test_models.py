from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from myapp.models import Category, Book, Student, IssueBook, FineLedger


class ModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            code="004",
            name="Computer Science",
            description="Computing & Systems"
        )
        self.book = Book.objects.create(
            title="Algorithm Design Manual",
            author="Steven S. Skiena",
            isbn="9781849967204",
            call_number="QA76.9 .A43 S55 2008",
            category=self.category,
            quantity=5,
            available_copies=5
        )
        self.student = Student.objects.create(
            patron_id="PAT-TEST-001",
            name="Alice Walker",
            email="alice@test.edu",
            department="Computer Science",
            role="UNDERGRADUATE",
            max_borrow_limit=5
        )

    def test_category_string_representation(self):
        self.assertEqual(str(self.category), "004 — Computer Science")

    def test_book_inventory_properties(self):
        self.assertEqual(str(self.book), "Algorithm Design Manual by Steven S. Skiena")
        self.assertTrue(self.book.is_available)
        self.assertEqual(self.book.borrowed_copies, 0)

        # Test validation when available exceeds quantity
        self.book.available_copies = 10
        with self.assertRaises(ValidationError):
            self.book.clean()

    def test_student_properties_and_borrowing_status(self):
        self.assertEqual(str(self.student), "Alice Walker (PAT-TEST-001)")
        self.assertTrue(self.student.can_borrow)
        self.assertEqual(self.student.active_loans_count, 0)
        self.assertEqual(self.student.total_fines_due, Decimal('0.00'))

    def test_issue_book_overdue_and_fine_calculation(self):
        today = date.today()
        # Create an overdue loan (due 5 days ago)
        loan = IssueBook.objects.create(
            book=self.book,
            student=self.student,
            issue_date=today - timedelta(days=19),
            due_date=today - timedelta(days=5),
            status='ACTIVE'
        )

        self.assertTrue(loan.is_overdue)
        self.assertEqual(loan.overdue_days, 5)
        self.assertEqual(loan.calculated_fine, Decimal('2.50'))

    def test_fine_ledger_remaining_amount(self):
        loan = IssueBook.objects.create(
            book=self.book,
            student=self.student,
            issue_date=date.today() - timedelta(days=10),
            due_date=date.today() - timedelta(days=2)
        )
        fine = FineLedger.objects.create(
            issue=loan,
            student=self.student,
            amount=Decimal('5.00'),
            paid_amount=Decimal('2.00'),
            status='PENDING'
        )
        self.assertEqual(fine.remaining_amount, Decimal('3.00'))

        fine.status = 'PAID'
        self.assertEqual(fine.remaining_amount, Decimal('0.00'))
