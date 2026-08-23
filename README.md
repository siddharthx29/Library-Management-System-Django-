# 🏛️ Athena — Academic Library Operations & Intelligence Platform

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.2+-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Security: Audited](https://img.shields.io/badge/security-audited-brightgreen.svg)](SECURITY.md)

**Athena** is a human-designed, enterprise-grade **Library Operations & Intelligence Platform** crafted for university libraries, research institutes, and academic centers. Inspired by premier research institutions, Athena blends scholarly cataloguing taxonomies with high-velocity circulation workflows, atomic inventory tracking, and strategic collection intelligence.

---

## 🌟 Core Highlights & Capabilities

### 1. 📖 Scholarly Catalog & Holdings Management
* **Academic Taxonomies**: Categorized by Dewey / Library of Congress inspired subject classes (Pure Mathematics, Computer Science, Jurisprudence, Philosophy, Life Sciences).
* **Archival Identification**: Full metadata tracking with ISBN-10/13 normalization, shelf call numbers (e.g. `QA76.73 .P98`), edition, imprint, and physical stack coordinates.
* **Instant Search & Multi-Param Filtering**: Search across title, author, ISBN, call number, publisher, or subject classification with real-time stock filters.

### 2. 🔄 High-Velocity Circulation Desk & Concurrency Protection
* **Atomic Transactions**: Concurrency-safe loan checkouts, renewals, and returns using `transaction.atomic()` with row-level locks (`select_for_update()`).
* **Active Borrowing Quotas**: Automatic validation of patron loan limits, active privileges, and duplicate holding checks.
* **Overdue Tracking & Fine Computation**: Automatic assessment of late return fines ($0.50/day policy) with integrated settlement/waiver ledgers.

### 3. 📈 Strategic Collection Intelligence & Analytics
Athena provides data visualization answering actionable library management questions:
* **"When are books being borrowed?"** → 6-month rolling circulation velocity line chart.
* **"What is being borrowed?"** → Subject area and discipline distribution breakdown.
* **"What should we buy more of?"** → Automated Acquisition Priority Matrix identifying high-demand titles with depleted shelf availability.
* **"Where is library usage strongest?"** → Academic department and institutional role engagement breakdown.
* **"Who are our most active scholars?"** → Patron circulation ranking and compliance records.

### 4. 🎨 Bespoke Editorial Design System
* **Academic Personality**: Deep Oxford Navy (`#0F1E36`), Parchment Linen (`#F9F8F5`), Warm Slate (`#334155`), and Cambridge Bronze accents.
* **Typography Pairing**: *Newsreader* (editorial academic serif for headings and bibliographic records) + *Plus Jakarta Sans* (crisp, readable body & tabular data) + *JetBrains Mono* (call numbers and ISBNs).
* **Respectful Micro-Interactions**: Restrained row hover feedback, interactive modal dialogs, status badges, and `prefers-reduced-motion` compliance.

---

## 🏗️ Architecture & Technology Stack

* **Backend Engine**: Python 3.11+ / Django 5.2 (Clean Architecture with Service Layer separation).
* **Database**: SQLite (Local Dev) / PostgreSQL (Production-Ready via ORM).
* **Services**:
  * `CirculationService`: Encapsulates atomic checkout, checkin, renewals, and fine settlements.
  * `AnalyticsService`: Encapsulates aggregate queries, KPIs, trends, and collection recommendations.
* **Frontend**: Semantic HTML5, Vanilla CSS Design System, Responsive App Shell, and Chart.js.
* **Security**: Parameterized ORM queries, CSRF enforcement, strict ModelForm validation, and security headers (`X-Frame-Options: DENY`, `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_BROWSER_XSS_FILTER`).

```
django/demo/
├── .env.example              # Environment variables template
├── SECURITY.md               # Security policy & disclosure guide
├── manage.py
├── demo/
│   ├── settings.py           # Dotenv configuration & security headers
│   ├── urls.py               # Root URL router
│   └── wsgi.py
├── myapp/
│   ├── models.py             # Category, Book, Student, IssueBook, FineLedger
│   ├── forms.py              # Strict ModelForms and input validators
│   ├── views.py              # Catalog, circulation, patron & analytics views
│   ├── urls.py               # Application endpoints
│   ├── services/
│   │   ├── circulation_service.py # Atomic transactions & concurrency control
│   │   └── analytics_service.py   # Aggregation & recommendation algorithms
│   ├── management/commands/
│   │   └── seed_library_data.py   # Rich academic seed dataset
│   ├── static/lms/
│   │   ├── css/style.css     # Bespoke academic design system
│   │   └── js/main.js        # Modals, alerts, and Chart.js integration
│   ├── templates/lms/        # Base layout, dashboard, catalog, circulation
│   └── tests/                # Automated test suite (25 test cases)
```

---

## 🚀 Quickstart & Installation

### 1. Clone & Set Up Environment
```bash
cd django/demo
python -m venv venv

# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
cp ../../.env.example .env
```

### 3. Run Database Migrations
```bash
python manage.py migrate
```

### 4. Seed Academic Demo Dataset
Populates scholarly categories, textbook titles, patron accounts, and historical circulation records:
```bash
python manage.py seed_library_data
```
> **Default Staff Account**:
> * **Username**: `librarian`
> * **Password**: `AdminLibrary2026!`

### 5. Launch Development Server
```bash
python manage.py runserver
```
Visit **`http://127.0.0.1:8000/`** to access the dashboard.

---

## 🧪 Automated Testing

Athena includes a comprehensive automated test suite covering models, atomic services, form sanitization, analytics computations, and view integrations.

Run all tests:
```bash
python manage.py test myapp.tests
```

---

## 🔒 Security & Defensive Engineering

* **Environment Isolation**: Secrets are loaded via `.env` and never committed to source control.
* **SQL Injection Immunity**: Zero raw string concatenation; all queries utilize Django's parameterized ORM with `select_for_update` row locks.
* **XSS Defense**: Strict HTML escaping, form input sanitization, and structured serialization.
* **CSRF Protection**: All state-modifying requests require valid CSRF tokens.
* **Security Headers**: Standard defense-in-depth headers configured in `settings.py`.

For vulnerability disclosure, please refer to [SECURITY.md](SECURITY.md).

---

## 📄 License
Released under the [MIT License](LICENSE).
