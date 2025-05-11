from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate,login,logout
from .models import *
import csv
from django.http import HttpResponse
import os
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from datetime import datetime
import razorpay
from decimal import Decimal, InvalidOperation,ROUND_HALF_UP
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
def carhub_login(req):
    if 'admin' in req.session:
        return redirect(admin_home)
    else:
        if req.method == 'POST':
            uname = req.POST.get('uname') or req.POST.get('email') or req.POST.get('username')
            password = req.POST.get('password')

            data = authenticate(username=uname, password=password)
            if data:
                login(req, data)
                if data.is_superuser:
                    req.session['admin'] = uname
                    return redirect(admin_home)
                else:
                    req.session['user'] = uname
                    return redirect(carhub_home)
            else:
                messages.warning(req, 'Invalid username or password')
                return redirect(carhub_login)

    return render(req, 'login.html')


def carhub_logout(req):
    logout(req)
    req.session.flush()
    return redirect(carhub_login)

def register(req):
    if req.method == 'POST':
        name = req.POST['name']
        email = req.POST['email']
        password = req.POST['password']
        
        try:
            validate_password(password)
            
            
            if User.objects.filter(email=email).exists():
                messages.warning(req, 'User with this email already exists.')
                return redirect(register)

            
            user = User.objects.create_user(first_name=name, username=email, email=email, password=password)
            user.save()

            
            send_mail(
                'Account Registration',
                'Your carhub account registration was successful.',
                settings.EMAIL_HOST_USER,
                [email]
            )

            messages.success(req, 'Registration successful. Please log in.')
            return redirect(carhub_login)

        except ValidationError as e:
            messages.error(req, ', '.join(e)) 
            return redirect(register)
        
    return render(req, 'register.html')


def mark_full_paid(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id)

    if rental.is_full_paid:
        messages.info(request, "This rental is already marked as fully paid.")
    else:
        rental.is_full_paid = True
        rental.balance_due = 0
        rental.save()
        messages.success(request, f"{rental.user.username}'s rental marked as fully paid.")

    return redirect("manage_rentals")


def manage_rentals(request):
    status = request.GET.get("status")
    if status:
        rentals = Rental.objects.filter(status=status).order_by("-id")
    else:
        rentals = Rental.objects.all().order_by("-id")
    return render(request, "admin/manage_rentals.html", {"rentals": rentals})



# --------admin-----------------------
def admin_home(req):
    if 'admin' in req.session:
        car=Car.objects.all()
        return render(req,'admin/admin_home.html',{'cars':car})
    else:
        return render(carhub_login)

def add_car(req):
    if 'admin' in req.session:
        if req.method=='POST':
            name=req.POST['name']
            brand=req.POST['brand']
            fuel=req.POST['fuel']
            categoryy=req.POST['category']
            seats=req.POST['num_of_seats']
            price=req.POST['price_per_day']
            status = req.POST.get('is_available') == 'on'
            file=req.FILES['image']
            data=Car.objects.create(name=name,brand=brand,image=file,fuel=fuel,category=Category.objects.get(category=categoryy),
                                    num_of_seats=seats,price_per_day=price,
                                    is_available=status
                                    )
            data.save()
        else:
            data=Category.objects.all()
            return render(req,'admin/add_car.html',{'data':data})
    return render(req,'admin/add_car.html')

def edit_car(req, id):
    if req.method == 'POST':
        name = req.POST['name']
        brand = req.POST['brand']
        img = req.FILES.get('image') 
        fuel = req.POST['fuel']
        seats = req.POST['num_of_seats']
        price = req.POST['price_per_day']
        status = req.POST.get('is_available') == 'on'

        if img:
            Car.objects.filter(pk=id).update(
                name=name, brand=brand, image=img, fuel=fuel,
                num_of_seats=seats, price_per_day=price,
                is_available=status
            )
            data = Car.objects.get(pk=id)
            data.image = img
            data.save()
        else:
            Car.objects.filter(pk=id).update(
                name=name, brand=brand, fuel=fuel,
                num_of_seats=seats, price_per_day=price,
                is_available=status
            )

        return redirect(admin_home)
    else:
        data = Car.objects.get(pk=id)
        return render(req, 'admin/edit_car.html', {'data': data})


def delete_car(req,id):
    data=Car.objects.get(pk=id)
    url=data.image.url
    url=url.split('/')[-1]
    os.remove('media/'+url)
    data.delete()
    return redirect(admin_home)

def delete_category(req,id):
    data=Category.objects.get(pk=id)
    data.delete()
    return redirect(add_category)

def add_category(req):
    if 'admin' in req.session:
        if req.method == 'POST':
            category=req.POST['category']
            data=Category.objects.create(category=category)
            data.save()
            return redirect(add_category)
        else:
            data=Category.objects.all()
            return render(req,'admin/add_category.html',{'data':data})
    else:
         return redirect(carhub_home)

def view_cat(req,id):
    category = Category.objects.get(pk=id)
    car = Car.objects.filter(category=category)
    return render(req, 'admin/view_cat.html', {'category': category,'car': car})

def manage_rentals(request):
    rentals = Rental.objects.all().order_by("-id")
    return render(request, "admin/manage_rentals.html", {"rentals": rentals})

def update_rental_status(request, rental_id, status):
    rental = get_object_or_404(Rental, id=rental_id)

    if status in ["Approved", "Rejected", "Completed"]:
        rental.status = status
        rental.save()
        
        if status == "Approved":
            subject = "Your Car Rental Request Has Been Approved!"
            message = f"Hello {rental.user.username},\n\nYour car rental request for {rental.car.name} has been approved.\n\nStart Date: {rental.start_date}\nEnd Date: {rental.end_date}\nTotal Price: ₹{rental.total_price}\n\nThank you for using our service!\n\nBest Regards,\nDrive Your Way! \ncarhub Rental Team"
            recipient_email = rental.user.email
            sender_email = settings.EMAIL_HOST_USER

            send_mail(subject, message, sender_email, [recipient_email])

        elif status == "Rejected":
            subject = "Your Car Rental Has Been Rejected!"
            message = f"Hello {rental.user.username},\n\nSORRY....!!!  Your car rental for {rental.car.name} has been Rejected.\n\nStart Date: {rental.start_date}\nEnd Date: {rental.end_date}\nTotal Price: ₹{rental.total_price}\n\nThank you for using our service!\n\nBest Regards,\nDrive Your Way! \ncarhub Rental Team"
            recipient_email = rental.user.email
            sender_email = settings.EMAIL_HOST_USER

            send_mail(subject, message, sender_email, [recipient_email])

        elif status == "Completed":
            subject = "Your Car Rental Has Been Completed!"
            message = f"Hello {rental.user.username},\n\nYour car rental for {rental.car.name} has been Completed.\n\nStart Date: {rental.start_date}\nEnd Date: {rental.end_date}\nTotal Price: ₹{rental.total_price}\n\nThank you for using our service!\n\nBest Regards,\nDrive Your Way! \ncarhub Rental Team"
            recipient_email = rental.user.email
            sender_email = settings.EMAIL_HOST_USER

            send_mail(subject, message, sender_email, [recipient_email]) 

        messages.success(request, f"Rental status updated to {status}")
    else:
        messages.error(request, "Invalid status update")

    return redirect("manage_rentals")

def mark_full_paid(request, rental_id):
    if not request.session.get("admin"):
        return redirect(carhub_home)

    rental = get_object_or_404(Rental, id=rental_id)
    rental.is_full_paid = True
    rental.balance_due = 0
    rental.save()
    messages.success(request, f"Marked rental #{rental.id} as fully paid.")
    return redirect("manage_rentals")


def export_rentals_csv(request):
    if not request.session.get("admin"):
        return redirect(carhub_home)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="rentals.csv"'

    writer = csv.writer(response)
    writer.writerow(['Rental ID', 'User', 'Car', 'Start Date', 'End Date', 'Status', 'Total Price', 'Paid'])

    rentals = Rental.objects.all().order_by('-id')
    for r in rentals:
        writer.writerow([
            r.id,
            r.user.username,
            r.car.name,
            r.start_date,
            r.end_date,
            r.status,
            r.total_price,
            'Yes' if r.is_full_paid else 'No'
        ])

    return response

# --------------user-----------------------
def carhub_home(req):
    if 'admin' in req.session:
        return redirect(admin_home)
    else:
        data=Car.objects.all()
        cat=Category.objects.all()
        return render(req,'user/user_home.html',{'data':data,"cat":cat})    

def view_car(req,id):
    data=Car.objects.get(pk=id)
    cat=Category.objects.all()
    return render(req,'user/view_car.html',{'data':data,"cat":cat})


def contact(req):
    cat=Category.objects.all()
    if req.method == "POST":
        name = req.POST["name"]
        email = req.POST["email"]
        message = req.POST["message"]

        send_mail(
            subject=f"New Contact Form Submission from {name}",
            message=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}",
            from_email=email,
            recipient_list=["contact.adarshjagadish@gmail.com"], 
            fail_silently=True,
        )

        messages.success(req, "Your message has been sent successfully!")
        return redirect(contact )  
    return render(req,'user/contact.html',{"cat":cat})

def rent_car(request, id):
    cat=Category.objects.all()
    car = get_object_or_404(Car, pk=id)

    if not car.is_available:
        messages.error(request, "Sorry, this car is not available for rent.")
        return redirect(view_car, id=car.pk)

    if request.method == "POST":
        start_date_str = request.POST.get("start_date")
        end_date_str = request.POST.get("end_date")

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            if start_date >= end_date:
                messages.error(request, "End date must be after start date.")
                return redirect(rent_car, id=car.pk)

            existing_rental = Rental.objects.filter(
                car=car,
                start_date__lte=end_date,
                end_date__gte=start_date,
                status__in=["Pending", "Approved"]
            ).exists()

            if existing_rental:
                messages.error(request, "This car is already booked for the selected dates.")
                return redirect(rent_car, id=car.pk)

            num_days = (end_date - start_date).days
            total_price = num_days * car.price_per_day

            rental = Rental.objects.create(
                user=request.user,
                car=car,
                start_date=start_date,
                end_date=end_date,
                num_days=num_days,
                total_price=total_price,
                status="Pending",  
            )

            messages.success(request, "Rental request submitted successfully!")
            return redirect(rent_car, id=car.pk)

    return render(request, "user/rent_car.html", {"car": car,"cat":cat})

def cancel_rental(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id, user=request.user)
    
    if rental.status in ["Pending", "Approved"]:
        rental.status = "Cancelled"
        rental.save()

        # Email notification
        subject = "Your Car Rental Has Been Cancelled"
        message = (
            f"Hello {rental.user.username},\n\n"
            f"Your rental for {rental.car.name} has been successfully cancelled.\n\n"
            f"Start Date: {rental.start_date}\n"
            f"End Date: {rental.end_date}\n"
            f"Total Price: ₹{rental.total_price}\n\n"
            f"Thank you for using CarHub!\n\n"
            f"Best Regards,\nCarHub Rentals Team"
        )
        send_mail(subject, message, settings.EMAIL_HOST_USER, [rental.user.email])

        messages.success(request, "Rental cancelled successfully.")
    else:
        messages.warning(request, "This rental cannot be cancelled.")

    return redirect("user_profile")

def view_category(req,id):
    category = Category.objects.get(pk=id)
    cat=Category.objects.all()
    car = Car.objects.filter(category=category)
    return render(req, 'user/category.html', {'category': category,'car': car,"cat":cat})

def user_profile(req):
    rentals = Rental.objects.filter(user=req.user).order_by("-id")
    cat = Category.objects.all()

    booking_sections = [
        {'label': 'Ongoing Rides', 'group': rentals.filter(status='Approved', is_full_paid=False)},
        {'label': 'Pending Requests', 'group': rentals.filter(status='Pending')},
        {'label': 'Completed Trips', 'group': rentals.filter(status='Completed')},
        {'label': 'Rejected Requests', 'group': rentals.filter(status='Rejected')},
        {'label': 'Cancelled Bookings', 'group': rentals.filter(status='Cancelled')},
    ]

    return render(req, 'user/user_profile.html', {
        'cat': cat,
        'rentals': rentals,
        'booking_sections': booking_sections
    })


# -----------------------------------------Payment------------------------------------------------------

def create_razorpay_order(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id)
    advance_amount = rental.total_price * Decimal('0.2')  # 20% advance
    amount_paise = int(advance_amount * 100)  # Razorpay needs paise as int

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    # Create Razorpay order
    order_data = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": f"receipt_{rental_id}",
        "payment_capture": 1,
    }
    order = client.order.create(data=order_data)

    context = {
        "rental": rental,
        "car": rental.car,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "order_id": order["id"],
        "amount": int(advance_amount),  # For display (₹)
        "amount_paise": amount_paise,   # For Razorpay JS
        "total_price": rental.total_price,
        "advance_amount": advance_amount,
        "order_receipt": order.get("receipt", ""),
        "order_status": order.get("status", ""),
        "user_email": request.user.email,
        "user_name": request.user.get_full_name(),
    }

    return render(request, "user/payment.html", context)

    
def create_balance_order(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id)

    # Ensure advance is paid and full payment not done
    if not rental.is_advance_paid or rental.is_full_paid:
        return redirect("user_profile")

    balance_amount = rental.remaining_amount
    balance_amount = balance_amount.quantize(Decimal('0.01'))  # Ensure precision
    amount_paise = int(balance_amount * 100)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    order_data = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": f"balance_{rental_id}",
        "payment_capture": 1,
    }

    order = client.order.create(data=order_data)

    # Store balance amount and order ID to validate later
    rental.balance_due = balance_amount  # You can add this field to your model
    rental.balance_order_id = order["id"]  # Add this if you'd like to track it
    rental.save()

    context = {
        "rental": rental,
        "car": rental.car,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "order_id": order["id"],
        "amount": int(balance_amount),
        "total_price": rental.total_price,
        "advance_paid": rental.advance_paid,
        "balance_amount": balance_amount,
        "order_receipt": order.get("receipt", ""),
        "order_status": order.get("status", ""),
        "user_email": request.user.email,
        "user_name": request.user.get_full_name(),
    }

    return render(request, "user/pay_balance.html", context)


@csrf_exempt
def razorpay_success(request):
    if request.method == "POST":
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        rental_id = request.POST.get('rental_id')

        try:
            rental = Rental.objects.get(id=rental_id)
        except Rental.DoesNotExist:
            messages.error(request, "Rental record not found.")
            return redirect('user_profile')

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            payment = client.payment.fetch(razorpay_payment_id)
            amount_paid = Decimal(payment['amount']) / 100  # Razorpay returns amount in paise
        except Exception as e:
            messages.error(request, "Failed to fetch payment details.")
            return redirect('user_profile')

        user = rental.user
        car = rental.car

        expected_advance = quantize_to_rupees(rental.total_price * Decimal('0.2'))
        expected_balance = quantize_to_rupees(rental.total_price - rental.advance_paid)

        if not rental.is_advance_paid and amount_paid == expected_advance:
            rental.advance_paid = amount_paid
            rental.is_advance_paid = True
            rental.razorpay_order_id = razorpay_order_id
            rental.save()

            messages.success(request, "Advance payment successful!")
            # send email ...

        elif rental.is_advance_paid and not rental.is_full_paid and amount_paid == expected_balance:
            rental.balance_paid = amount_paid
            rental.is_full_paid = True
            rental.razorpay_balance_order_id = razorpay_order_id
            rental.save()

            messages.success(request, "Balance payment successful!")
            # send email ...

        else:
            messages.error(request, "Payment amount does not match expected amount.")
            return redirect("user_profile")

        return redirect("user_profile")

# Utility function to round off to 2 decimal places
def quantize_to_rupees(amount):
    return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
