from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from django.contrib.auth import authenticate, login

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import LoginForm


def home(request):
    return render(request, 'accounts/home.html') 

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('myapp:dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})



def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if user.user_type == 'vtc':
                    return redirect('vtc:dashboard')
                elif user.user_type == 'mm':
                    return redirect('mm:dashboard')
                elif user.user_type == 'aso':
                    return redirect('aso:dashboard')
                elif user.is_superuser:
                    return redirect('/admin/')
                else:
                    return redirect('accounts:home')
            else:
                form.add_error(None, 'Invalid username or password')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


from django.contrib.auth import logout
from django.shortcuts import redirect

def custom_logout_view(request):
    logout(request)  # Logs out the user
    return redirect('accounts:login')  # Redirects to login page (you can change this)


