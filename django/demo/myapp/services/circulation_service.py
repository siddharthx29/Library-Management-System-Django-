from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from decimal import Decimal
from myapp.models import Book, Student, IssueBook, FineLedger


class CirculationError(Exception):
    """Custom domain exception for circulation operation failures."""
    pass


class CirculationService:
    """
    Handles atomic circulation workflows (issue, return, renew, fine settlements).
    Enforces transaction isolation and concurrency safety via select_for_update.
    """

    @classmethod
    def issue_book(cls, book_id, student_id, issued_by=None, due_days=14, notes=""):
        """
        Atomically checkout a book to a patron.
        """
        with transaction.atomic():
            # Acquire row-level locks
            try:
                book = Book.objects.select_for_update().get(pk=book_id)
            except Book.DoesNotExist:
                raise CirculationError("The requested catalog book does not exist.")

            try:
                student = Student.objects.select_for_update().get(pk=student_id)
            except Student.DoesNotExist:
                raise CirculationError("The specified patron does not exist.")

            # Eligibility validations
            if not student.is_active:
                raise CirculationError(f"Patron {student.name} ({student.patron_id}) membership is inactive or suspended.")

            active_loans_count = IssueBook.objects.filter(student=student, return_date__isnull=True).count()
            if active_loans_count >= student.max_borrow_limit:
                raise CirculationError(
                    f"Patron has reached the maximum borrowing limit ({student.max_borrow_limit} books)."
                )

            # Check if patron already has an active loan of this exact book
            existing_loan = IssueBook.objects.filter(
                student=student,
                book=book,
                return_date__isnull=True
            ).exists()
            if existing_loan:
                raise CirculationError(f"Patron {student.name} currently holds an active copy of '{book.title}'.")

            # Inventory validation
            if book.available_copies <= 0:
                raise CirculationError(f"'{book.title}' is currently out of stock with 0 available copies.")

            # Update inventory and record loan
            book.available_copies -= 1
            book.save(update_fields=['available_copies', 'updated_at'])

            issue_date = date.today()
            due_date = issue_date + timedelta(days=int(due_days))

            loan = IssueBook.objects.create(
                book=book,
                student=student,
                issued_by=issued_by,
                issue_date=issue_date,
                due_date=due_date,
                status='ACTIVE',
                notes=notes.strip()
            )

            return loan

    @classmethod
    def return_book(cls, issue_id, user=None, return_date=None, notes=""):
        """
        Atomically process book return, recalculate fines, and restore inventory.
        """
        with transaction.atomic():
            try:
                loan = IssueBook.objects.select_for_update().get(pk=issue_id)
            except IssueBook.DoesNotExist:
                raise CirculationError("Circulation loan record not found.")

            if loan.return_date is not None:
                raise CirculationError(f"This item was already returned on {loan.return_date}.")

            book = Book.objects.select_for_update().get(pk=loan.book_id)

            actual_return_date = return_date or date.today()
            loan.return_date = actual_return_date
            loan.status = 'RETURNED'
            if notes:
                loan.notes = (loan.notes + f"\n[Return Note]: {notes}").strip()
            loan.save(update_fields=['return_date', 'status', 'notes'])

            # Restore inventory safely
            if book.available_copies < book.quantity:
                book.available_copies += 1
                book.save(update_fields=['available_copies', 'updated_at'])

            # Fine calculation
            fine_record = None
            if loan.due_date and actual_return_date > loan.due_date:
                days_overdue = (actual_return_date - loan.due_date).days
                fine_amount = Decimal(days_overdue) * Decimal('0.50')

                if fine_amount > Decimal('0.00'):
                    fine_record = FineLedger.objects.create(
                        issue=loan,
                        student=loan.student,
                        amount=fine_amount,
                        paid_amount=Decimal('0.00'),
                        status='PENDING',
                        notes=f"Overdue by {days_overdue} day(s) (${Decimal('0.50')}/day)."
                    )

            return loan, fine_record

    @classmethod
    def renew_book(cls, issue_id, additional_days=14, user=None):
        """
        Atomically renew an active loan if within institutional limits.
        """
        with transaction.atomic():
            try:
                loan = IssueBook.objects.select_for_update().get(pk=issue_id)
            except IssueBook.DoesNotExist:
                raise CirculationError("Circulation loan record not found.")

            if loan.return_date is not None:
                raise CirculationError("Cannot renew an already returned book.")

            if loan.renewal_count >= 2:
                raise CirculationError("Maximum renewal limit (2 times) reached for this loan.")

            # Calculate new due date
            base_date = max(loan.due_date or date.today(), date.today())
            loan.due_date = base_date + timedelta(days=int(additional_days))
            loan.renewal_count += 1
            loan.status = 'ACTIVE'
            loan.save(update_fields=['due_date', 'renewal_count', 'status'])

            return loan

    @classmethod
    def settle_fine(cls, fine_id, action='PAID', paid_amount=None, user=None, notes=""):
        """
        Settle or waive a pending fine.
        """
        with transaction.atomic():
            try:
                fine = FineLedger.objects.select_for_update().get(pk=fine_id)
            except FineLedger.DoesNotExist:
                raise CirculationError("Fine record not found.")

            if fine.status != 'PENDING':
                raise CirculationError(f"Fine is already marked as {fine.status}.")

            if action == 'WAIVED':
                fine.status = 'WAIVED'
                fine.settled_at = timezone.now()
                fine.settled_by = user
                fine.notes = (fine.notes + f"\n[Waived]: {notes}").strip()
            elif action == 'PAID':
                amount = Decimal(str(paid_amount)) if paid_amount is not None else fine.amount
                fine.paid_amount = min(fine.amount, fine.paid_amount + amount)
                if fine.paid_amount >= fine.amount:
                    fine.status = 'PAID'
                fine.settled_at = timezone.now()
                fine.settled_by = user
                if notes:
                    fine.notes = (fine.notes + f"\n[Settled]: {notes}").strip()
            else:
                raise CirculationError("Invalid fine action.")

            fine.save()
            return fine
