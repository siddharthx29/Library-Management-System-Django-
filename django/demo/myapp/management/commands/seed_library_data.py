from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from myapp.models import Category, Book, Student, IssueBook, FineLedger


class Command(BaseCommand):
    help = 'Seeds realistic academic library catalog, patron registry, and circulation loan records.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding Athena Academic Library Platform dataset..."))

        # 1. Create Staff / Admin User
        admin_user, created = User.objects.get_or_create(
            username='librarian',
            defaults={
                'email': 'librarian@university.edu',
                'first_name': 'Dr. Margaret',
                'last_name': 'Sterling',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('AdminLibrary2026!')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created staff user: librarian (Password: AdminLibrary2026!)"))

        # 2. Categories
        categories_data = [
            ("004", "Computer Science & AI", "Algorithms, systems architecture, machine learning, and computational theory."),
            ("100", "Philosophy & Ethics", "Epistemology, moral philosophy, classical logic, and metaphysics."),
            ("330", "Economics & Social Sciences", "Macroeconomics, microeconomic theory, public policy, and sociology."),
            ("340", "Law & Jurisprudence", "Constitutional law, international treaties, and legal history."),
            ("510", "Pure Mathematics", "Algebra, real analysis, differential geometry, and topology."),
            ("530", "Physics & Astronomy", "Quantum mechanics, relativity, thermodynamics, and astrophysics."),
            ("610", "Medicine & Life Sciences", "Pathology, pharmacology, neurobiology, and clinical biochemistry."),
            ("800", "World Literature & Classics", "Ancient classics, comparative literature, drama, and critical theory."),
            ("900", "History & Archaeology", "Ancient Near East, medieval Europe, modern global history, and archives."),
        ]

        cat_map = {}
        for code, name, desc in categories_data:
            cat, _ = Category.objects.update_or_create(
                code=code,
                defaults={'name': name, 'description': desc}
            )
            cat_map[code] = cat

        # 3. Books
        books_data = [
            {
                "title": "Introduction to Algorithms",
                "author": "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, Clifford Stein",
                "isbn": "9780262033848",
                "call_number": "QA76.6 .C662 2009",
                "category": cat_map["004"],
                "publisher": "MIT Press",
                "publication_year": 2022,
                "edition": "4th Edition",
                "quantity": 6,
                "available_copies": 2,
                "shelf_location": "Science Wing, Stack 3A, Shelf 12",
                "description": "Comprehensive reference covering dynamic programming, graph algorithms, and asymptotic complexity analysis."
            },
            {
                "title": "Structure and Interpretation of Computer Programs",
                "author": "Harold Abelson, Gerald Jay Sussman, Julie Sussman",
                "isbn": "9780262510875",
                "call_number": "QA76.6 .A255 1996",
                "category": cat_map["004"],
                "publisher": "MIT Press",
                "publication_year": 1996,
                "edition": "2nd Edition",
                "quantity": 4,
                "available_copies": 1,
                "shelf_location": "Science Wing, Stack 3A, Shelf 14",
                "description": "Foundational text exploring abstraction barriers, meta-linguistic abstraction, and interpreter design."
            },
            {
                "title": "Deep Learning",
                "author": "Ian Goodfellow, Yoshua Bengio, Aaron Courville",
                "isbn": "9780262035613",
                "call_number": "Q325.5 .G66 2016",
                "category": cat_map["004"],
                "publisher": "MIT Press",
                "publication_year": 2016,
                "edition": "1st Edition",
                "quantity": 5,
                "available_copies": 0,
                "shelf_location": "Science Wing, Stack 3B, Shelf 02",
                "description": "Broad mathematical framework covering deep feedforward networks, convolutional architectures, and generative modeling."
            },
            {
                "title": "Computer Systems: A Programmer's Perspective",
                "author": "Randal E. Bryant, David R. O'Hallaron",
                "isbn": "9780134092669",
                "call_number": "QA76.5 .B795 2015",
                "category": cat_map["004"],
                "publisher": "Pearson",
                "publication_year": 2015,
                "edition": "3rd Edition",
                "quantity": 5,
                "available_copies": 3,
                "shelf_location": "Science Wing, Stack 3B, Shelf 08",
                "description": "Exploration of machine-level code execution, memory hierarchy, cache optimization, and virtual memory."
            },
            {
                "title": "Critique of Pure Reason",
                "author": "Immanuel Kant (Trans. Paul Guyer)",
                "isbn": "9780521657297",
                "call_number": "B2778.E5 G89 1998",
                "category": cat_map["100"],
                "publisher": "Cambridge University Press",
                "publication_year": 1998,
                "edition": "Cambridge Edition",
                "quantity": 3,
                "available_copies": 2,
                "shelf_location": "Humanities Tower, Stack 1A, Shelf 04",
                "description": "Milestone philosophical treatise examining synthetic a priori propositions and transcendental idealism."
            },
            {
                "title": "The Republic",
                "author": "Plato (Trans. Allan Bloom)",
                "isbn": "9780465069347",
                "call_number": "JC71 .P35 1991",
                "category": cat_map["100"],
                "publisher": "Basic Books",
                "publication_year": 1991,
                "edition": "2nd Edition",
                "quantity": 4,
                "available_copies": 3,
                "shelf_location": "Humanities Tower, Stack 1A, Shelf 09",
                "description": "Socratic dialogue concerning justice, philosopher kings, and the theory of forms."
            },
            {
                "title": "Principles of Mathematical Analysis",
                "author": "Walter Rudin",
                "isbn": "9780070542358",
                "call_number": "QA300 .R8 1976",
                "category": cat_map["510"],
                "publisher": "McGraw-Hill",
                "publication_year": 1976,
                "edition": "3rd Edition",
                "quantity": 4,
                "available_copies": 1,
                "shelf_location": "Science Wing, Stack 2A, Shelf 05",
                "description": "Rigorous treatment of metric spaces, sequences, continuity, Riemann-Stieltjes integration, and multivariable theory."
            },
            {
                "title": "Linear Algebra Done Right",
                "author": "Sheldon Axler",
                "isbn": "9783319110790",
                "call_number": "QA184.2 .A95 2015",
                "category": cat_map["510"],
                "publisher": "Springer",
                "publication_year": 2015,
                "edition": "3rd Edition",
                "quantity": 5,
                "available_copies": 2,
                "shelf_location": "Science Wing, Stack 2A, Shelf 11",
                "description": "Determinant-free approach to finite-dimensional vector spaces, linear operators, and spectral theory."
            },
            {
                "title": "The Feynman Lectures on Physics (Vol. 1-3)",
                "author": "Richard P. Feynman, Robert B. Leighton, Matthew Sands",
                "isbn": "9780465023820",
                "call_number": "QC21.2 .F49 2010",
                "category": cat_map["530"],
                "publisher": "Basic Books",
                "publication_year": 2010,
                "edition": "Millennium Edition",
                "quantity": 3,
                "available_copies": 1,
                "shelf_location": "Science Wing, Stack 2C, Shelf 01",
                "description": "Masterwork covering Newtonian mechanics, thermodynamics, electromagnetism, and quantum behavior."
            },
            {
                "title": "Capital in the Twenty-First Century",
                "author": "Thomas Piketty (Trans. Arthur Goldhammer)",
                "isbn": "9780674430006",
                "call_number": "HB501 .P43613 2014",
                "category": cat_map["330"],
                "publisher": "Belknap Press",
                "publication_year": 2014,
                "edition": "1st Edition",
                "quantity": 4,
                "available_copies": 2,
                "shelf_location": "Social Sciences Annex, Stack 4A, Shelf 03",
                "description": "Empirical historical study of wealth concentration and return on capital versus economic growth rates."
            },
            {
                "title": "The Odyssey",
                "author": "Homer (Trans. Emily Wilson)",
                "isbn": "9780393089059",
                "call_number": "PA4025.A5 W55 2017",
                "category": cat_map["800"],
                "publisher": "W. W. Norton & Company",
                "publication_year": 2017,
                "edition": "Critical Edition",
                "quantity": 4,
                "available_copies": 3,
                "shelf_location": "Humanities Tower, Stack 2B, Shelf 07",
                "description": "Critically acclaimed contemporary iambic pentameter translation of Homeric epic verse."
            },
            {
                "title": "Robbins & Cotran Pathologic Basis of Disease",
                "author": "Vinay Kumar, Abul K. Abbas, Jon C. Aster",
                "isbn": "9780323531139",
                "call_number": "RB111 .R62 2020",
                "category": cat_map["610"],
                "publisher": "Elsevier",
                "publication_year": 2020,
                "edition": "10th Edition",
                "quantity": 3,
                "available_copies": 0,
                "shelf_location": "Medical Stacks, Bay M1, Shelf 04",
                "description": "Comprehensive reference in human disease mechanisms, cellular injury, inflammation, and clinical pathology."
            },
        ]

        book_objs = []
        for bdata in books_data:
            book, _ = Book.objects.update_or_create(
                isbn=bdata["isbn"],
                defaults=bdata
            )
            book_objs.append(book)

        # 4. Patrons / Students
        patrons_data = [
            ("PAT-2026-0101", "Dr. Alistair Finch", "a.finch@university.edu", "+1 (555) 345-6789", "Computer Science", "FACULTY", 10),
            ("PAT-2026-0102", "Elena Rostova", "e.rostova@university.edu", "+1 (555) 456-7890", "Computer Science", "POSTGRADUATE", 8),
            ("PAT-2026-0103", "Marcus Sterling", "m.sterling@university.edu", "+1 (555) 567-8901", "Pure Mathematics", "UNDERGRADUATE", 5),
            ("PAT-2026-0104", "Sophia Chen", "s.chen@university.edu", "+1 (555) 678-9012", "Physics & Astronomy", "RESEARCHER", 8),
            ("PAT-2026-0105", "David K. Adebayo", "d.adebayo@university.edu", "+1 (555) 789-0123", "Economics & Law", "POSTGRADUATE", 6),
            ("PAT-2026-0106", "Chloe Montgomery", "c.montgomery@university.edu", "+1 (555) 890-1234", "Philosophy & Ethics", "UNDERGRADUATE", 5),
            ("PAT-2026-0107", "Dr. Julian Thorne", "j.thorne@university.edu", "+1 (555) 901-2345", "Medicine & Life Sciences", "FACULTY", 10),
            ("PAT-2026-0108", "Liam O'Connor", "l.oconnor@university.edu", "+1 (555) 012-3456", "World Literature", "UNDERGRADUATE", 5),
        ]

        patron_objs = []
        for pid, name, email, phone, dept, role, limit in patrons_data:
            patron, _ = Student.objects.update_or_create(
                email=email,
                defaults={
                    'patron_id': pid,
                    'name': name,
                    'phone': phone,
                    'department': dept,
                    'role': role,
                    'max_borrow_limit': limit,
                    'is_active': True,
                }
            )
            patron_objs.append(patron)

        # 5. Circulation Loans & Fines (Active, Overdue, and Historical)
        today = date.today()

        loans_to_create = [
            # Active normal loans
            (book_objs[0], patron_objs[1], today - timedelta(days=5), today + timedelta(days=9), None, 'ACTIVE', 0),
            (book_objs[1], patron_objs[0], today - timedelta(days=2), today + timedelta(days=12), None, 'ACTIVE', 0),
            (book_objs[3], patron_objs[2], today - timedelta(days=6), today + timedelta(days=8), None, 'ACTIVE', 1),
            (book_objs[6], patron_objs[3], today - timedelta(days=4), today + timedelta(days=10), None, 'ACTIVE', 0),

            # Overdue loans (Past due date)
            (book_objs[2], patron_objs[4], today - timedelta(days=20), today - timedelta(days=6), None, 'OVERDUE', 0),
            (book_objs[8], patron_objs[5], today - timedelta(days=25), today - timedelta(days=11), None, 'OVERDUE', 0),
            (book_objs[11], patron_objs[6], today - timedelta(days=18), today - timedelta(days=4), None, 'OVERDUE', 0),

            # Completed historical returns (Across past 4 months for trend charts)
            (book_objs[0], patron_objs[2], today - timedelta(days=90), today - timedelta(days=76), today - timedelta(days=75), 'RETURNED', 0),
            (book_objs[1], patron_objs[3], today - timedelta(days=85), today - timedelta(days=71), today - timedelta(days=70), 'RETURNED', 0),
            (book_objs[4], patron_objs[5], today - timedelta(days=60), today - timedelta(days=46), today - timedelta(days=45), 'RETURNED', 0),
            (book_objs[5], patron_objs[7], today - timedelta(days=55), today - timedelta(days=41), today - timedelta(days=40), 'RETURNED', 0),
            (book_objs[7], patron_objs[2], today - timedelta(days=35), today - timedelta(days=21), today - timedelta(days=20), 'RETURNED', 0),
            (book_objs[9], patron_objs[4], today - timedelta(days=30), today - timedelta(days=16), today - timedelta(days=15), 'RETURNED', 0),
            (book_objs[10], patron_objs[7], today - timedelta(days=22), today - timedelta(days=8), today - timedelta(days=7), 'RETURNED', 0),
        ]

        for book, patron, issue_d, due_d, ret_d, status, renewals in loans_to_create:
            loan, _ = IssueBook.objects.update_or_create(
                book=book,
                student=patron,
                issue_date=issue_d,
                defaults={
                    'due_date': due_d,
                    'return_date': ret_d,
                    'status': status,
                    'renewal_count': renewals,
                    'issued_by': admin_user,
                    'notes': "Issued via circulation desk terminal.",
                }
            )

            # Create fine ledger for overdue items
            if status == 'OVERDUE':
                overdue_days = (today - due_d).days
                fine_amount = Decimal(overdue_days) * Decimal('0.50')
                FineLedger.objects.update_or_create(
                    issue=loan,
                    student=patron,
                    defaults={
                        'amount': fine_amount,
                        'paid_amount': Decimal('0.00'),
                        'status': 'PENDING',
                        'notes': f"System assessed: {overdue_days} day(s) overdue at $0.50/day.",
                    }
                )

        # Historical Settled Fine
        paid_fine_loan = IssueBook.objects.filter(status='RETURNED').first()
        if paid_fine_loan:
            FineLedger.objects.get_or_create(
                issue=paid_fine_loan,
                student=paid_fine_loan.student,
                defaults={
                    'amount': Decimal('3.50'),
                    'paid_amount': Decimal('3.50'),
                    'status': 'PAID',
                    'settled_at': timezone.now() - timedelta(days=12),
                    'settled_by': admin_user,
                    'notes': "Late return fee settled at desk via receipt #RC-4091.",
                }
            )

        self.stdout.write(self.style.SUCCESS("Successfully seeded Athena Library Platform dataset!"))
