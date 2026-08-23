from django.test import TestCase, Client
from django.urls import reverse
from myapp.models import Category, Book, Student, IssueBook
from myapp.forms import BookForm, StudentForm


class SecurityAndFormsTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(code="340", name="Law")

    def test_book_form_valid_and_isbn_cleanup(self):
        data = {
            'title': 'The Concept of Law',
            'author': 'H. L. A. Hart',
            'isbn': '978-0199644704',
            'call_number': 'K230 .H37',
            'category': self.category.id,
            'quantity': 3,
            'available_copies': 3,
            'publication_year': 2012,
            'publisher': 'Oxford University Press',
            'shelf_location': 'Law Wing B',
            'description': 'Analytical jurisprudence foundation.'
        }
        form = BookForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['isbn'], '9780199644704')

    def test_book_form_invalid_available_copies(self):
        data = {
            'title': 'Sample Law Book',
            'author': 'Author',
            'quantity': 2,
            'available_copies': 5, # Exceeds quantity!
        }
        form = BookForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('available_copies', form.errors)

    def test_student_form_duplicate_email_rejected(self):
        Student.objects.create(
            name="John Doe",
            email="john@univ.edu",
            patron_id="PAT-JD-01"
        )
        # Attempt duplicate email
        form = StudentForm(data={
            'name': 'Jonathan Doe',
            'email': 'john@univ.edu',
            'patron_id': 'PAT-JD-02',
            'role': 'UNDERGRADUATE',
            'max_borrow_limit': 5,
            'is_active': True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class ViewsIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(code="004", name="Computer Science")
        self.book = Book.objects.create(
            title="Operating Systems Concepts",
            author="Silberschatz",
            isbn="9781118063330",
            category=self.category,
            quantity=4,
            available_copies=4
        )
        self.student = Student.objects.create(
            patron_id="PAT-VIEW-01",
            name="Diana Prince",
            email="diana@univ.edu",
            department="Computer Science"
        )

    def test_dashboard_view_status_and_template(self):
        # Create a loan so it appears in recent loans
        IssueBook.objects.create(
            book=self.book,
            student=self.student,
            notes="Test checkout"
        )
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Library Overview")
        self.assertContains(response, "Operating Systems Concepts")

    def test_catalog_list_and_search_query(self):
        response = self.client.get(reverse('catalog_list'), {'q': 'Silberschatz'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Operating Systems Concepts")

        # Non-matching search
        response_empty = self.client.get(reverse('catalog_list'), {'q': 'QuantumCosmologyXYZ'})
        self.assertContains(response_empty, "No catalogue volumes match the specified query.")

    def test_book_detail_view(self):
        response = self.client.get(reverse('book_detail', args=[self.book.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bibliographic & Archival Record")

    def test_add_book_view_post(self):
        response = self.client.post(reverse('add_book'), {
            'title': 'Introduction to Automata Theory',
            'author': 'Hopcroft & Ullman',
            'isbn': '9780201441246',
            'category': self.category.id,
            'quantity': 3,
            'available_copies': 3,
        })
        self.assertEqual(response.status_code, 302) # Redirect to book_detail
        self.assertTrue(Book.objects.filter(title='Introduction to Automata Theory').exists())

    def test_circulation_issue_and_return_cycle(self):
        # 1. Issue book
        issue_response = self.client.post(reverse('issue_book'), {
            'book': self.book.id,
            'student': self.student.id,
            'loan_period_days': 14,
            'notes': 'Course text checkout.'
        })
        self.assertEqual(issue_response.status_code, 302)
        loan = IssueBook.objects.get(book=self.book, student=self.student)
        self.assertEqual(loan.status, 'ACTIVE')

        # 2. Return book
        return_response = self.client.post(reverse('return_book', args=[loan.id]), {
            'return_notes': 'Returned in pristine condition.'
        })
        self.assertEqual(return_response.status_code, 302)
        loan.refresh_from_db()
        self.assertEqual(loan.status, 'RETURNED')

    def test_analytics_view_and_api_endpoint(self):
        resp_view = self.client.get(reverse('analytics'))
        self.assertEqual(resp_view.status_code, 200)
        self.assertContains(resp_view, "Library Intelligence")

        resp_api = self.client.get(reverse('api_chart_data'))
        self.assertEqual(resp_api.status_code, 200)
        json_data = resp_api.json()
        self.assertEqual(json_data['status'], 'success')
        self.assertIn('circulation_trends', json_data)
