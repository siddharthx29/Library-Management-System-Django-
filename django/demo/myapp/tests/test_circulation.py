from django.test import TestCase
from datetime import date, timedelta
from decimal import Decimal
from myapp.models import Category, Book, Student, IssueBook, FineLedger
from myapp.services.circulation_service import CirculationService, CirculationError


class CirculationServiceTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(code="510", name="Mathematics")
        self.book = Book.objects.create(
            title="Calculus Vol 1",
            author="Tom M. Apostol",
            isbn="9780471000051",
            call_number="QA300 .A57",
            quantity=2,
            available_copies=2
        )
        self.student = Student.objects.create(
            patron_id="PAT-CIRC-01",
            name="Bob Smith",
            email="bob@test.edu",
            max_borrow_limit=2,
            is_active=True
        )

    def test_issue_book_success_and_atomic_decrement(self):
        loan = CirculationService.issue_book(
            book_id=self.book.id,
            student_id=self.student.id,
            due_days=14
        )
        self.assertEqual(loan.book, self.book)
        self.assertEqual(loan.student, self.student)
        self.assertEqual(loan.status, 'ACTIVE')
        
        # Verify book availability was decremented
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 1)

    def test_issue_book_fails_when_no_copies_available(self):
        # Deplete available copies
        self.book.available_copies = 0
        self.book.save()

        with self.assertRaises(CirculationError) as ctx:
            CirculationService.issue_book(
                book_id=self.book.id,
                student_id=self.student.id
            )
        self.assertIn("out of stock", str(ctx.exception))

    def test_issue_book_fails_when_patron_limit_reached(self):
        # Set limit to 1 and create 1 loan
        self.student.max_borrow_limit = 1
        self.student.save()

        CirculationService.issue_book(book_id=self.book.id, student_id=self.student.id)

        book2 = Book.objects.create(title="Calculus Vol 2", author="Apostol", quantity=1, available_copies=1)

        with self.assertRaises(CirculationError) as ctx:
            CirculationService.issue_book(book_id=book2.id, student_id=self.student.id)
        self.assertIn("maximum borrowing limit", str(ctx.exception))

    def test_issue_book_fails_for_inactive_patron(self):
        self.student.is_active = False
        self.student.save()

        with self.assertRaises(CirculationError) as ctx:
            CirculationService.issue_book(book_id=self.book.id, student_id=self.student.id)
        self.assertIn("inactive or suspended", str(ctx.exception))

    def test_return_book_on_time_restores_inventory(self):
        loan = CirculationService.issue_book(book_id=self.book.id, student_id=self.student.id)
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 1)

        loan_ret, fine = CirculationService.return_book(issue_id=loan.id)
        self.assertEqual(loan_ret.status, 'RETURNED')
        self.assertIsNone(fine)

        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 2)

    def test_return_book_overdue_assesses_fine(self):
        today = date.today()
        # Create loan due 4 days ago
        loan = IssueBook.objects.create(
            book=self.book,
            student=self.student,
            issue_date=today - timedelta(days=18),
            due_date=today - timedelta(days=4),
            status='ACTIVE'
        )
        self.book.available_copies = 1
        self.book.save()

        loan_ret, fine = CirculationService.return_book(issue_id=loan.id, return_date=today)
        self.assertEqual(loan_ret.status, 'RETURNED')
        self.assertIsNotNone(fine)
        self.assertEqual(fine.amount, Decimal('2.00')) # 4 days * 0.50
        self.assertEqual(fine.status, 'PENDING')

    def test_renew_book_extends_due_date(self):
        loan = CirculationService.issue_book(book_id=self.book.id, student_id=self.student.id, due_days=14)
        original_due = loan.due_date

        renewed_loan = CirculationService.renew_book(issue_id=loan.id, additional_days=14)
        self.assertEqual(renewed_loan.renewal_count, 1)
        self.assertEqual(renewed_loan.due_date, original_due + timedelta(days=14))

    def test_fine_settlement_paid_and_waived(self):
        loan = IssueBook.objects.create(
            book=self.book,
            student=self.student,
            issue_date=date.today() - timedelta(days=20),
            due_date=date.today() - timedelta(days=5),
            status='RETURNED'
        )
        fine = FineLedger.objects.create(
            issue=loan,
            student=self.student,
            amount=Decimal('4.00'),
            paid_amount=Decimal('0.00'),
            status='PENDING'
        )

        CirculationService.settle_fine(fine_id=fine.id, action='PAID', paid_amount=Decimal('4.00'))
        fine.refresh_from_db()
        self.assertEqual(fine.status, 'PAID')
        self.assertEqual(fine.remaining_amount, Decimal('0.00'))
