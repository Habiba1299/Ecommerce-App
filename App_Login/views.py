from django.shortcuts import render,HttpResponseRedirect,HttpResponse
from django.urls import reverse


# Authentication forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate


#forms 
from App_Login.models import Profile,User
from App_Login.forms import ProfileForm,SignUpForm


#Messages

from django.contrib import messages

# Create your views here.
def sign_up(request):
    form = SignUpForm

    if request.method == 'POST':
        form = SignUpForm(request.POST)

        if form.is_valid():
            form.save()
             # there are 4 type of messaged: info ,error,warning,success
            messages.success(request,"Account created successfully")
            return HttpResponseRedirect(reverse('App_Login:login'))
    dict={'form':form}
    return render(request,'App_Login/sign_up.html', context = dict)


def login_user(request):
    form = AuthenticationForm()

    if request.method == 'POST':
        form = AuthenticationForm(data = request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect(reverse('App_Shop:home'))
    dict={'form':form}
    return render(request,'App_Login/login.html', context = dict)

@login_required
def logout_user(request):
    logout(request)
    messages.warning(request,"You are logged out")
    return HttpResponseRedirect(reverse('App_Shop:home'))


@login_required
def user_profile(request):
    profile = Profile.objects.get(user = request.user)
    form = ProfileForm(instance = profile)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance = profile)

        if form.is_valid():
            form.save()
            # there are 4 type of messaged: info ,error,warning,success
            messages.success(request,"Changed Saved!!!!")
            form = ProfileForm(instance = profile)
    dict={'form':form}
    return render(request,'App_Login/change_profile.html', context = dict)
    





