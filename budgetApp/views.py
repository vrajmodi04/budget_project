from django.shortcuts import render, redirect
from .models import *
from django.db import IntegrityError
import os, random
from django.conf import settings
from django.core.mail import send_mail



default_data = {
    'no_header_pages': ['login_page', 'signup_page', 'forgot_password_page', 'otp_page'],
    'current_page': str(),
    'gender_choices': [],
}

for k,v in gender_choices:
    default_data['gender_choices'].append({'short_value': k, 'text': v})

# OTP Creation
def otp(request):
    otp_number = random.randint(1000, 9999)
    print("OTP is: ", otp_number)
    request.session['otp'] = otp_number

# send_otp
def send_otp(request, otp_for="register"):
    print(otp_for)
    otp(request)

    email_to_list = [request.session['reg_data']['email'],]

    if otp_for == 'activate':
        request.session['otp_for'] = 'activate'
        subject = f'OTP for Budget System Activation'
    elif otp_for == 'recover_pwd':
        request.session['otp_for'] = 'recover_pwd'
        subject = f'OTP for Password Recovery Budget System'
    else:
        request.session['otp_for'] = 'register'
        subject = f'OTP for Budget System Registration'

    email_from = settings.EMAIL_HOST_USER

    message = f"Your One Time Password for verification is: {request.session['otp']}."

    send_mail(subject, message, email_from, email_to_list)

    # alert('success', 'An OTP has sent to your email.')

# verify otp
def verify_otp(request, verify_for="register"):

    if request.session['otp'] == int(request.POST['otp']):

        if verify_for == 'activate':
            master = Master.objects.get(Email=request.session['reg_data']['email'])
            master.Password = request.session['reg_data']['password']
            master.IsActive = True
            master.save()


            return redirect(profile_page)
        elif verify_for == 'recover_pwd':
            print('recover verify', request.session['reg_data'])
            master = Master.objects.get(
                Email=request.session['reg_data']['email'],
            )
            master.Password = Password=request.session['reg_data']['password']
            
            master.save()
        else:
            print('before new account')
            master = Master.objects.create(
                Email = request.session['reg_data']['email'],
                Password = request.session['reg_data']['password'],
                IsActive = True,
            )
            UserProfile.objects.create(Master=master)
            print('after new account')

        print("verified.")
        # alert('success', 'An OTP verified.')

    else:
        print("Invalid OTP")
        
        # alert('danger', 'Invalid OTP')

        return redirect(otp_page)

    del request.session['reg_data']
    
    return redirect(login_page)


# Create your views here.
def index(request):
    return render(request, 'index.html')

def login_page(request):
    default_data['current_page'] = 'login_page'
    return render(request, 'login_page.html', default_data)

def signup_page(request):
    default_data['current_page'] = 'signup_page'
    return render(request, 'signup_page.html', default_data)

def forgot_password_page(request):
    default_data['current_page'] = 'forgot_password_page'
    return render(request, 'forgot_password_page.html', default_data)

def otp_page(request):
    default_data['current_page'] = 'otp_page'
    return render(request, 'otp_page.html', default_data)

def profile_page(request):
    default_data['current_page'] = 'profile_page'
    if 'email' in request.session:
        profile_data(request) # call profile_data function to load profile data on login success/update.

        return render(request, 'profile_page.html', default_data)
    
    return redirect(login_page)

# load profile data
def profile_data(request):
    master = Master.objects.get(Email = request.session['email'])
    profile = UserProfile.objects.get(Master = master)
    profile.BirthDate = profile.BirthDate.strftime("%Y-%m-%d")
    default_data['profile_data'] = profile

# signup functionality
def signup(request):
    try:
        request.session['reg_data'] = {
             'email':request.POST['email'],
             'password':request.POST['password'],
        }  

        send_otp(request) #send an otp 
        return redirect(otp_page)
    except IntegrityError as err:
        print('email already exists.')
    
    return redirect(signup_page)

#forget password functionality
def forget_password(request):
    request.session['reg_data'] = {
        'email':request.POST['email'],
        'password':request.POST['password'],
    }

    send_otp(request, 'recover_pwd') #send an otp

    return redirect(otp_page)

# login functionality
def login(request):
    try:
        master = Master.objects.get(Email = request.POST['email'])
        if master.Password == request.POST['password']:
            if master.IsActive:
                request.session['email'] = master.Email

                print('login success')
                return redirect(profile_page)
            else:
                print('your account is deactivated')
                request.session['reg_data'] = {
                    'email':request.POST['email'],
                    'password':request.POST['password'],
                }
                send_otp(request, 'activate')
                return redirect(otp_page)
        else:
            print('Incorrect password')
    except Master.DoesNotExist as err:
        print('Email not registered.')
    
    return redirect(login_page)

image_path = os.path.join(settings.MEDIA_ROOT, 'user_profiles')

# profile image upload
def profile_image_upload(request):
    master = Master.objects.get(Email = request.session['email'])
    profile = UserProfile.objects.get(Master = master)

    if 'profile_image' in request.FILES:
        file = request.FILES['profile_image']
        print(type(file))
        print(type(file.name))
        file_type = file.name.split('.')[-1]
        new_name = f"{profile.id}_{profile.UserName}.{file_type}"
        file.name = new_name
        print(type(file.name))

        for f in os.scandir(image_path):
            if f.name == file.name:
                os.unlink(f"{image_path}\\{file.name}")

        profile.ProfileImage = file

    profile.save()

    return redirect(profile_page)

# profile update functionality
def profile_update(request):
    master = Master.objects.get(Email = request.session['email'])

    profile = UserProfile.objects.get(Master = master)

    profile.FullName = request.POST['full_name']
    profile.Gender = request.POST['gender']
    profile.BirthDate = request.POST['birth_date']
    profile.Address = request.POST['address']

    profile.save()

    print("profile updated successfully")

    return redirect(profile_page)

#add budget


# logout functionality
def logout(request):
    if 'email' in request.session:
        del request.session['email']
    
    return redirect(login_page)