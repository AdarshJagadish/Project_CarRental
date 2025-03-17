from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

# Register
def register(request):
    if request.user.is_authenticated:
        return redirect('userhome')  # Redirect if the user is already logged in
        
    if request.method == 'POST':
        username = request.POST['username'].strip()
        email = request.POST['email'].strip()
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('register')

        if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
            messages.error(request, "Username or Email already taken!")
            return redirect('register')

        try:
            User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, "Account created! Please log in.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
            return redirect('register')

    return render(request, 'user/register.html')


# Login
def userlogin(request):
    if request.user.is_authenticated:
        return redirect('userhome')  # Redirect if already logged in
    
    if request.method == 'POST':
        email = request.POST['email'].strip()
        password = request.POST['password']

        user_obj = User.objects.filter(email=email).first()
        if user_obj:
            user = authenticate(request, username=user_obj.username, password=password)
            if user:
                login(request, user)
                return redirect('userhome')

        messages.error(request, "Invalid email or password!")
        return redirect('login')

    return render(request, 'user/login.html')


# Logout
def userlogout(request):
    logout(request)
    return redirect('login')


# Home
def userhome(request):
    return render(request,'home.html', {'username': request.user.username})
