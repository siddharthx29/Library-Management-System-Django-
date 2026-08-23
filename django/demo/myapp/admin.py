from django.contrib import admin
from .models import Category, Book, Student, IssueBook, FineLedger


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'book_count')
    search_fields = ('code', 'name', 'description')
    ordering = ('code',)

    def book_count(self, obj):
        return obj.books.count()
    book_count.short_description = "Catalog Titles"


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'call_number', 'category', 'available_copies', 'quantity', 'shelf_location')
    list_filter = ('category', 'publication_year')
    search_fields = ('title', 'author', 'isbn', 'call_number', 'publisher')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('General Information', {
            'fields': ('title', 'author', 'category', 'description')
        }),
        ('Classification & Identifiers', {
            'fields': ('isbn', 'call_number', 'publisher', 'publication_year', 'edition')
        }),
        ('Inventory & Location', {
            'fields': ('quantity', 'available_copies', 'shelf_location')
        }),
        ('Audit Metadata', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        })
    )


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('patron_id', 'name', 'email', 'department', 'role', 'active_loans_count', 'is_active')
    list_filter = ('role', 'is_active', 'department')
    search_fields = ('patron_id', 'name', 'email', 'department')
    readonly_fields = ('created_at',)


@admin.register(IssueBook)
class IssueBookAdmin(admin.ModelAdmin):
    list_display = ('book', 'student', 'issue_date', 'due_date', 'return_date', 'status', 'renewal_count')
    list_filter = ('status', 'issue_date', 'due_date')
    search_fields = ('book__title', 'student__name', 'student__patron_id')
    raw_id_fields = ('book', 'student', 'issued_by')


@admin.register(FineLedger)
class FineLedgerAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'paid_amount', 'status', 'created_at', 'settled_at')
    list_filter = ('status', 'created_at')
    search_fields = ('student__name', 'student__patron_id', 'notes')
    raw_id_fields = ('issue', 'student', 'settled_by')
