from django.shortcuts import render, redirect, get_object_or_404
from .models import Book


def home(request):
    books = Book.objects.all()
    return render(request, 'lms/home.html', {'books': books})

def add_book(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        author = request.POST.get('author')
        quantity = request.POST.get('quantity')

        # Validate quantity
        if quantity.isdigit():
            quantity = int(quantity)
            Book.objects.create(title=title, author=author, quantity=quantity)
            return redirect('home')  
        else:
            error = "Quantity must be a number."
            return render(request, 'lms/add_book.html', {'error': error})

    return render(request, 'lms/add_book.html')



def edit_book(request, id):
    book = get_object_or_404(Book, id=id)

    if request.method == "POST":
        book.title = request.POST.get('title')
        book.author = request.POST.get('author')
        book.quantity = request.POST.get('quantity')
        book.save()
        return redirect('home')

    else:
        return render(request, 'lms/edit_book.html', {'book': book})

  

def delete_book(request, id):
    book = get_object_or_404(Book, id=id)
    book.delete()
    return redirect('home')

