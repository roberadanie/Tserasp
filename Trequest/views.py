from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
#from Tserasp import Trequest
from sys import path_hooks
from django.contrib import messages
from django.core.validators import ProhibitNullCharactersValidator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import *
from django.contrib.auth.forms import PasswordChangeForm
from Trequest.forms import *
from django.core.mail import send_mail
import random
import string
from django.http.response import JsonResponse
import datetime
from django.db.models import Q
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.views.generic import ListView
from .decorators import unauthenticated_user,allowed_users
from MaterialApp.models import Material, MaterialRequest



class Requestpdf(ListView):
    model = TransportRequest
    template_name = 'Trequest/pdf.html'

@login_required(login_url='login')
@allowed_users(allowed_roles=['TSHO'])
def request_pdf(request, *args, **kwargs):
    pk = kwargs.get('pk')
    requestpdf = get_object_or_404(TransportRequest, pk=pk)
    template_path = 'Trequest/pdf.html'
    context = {'requestpdf': requestpdf}
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    # If download:
    #response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    # if display:
    response['Content-Disposition'] = 'filename="report.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
        html, dest=response)
    # if error then show some funy view
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

# registered users can login in to the system

@unauthenticated_user
def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.info(request, 'Incorrect username or password!')

    return render(request, 'Trequest/login.html')

# creating account for the users
@login_required(login_url='login')
def create_account(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            username = 'tserasp'.join(random.choice(
                string.ascii_uppercase + string.digits) for x in range(2))
            instance = user_form.save(commit=False)
            instance.username = username
            instance.save()
            role = user_form.cleaned_data.get('role')
            if role == 'Driver':
                Driver.objects.create(user=instance)
            messages.success(request, 'Account Created Successfully!')
            return redirect('account')
    else:
        user_form = UserRegistrationForm()
    context = {'user_form': user_form}
    return render(request, 'Trequest/register.html', context)

# AJAX

@login_required(login_url='login')
def load_department(request):
    school_id = request.GET.get('school_id')
    departments = Department.objects.filter(
        school_id=school_id).order_by('name')
    context = {'departments': departments}
    return render(request, 'Trequest/department_dropdown_list_options.html', context)
    # print(list(departments.values('id','name')))
    # return JsonResponse(list(departments.values('id', 'name')), safe=False)

# editing/updating user account

@login_required(login_url='login')
def edit_account(request):
    if request.method == 'POST':
        a_form = UserAccountEditForm(request.POST, instance=request.user)
        p_form = UserProfileEditForm(
            request.POST, instance=request.user.passenger)
        if a_form.is_valid() and p_form.is_valid():
            a_form.save()
            p_form.save()
            messages.success(request, 'Profile updated Successfully!')
            return redirect('profile')

    else:
        a_form = UserAccountEditForm(instance=request.user)
        p_form = UserProfileEditForm(instance=request.user.passenger)

    context = {'a_form': a_form, 'p_form': p_form}
    return render(request, 'Trequest/edit_account.html', context)


def user_logout(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password Changed successfully')
            return redirect('change-password')
    else:
        form = PasswordChangeForm(request.user)
    context = {'form': form}
    return render(request, 'Trequest/change_password.html', context)


@login_required(login_url='login')
def index(request):
    schedule = Schedule.objects.all().order_by('-date')
    total_user = MyUser.objects.all()
    total_feedback=Feedback.objects.all().count()
    tsho_pending_request = TransportRequest.objects.filter(
        status='Pending', status2='Approved', status3='Approved')
    dep_pending_request = TransportRequest.objects.filter(status2='Pending',
                                                          passenger__department=request.user.department).exclude(passenger__role="DepartmentHead")
    sch_pending_request = TransportRequest.objects.filter(status3='Pending', status2='Approved',
                                                          passenger__school=request.user.school).exclude(passenger__role="SchoolDean")
    app = total_user.count()
    tsho_pend = tsho_pending_request.count()
    dep_pend = dep_pending_request.count()
    sch_pend = sch_pending_request.count()
    vehicle = Vehicle.objects.all()
    vehicle_count = vehicle.count()

#   to expire transport request
    transport = TransportRequest.objects.filter(Q(status="Pending") or Q(status2="Pending") or Q(status3="Pending"))
    for req in transport:
        exp=req.start_date
        if date.today()>= exp:
            TransportRequest.objects.filter(Q(status="Pending") or Q(status2="Pending") or Q(status3="Pending")).update(status='Expired',status2='Expired',status3='Expired')
    # print(transport)  

    # storeman material report
    material = Material.objects.all()
    material_request=MaterialRequest.objects.all()
# list of vehicle type 
    vehicle = Vehicle.objects.all().values_list('vehicle_type__name')
#create a set(since it always contain unique data) 
    ab={}
    # print(type(ab))
    for vehicle_type in vehicle:
        if vehicle_type in ab:
            ab[vehicle_type]+=1
        else:
            ab[vehicle_type]=1
    x=ab.keys()
    y=ab.values()

    context = {'schedule': schedule,
               'vehicle_count': vehicle_count,
               'app': app,
               'tsho_pend': tsho_pend,
               'dep_pend': dep_pend,
               'sch_pend': sch_pend,
               'feedback_count':total_feedback,
               'material':material,
               'x':x,
               'y':y,
               'material_request':material_request

               }
    return render(request, 'Trequest/index.html', context)


@login_required(login_url='login')
def view_request(request):
    return render(request, 'Trequest/view_request.html')


@login_required(login_url='login')
@allowed_users(allowed_roles=['TSHO'])
def vehicle_management(request):
    vehicle = Vehicle.objects.all()
    query = request.GET.get('q')
    if query:
        vehicle = Vehicle.objects.filter(Q(vehicle_type__name__icontains=query) |
                                    Q(plate_number__icontains=query) |
                                    Q(currently__icontains=query))

    if request.method == 'POST':
        t_form = VehicleTypeForm(request.POST)
        if t_form.is_valid():
            t_form.save()
            messages.success(request, 'Vehicle Type registered Successfully!')
            return redirect('vehicle-manage')
    else:
        t_form = VehicleTypeForm()
  
    context = {'vehicle': vehicle,'t_form': t_form}
    return render(request, 'Trequest/vehicle_management.html', context)


@login_required(login_url='login')
def annual_report(request):
    transport_request=TransportRequest.objects.all()
    print(transport_request.count())
    context={'transport_request':transport_request}
    return render(request, 'Trequest/report.html',context)

#  vehicle related
@login_required(login_url='login')
@allowed_users(allowed_roles=['TSHO'])
def vehicle_register(request):
    if request.method == 'POST':
        form = VehicleRegisterForm(request.POST)
        if form.is_valid():
            # Because your model requires that user is present, we validate the form and
            # save it without commiting, manually assigning the user to the object and resaving
            obj = form.save(commit=False)
            obj.adder = request.user
            obj.save()
            messages.success(request, 'Vehicle registered Successfully!')
            return redirect('vehicle-manage')
    else:
        form = VehicleRegisterForm()
    context = {'form': form}
    return render(request, 'Trequest/register_vehicle.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['TSHO'])
def edit_vehicle(request, id):
    vehicle = Vehicle.objects.get(id=id)
    if request.method == 'POST':
        form = VehicleRegisterForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vehicle updated Successfully!')
            return redirect('vehicle-manage')

    else:
        form = VehicleRegisterForm(instance=vehicle)

    context = {'form': form}
    return render(request, 'Trequest/update_vehicle.html', context)


@login_required(login_url='login')
def repaired_vehicle(request):
    return render(request, 'Trequest/repaired_vehicle.html')

@login_required(login_url='login')
def profile(request):
    return render(request, 'Trequest/profile.html')

@login_required(login_url='login')
@allowed_users(allowed_roles=['TSHO'])
def delete_account(request, id):
    account = get_object_or_404(MyUser, id=id)
    account.delete()
    messages.success(request, 'Account deleted Successfully!')
    return redirect('account')

@login_required(login_url='login')
@allowed_users(allowed_roles=['TSHO'])
def delete_vehicle(request, id):
    veh = get_object_or_404(Vehicle, id=id)
    veh.delete()
    messages.success(request, 'Vehicle deleted Successfully!')
    return redirect('vehicle-manage')


# @background(schedule=3600)
# def request_expire(username):  
#     TransportRequest.objects.filter(Q(status="Pending") or Q(status2 = "Pending") or Q(status3='Pending')).update(status="Expired")

#     available_request=TransportRequest.objects.filter(status=Pending or status2=Pending or status3=Pending)



@login_required(login_url='login')
@allowed_users(allowed_roles=['Passenger','DepartmentHead','SchoolDean'])
def make_request(request):
    current=TransportRequest.objects.filter(passenger=request.user)
    if not current:
        form = MakeRequestForm()
        if request.method == 'POST':
            form = MakeRequestForm(request.POST)
            if form.is_valid():
                # Because your model requires that user is present, we validate the form and
                # save it without commiting, manually assigning the user to the object and resaving
                obj = form.save(commit=False)
                obj.passenger = request.user
                obj.save()
                # request_expire(username=request.user)
                #user =TransportRequest.objects.get(passenger=request.user)
                role = MyUser.objects.get(username=request.user).role

                if role == 'DepartmentHead':

                    # TransportRequest.objects.create(status2="Approved")
                    #status2 = TransportRequest.objects.get(status2="Approved")
                    s2 = TransportRequest.objects.filter(
                        passenger=request.user)[0:1]
                    TransportRequest.objects.filter(
                        id__in=s2).update(status2="Approved")
                    # status2=s2.status2
                if role == 'SchoolDean':
                    s2 = TransportRequest.objects.filter(
                        passenger=request.user)[0:1]
                    TransportRequest.objects.filter(id__in=s2).update(
                        status2="Approved", status3="Approved")

                    # status2.save()
                messages.success(request, 'Request sent Successfully!')
                return redirect('my-request')
        else:
            form = MakeRequestForm()
        context = {'form': form}
        return render(request, 'Trequest/make_request.html', context)
    else:
        for req in current:
            s1=req.status 
            s2=req.status2
            s3=req.status3 
            if s1 == "Pending" or s2 == "Pending" or s3== "Pending" or None:
                messages.warning(request, 'Your Current Request is in progress...')
                return redirect('my-request')
            else:
                form = MakeRequestForm()
                if request.method == 'POST':
                    form = MakeRequestForm(request.POST)
                    if form.is_valid():
                        # Because your model requires that user is present, we validate the form and
                        # save it without commiting, manually assigning the user to the object and resaving
                        obj = form.save(commit=False)
                        obj.passenger = request.user
                        obj.save()
                        # request_expire(username=request.user)
                        #user =TransportRequest.objects.get(passenger=request.user)
                        role = MyUser.objects.get(username=request.user).role

                        if role == 'DepartmentHead':

                            # TransportRequest.objects.create(status2="Approved")
                            #status2 = TransportRequest.objects.get(status2="Approved")
                            s2 = TransportRequest.objects.filter(
                                passenger=request.user)[0:1]
                            TransportRequest.objects.filter(
                                id__in=s2).update(status2="Approved")
                            # status2=s2.status2
                        if role == 'SchoolDean':
                            s2 = TransportRequest.objects.filter(
                                passenger=request.user)[0:1]
                            TransportRequest.objects.filter(id__in=s2).update(
                                status2="Approved", status3="Approved")

                            # status2.save()
                        messages.success(request, 'Request sent Successfully!')
                        return redirect('my-request')
                else:
                    form = MakeRequestForm()
                context = {'form': form}
                return render(request, 'Trequest/make_request.html', context)

# request cancelling by passengers

@login_required(login_url='login')
@allowed_users(allowed_roles=['Passenger','DepartmentHead','SchoolDean'])
def cancel_request(request, id):
    TransportRequest.objects.filter(id=id).update(status='Cancelled',status2='Cancelled',status3='Cancelled')  
    messages.success(request, ' Request Cancelled Successfully!')
    return redirect('my-request')

@login_required(login_url='login')
@allowed_users(allowed_roles=['TSHO','DepartmentHead','SchoolDean'])
def reject_request(request, id):
    TransportRequest.objects.filter(id=id).update(status='Rejected',status2='Rejected',status3='Rejected')  
    messages.success(request, ' Request Rejected Successfully!')
    return redirect('index')

@login_required(login_url='login')
@allowed_users(allowed_roles=['DepartmentHead'])
def department_view_request(request):
    transport1 = TransportRequest.objects.filter(status2='Pending')
    
    # exclude the request sent from department to not visible to themselves
    transport = transport1.exclude(passenger__role="DepartmentHead").order_by('-created_at')
    context = {'transport': transport}
    return render(request, 'Trequest/department_view_request.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['DepartmentHead'])
def department_view_approved_request(request):
    transport = TransportRequest.objects.filter(status2='Approved').order_by('-created_at')
    context = {'transport': transport}
    return render(request, 'Trequest/department_view_approved_request.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['SchoolDean'])
def school_view_request(request):
    # std=TransportRequest.objects.all()
    # request_expire(pk=id)
    
    transport1 = TransportRequest.objects.filter(status2='Approved', status3='Pending')
    # if transport1.is_expired() == True:
    #     print ('expired')
    # exclude the request sent from school to not visible to them selves
    transport = transport1.exclude(
        passenger__role="SchoolDean").order_by('-created_at')
    context = {'transport': transport}
    return render(request, 'Trequest/school_view_request.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['SchoolDean'])
def school_view_approved_request(request):
    transport = TransportRequest.objects.filter(
        status3='Approved').order_by('-created_at')
    context = {'transport': transport}
    return render(request, 'Trequest/school_view_approved_request.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['TSHO','VicePresident'])
def tsho_view_approved_request(request):
    transport = TransportRequest.objects.filter(
        status='Approved').order_by('-created_at')
    context = {'transport': transport}
    return render(request, 'Trequest/tsho_view_approved_request.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['TSHO','VicePresident'])
def tsho_view_approved_request_detail(request, id):
    trans = TransportRequest.objects.get(id=id)
    
    context = {'trans': trans}
    return render(request, 'Trequest/view_approved_detail.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['TSHO','VicePresident'])
def tsho_view_request(request):
    transport = TransportRequest.objects.filter(status2='Approved', status3='Approved', status='Pending').order_by(
        '-created_at')
    print(transport)    
    
    
    context = {'transport': transport}
    return render(request, 'Trequest/tsho_view_request.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['DepartmentHead'])
def department_approve_request(request, id):
    approve = get_object_or_404(TransportRequest, id=id)
        
    if request.method == 'POST':
        form = DepartmentApproveForm(request.POST, instance=approve)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.status2 = "Approved"
            obj.save()
            messages.success(request, 'Request approved Successfully!')
            return redirect('department-view-approved-request')
    else:
        form = DepartmentApproveForm(instance=approve)
    context = {'form': form, 'approve': approve}
    return render(request, 'Trequest/department_approve_request.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['TSHO'])
def tsho_approve_request(request, id):
    vehicle = Vehicle.objects.filter(currently='Inside', status='Occupied')
    approve = get_object_or_404(TransportRequest, id=id)
    if request.method == 'POST':
        assigned=AssignRequest()
        name=request.POST.get('user')
        email=request.POST.get('email')
        date=request.POST.get('message')
        time=request.POST.get('message2')      
        
        new_driver = request.POST.get('driver')
        driver_fname = MyUser.objects.get(username=new_driver).first_name
        driver_lname = MyUser.objects.get(username=new_driver).last_name
        driver_full_name = driver_fname + " " + driver_lname

        assigned.user_to=name
        assigned.email_to=email
        assigned.driver_to=driver_full_name
        assigned.date_to=date
        assigned.time_to=time
        
        assigned.save()

        form = TshoApproveForm(request.POST, instance=approve)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.status = "Approved"
            obj.save()
            # for sending email to respective user
            subject = request.POST.get('subject')
            date = request.POST.get('message')
            time = request.POST.get('message2')
            new_driver = request.POST.get('driver')
            driver_fname = MyUser.objects.get(username=new_driver).first_name
            driver_lname = MyUser.objects.get(username=new_driver).last_name
            driver_full_name = driver_fname + " " + driver_lname
            driver_phone = MyUser.objects.get(username=new_driver).phone
            vehicle_plate = Vehicle.objects.get(
                driver__user__username=new_driver).plate_number
            message = "Your driver name: " + driver_full_name + "\n" + "Driver phone number: " + driver_phone + "\n " + \
                "Date of your trip: " + date + "\n " + "Time of your trip: " + \
                time + "\n " + "Your vehicle plate number: " + vehicle_plate
            email = request.POST.get('email')
            send_mail(subject, message, settings.EMAIL_HOST_USER,
                      [email], fail_silently=False)
            return render(request, 'Trequest/email_sent.html', {'email': email})
    else:
        form = TshoApproveForm(instance=approve)
    context = {'form': form,
               'approve': approve,
               'vehicle': vehicle
               }
    return render(request, 'Trequest/tsho_approve_request.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['SchoolDean'])
def school_approve_request(request, id):
    approve = get_object_or_404(TransportRequest, id=id)
    if request.method == 'POST':
        form = SchoolApproveForm(request.POST, instance=approve)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.status3 = "Approved"
            obj.save()
            messages.success(request, 'Request approved Successfully!')
            return redirect('school-view-approved-request')
    else:
        form = SchoolApproveForm(instance=approve)
    context = {'form': form, 'approve': approve}
    return render(request, 'Trequest/school_approve_request.html', context)


@login_required(login_url='login')
def my_request(request):
    myrequest = TransportRequest.objects.filter(passenger=request.user).order_by("-created_at")
    my_request_total = myrequest.count()
    
    context = {'myrequest': myrequest,
               'my_request_total': my_request_total}
    return render(request, 'Trequest/myrequest.html', context)


@login_required(login_url='login')
def my_request_detail(request, id):
    myrequest_detail = TransportRequest.objects.get(id=id)
    context = {'myrequest_detail': myrequest_detail}
    return render(request, 'Trequest/my_request_detail.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['TSHO'])
def account_management(request):
    account = MyUser.objects.all().order_by('-date_registered')
    total_account = account.count()
    query = request.GET.get('q')
    if query:
        account = MyUser.objects.filter(Q(first_name__icontains=query) |
                                    Q(last_name__icontains=query) |
                                    Q(role__icontains=query) |
                                    Q(username__icontains=query))
    # myfilter = UserFilter(request.GET, queryset=account)
    # account = myfilter.qs
    context = {'account': account,
               'total_account': total_account,
               }
    return render(request, 'Trequest/account_management.html', context)

@login_required(login_url='login')
def account_detail(request, username):
    user = Profile.objects.get(user__username=username)
    context = {'user': user}
    return render(request, 'Trequest/user_account_detail.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['TSHO'])
def create_schedule(request):
    if request.method == 'POST':
        form = CreateScheduleForm(request.POST)
        if form.is_valid():
            # Because your model requires that user is present, we validate the form and
            # save it without commiting, manually assigning the user to the object and resaving
            obj = form.save(commit=False)
            obj.author = request.user
            obj.save()
            messages.success(request, 'Schedule created Successfully!')
            return redirect('index')
    else:
        form = CreateScheduleForm()
    context = {'form': form}
    return render(request, 'Trequest/create_schedule.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['TSHO'])
def update_schedule(request, id):
    schedule = Schedule.objects.get(id=id)
    if request.method == 'POST':
        form = CreateScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Schedule updated Successfully')
            return redirect('index')
    else:
        form = CreateScheduleForm(instance=schedule)
    context = {'form': form}
    return render(request, 'Trequest/update_schedule.html', context)



# for notification which appear in the dashboard of thsho


def dep_notifications_count():
    return Notifications.objects.filter(is_viewed=False, request_id__status2="Pending").count()


def scho_notifications_count():
    return Notifications.objects.filter(is_viewed=False, request_id__status3="Pending", request_id__status2="Approved").count()


def tsho_notifications_count():
    return Notifications.objects.filter(is_viewed=False, request_id__status="Pending", request_id__status3="Approved").count()
# def notifications_list():
#     return Notifications.objects.all()
#     # not_count=notifications.count()
    # context={'notifications':notifications,'not_count':not_count}
    # return render(request, 'Trequest/notifications.html', context)


# Driver Evaluation View


@login_required(login_url='login')
def evaluate(request):
    if request.method == 'POST':
        form = EvaluateDriverForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.duser = request.user
            myrating=request.POST.get('rat')
            obj.rating=myrating
            form.save()
            messages.success(request, 'Rated Successfully!')
            return redirect('index')
    else:
        form = EvaluateDriverForm()
    context = {'form': form}
    return render(request, 'Trequest/evaluate_driver.html', context)


# Activity Log
# Activity log view
@login_required(login_url='login')
@allowed_users(allowed_roles=['TSHO'])
def ActivityLogs(request):
    logs=ActivityLog.objects.all()
    context={'logs':logs}
    return render(request, 'Trequest/activity_log.html',context)
# view Rate
@login_required(login_url='login')
def viewRate(request):
     rates= DriverEvaluation.objects.all()
     context={'rates':rates}
     return render(request, 'Trequest/view_rate.html',context)  

@login_required(login_url='login')
def myRate(request):
     rates= DriverEvaluation.objects.filter(driver__user__first_name =request.user.first_name)
     context={'rates':rates}
     return render(request, 'Trequest/my_rate.html',context) 
# feedback
@login_required(login_url='login')
def feedback(request):
    form = FeedBackForm()
    if request.method == 'POST':
        form = FeedBackForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            form.save()
            messages.success(request, 'your feedback is successfully sent')
            return redirect('index')
    context = {'form': form}
    return render(request, 'Trequest/create_feedback.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['TSHO'])
def view_feedback(request):
    feedbacks = Feedback.objects.all()
    context = {'feedback': feedbacks}
    return render(request, 'Trequest/view_feedback.html', context)
