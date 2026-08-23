from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.home, name='home'),

    # Catalog & Books
    path('catalog/', views.catalog_list_view, name='catalog_list'),
    path('catalog/<int:id>/', views.book_detail_view, name='book_detail'),
    path('catalog/add/', views.add_book, name='add_book'),
    path('catalog/edit/<int:id>/', views.edit_book, name='edit_book'),
    path('catalog/delete/<int:id>/', views.delete_book, name='delete_book'),

    # Backwards-compatibility routes for existing links
    path('add/', views.add_book),
    path('edit/<int:id>/', views.edit_book),
    path('delete/<int:id>/', views.delete_book),

    # Circulation Desk
    path('circulation/', views.loan_list_view, name='loan_list'),
    path('circulation/issue/', views.issue_book_view, name='issue_book'),
    path('circulation/return/<int:loan_id>/', views.return_book_view, name='return_book'),
    path('circulation/renew/<int:loan_id>/', views.renew_book_view, name='renew_book'),

    # Patrons & Members
    path('patrons/', views.patron_list_view, name='patron_list'),
    path('patrons/<int:id>/', views.patron_detail_view, name='patron_detail'),
    path('patrons/add/', views.patron_create_view, name='patron_create'),
    path('patrons/edit/<int:id>/', views.patron_edit_view, name='patron_edit'),

    # Financial / Fines
    path('fines/<int:fine_id>/settle/', views.settle_fine_view, name='settle_fine'),

    # Analytics & Intelligence
    path('analytics/', views.analytics_view, name='analytics'),
    path('api/analytics/data/', views.api_chart_data, name='api_chart_data'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
