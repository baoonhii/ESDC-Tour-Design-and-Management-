import json

from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_http_methods

from django.shortcuts import get_object_or_404, render, redirect

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from django.db.models import Q

from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder

from django.views.decorators.http import require_POST, require_GET


from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from django.template.loader import render_to_string
from django.urls import reverse
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes

from TDMS.forms import RegistrationForm, LoginForm, EditLocationForm, PasswordResetForm

from TDMS.models import Account, Bookmark, Location, Note, Plan, ROLE, Log, STATUS

JSON_INSUFFICIENT_PERMISSION = {'status': 'error', 'error': 'Insufficient permissions'}

def json_return_success_status(model, action):
    """`{'status': 'success', 'message': f'{model} {action} successfully'}`"""
    return {'status': 'success', 'message': f'{model} {action} successfully'}

def json_return_error_status(model=None, action=None, error_code=None):
    """default = `{'status': 'error', 'error': f'Form is invalid'}`"""
    if model is None:
        model = "Form"
    if action is None:
        action = "is invalid data"
    if error_code is None:
        error_code = 'error'
    return {'status': error_code, 'error': f'{model} {action}'}

def create_logout_log(user):
    """Create a logout log for the given user."""
    new_log = Log.create_logout_log(user)
    new_log.save()
    print(new_log)

@login_required(login_url='home')
def logout_view(request):
    create_logout_log(request.user)
    logout(request)
    return redirect('home')

def home_view(request):
    return render(request, 'home.html')

def authenticate_user(request, form):
    """Authenticate user with given form data."""
    if form.is_valid():
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        return authenticate(request, username=username, password=password)
    return None

def create_login_log(user):
    """Create a login log for the given user."""
    new_log = Log.create_login_log(user)
    new_log.save()
    print(new_log)

def login_view(request): 
    form = LoginForm(request.POST or None)
    user = authenticate_user(request, form)

    if user is not None:
        login(request, user)
        create_login_log(user)
        return redirect('home')

    return render(request, 'login.html', {'form': form})


def register_view(request):
    form = RegistrationForm(request.POST or None)

    if form.is_valid():
        form.save()
        username = form.cleaned_data.get('username')
        messages.info(request, f'{username}')
        return redirect('register_success')

    return render(request, 'register.html', {'form': form})

def register_success_view(request):
    username = ''
    for message in messages.get_messages(request):
        if message.level == messages.INFO:
            username = message.message
            break
    return render(request, 'register_success.html', {'username': username})

def create_activate_acc_email(request, user, to_email, uid, token):
    mail_subject = 'Activate your account'
    message = render_to_string('acc_active_email.html', {
        'user': user,
        'domain': request.META['HTTP_HOST'],
        'uid': uid,
        'token': token,
        'password_reset_link': request.build_absolute_uri(reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token}))
    })
    email = EmailMessage(mail_subject, message, to=[to_email])
    return email
    
@login_required(login_url='home')
def account_create_view(request):
    if not request.user.user_role == ROLE.OWNER:
        return HttpResponseForbidden()
    form = RegistrationForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        token = default_token_generator.make_token(user)
        to_email = form.cleaned_data.get('email')
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        email = create_activate_acc_email(request, user, to_email, uid, token)
        print(email.send())
        return HttpResponse(f'Email is sent to {to_email}. <a href="TDMS/home">Return to home</a>')
    return render(request, 'register.html', {'form': form})

def create_pass_reset_email(request, user, to_email, uid, token):
    mail_subject = 'Reset your password'
    message = render_to_string('password_reset_email.html', {
        'user': user,
        'domain': request.META['HTTP_HOST'],
        'uid': uid,
        'token': token,
        'password_reset_link': request.build_absolute_uri(reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token}))
    })
    email = EmailMessage(mail_subject, message, to=[to_email])
    return email

def password_reset_view(request):
    form = PasswordResetForm(request.POST or None)
    if form.is_valid():
        to_email = form.cleaned_data.get('email')
        ssn = form.cleaned_data.get('ssn')
        try:
            user = Account.objects.get(email=to_email, ssn=ssn)
        except Account.DoesNotExist:
            form.add_error(None, 'No account found with the provided email and SSN.')
        else:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            email = create_pass_reset_email(request, user, to_email, uid, token)
            email.send()
            return HttpResponse(f'Email is sent to {user.email}. <a href="TDMS/home">Return to home</a>')
    else:
        form = PasswordResetForm()
    return render(request, 'password_reset.html', {'form': form})
    
    
def create_add_loc_log(user, location):
    """Create an add location log for the given user and new location."""
    new_log = Log.create_add_loc_log(user, location)
    new_log.save()
    print(new_log)

@login_required(login_url='home')
def add_loc_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        location = Location.create_from_json(data)
        if location:
            location.save()
            create_add_loc_log(request.user, location)
            return JsonResponse(json_return_success_status("Location", "added"))
        return JsonResponse(json_return_error_status("Location", "cannot be added"))
    return render(request, 'add_loc.html')


@login_required(login_url='home')
def display_locations(request):   
    return render(request, 'lookup_loc.html', {'current_user': request.user})

@login_required(login_url='home')
def search(request):
    query = request.GET.get('q', '')
    n = request.GET.get('n')
    try:
        n = int(n)
    except (TypeError, ValueError):
        n = None

    data = Location.get_list_loc_w_bookmark(request.user, n, query, True)
 
    return JsonResponse(data, safe=False, encoder=DjangoJSONEncoder)

def get_location_name(request):
    data = json.loads(request.body)
    location_names = []
    for coord in data:
        lat = coord['lat']
        lng = coord['lng']

        # Find the nearest location to the given coordinates
        location = Location.get_nearest(lat, lng)

        if location is None:
            location_names.append(f"({lat}, {lng})")
        else:
            # Add the location name to the list
            location_names.append(location.name)

    # Return the location names as a JSON response
    return JsonResponse({'names': location_names})

@login_required(login_url='home')
@require_http_methods(["DELETE"])
def delete_location(request, location_id):
    return delete_object(request, location_id, Location)

def create_edit_loc_log(user, location, field, old_val, new_val):
    """Create an edit location log for the given user and location and what is changed."""
    new_log = Log.create_edit_loc_log(
        user=user, 
        location=location, 
        field_name=field, 
        old_value=old_val, 
        new_value=new_val
    )
    new_log.save()
    print(new_log)

def process_edit_location_form_log(user, location, form, old_name, old_addr):
    new_name = form.cleaned_data.get('name')
    new_addr = form.cleaned_data.get('address')
    message = []
    if new_name != old_name:
        message.append("name")
        create_edit_loc_log(user, location, 'name', old_name, new_name)
    if new_addr != old_addr:
        message.append("address")
        create_edit_loc_log(user, location, 'address', old_addr, new_addr)
    form.save()
    return message

def create_edit_loc_form_log(message):
    if len(message) == 0:
        return JsonResponse(json_return_success_status(f"Location data same,", "nothing was updated"))
    if len(message) == 1:
        message = message[0]    
    else:
        message = " and ".join(message)
    return JsonResponse(json_return_success_status(f"Location {message}", "updated"))
    

@login_required(login_url='home')
def edit_location(request, location_id):
    if not request.user.can_modify():
        return JsonResponse(JSON_INSUFFICIENT_PERMISSION)
    
    location = get_object_or_404(Location, pk=location_id)
    old_name = location.name
    old_addr = location.address
    if request.method == 'POST':
        form = EditLocationForm(request.POST, instance=location)
        if form.is_valid():
            message = process_edit_location_form_log(request.user, location, form, old_name, old_addr)
            return create_edit_loc_form_log(message)
        else:
            return JsonResponse(json_return_error_status("Location", "cannot be updated"))
    else:
        form = EditLocationForm(instance=location)
        form_html = form_html_builder("editLocationForm", f"edit_location/{location_id}/", form)
        return JsonResponse({'form_html': form_html})

def form_html_builder(id, action, form):
        return f'<form id="{id}" action="{action}" method="post">{form.as_p()}</form>'

@login_required(login_url='home')
@require_POST
def bookmark_location(request):
    location = get_object_or_404(Location, pk=request.POST.get('location_id'))
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, location=location)
    
    if not created:
        bookmark.delete()
        
    return JsonResponse({'bookmarked': created})

@login_required(login_url='home')
@require_GET
def fetch_notes(request):
    data = json.dumps(
        Note.get_note_list_by_loc_id(request.GET.get('location_id')),
        cls=DjangoJSONEncoder)

    return JsonResponse(data, safe=False)

@login_required(login_url='home')
@require_POST
def add_note(request):
    new_note = Note.create_note(
        request.user, 
        request.POST.get('location_id'), 
        request.POST.get('content'))
    
    if new_note is not None:
        new_note.save()
        return JsonResponse(json_return_success_status("Note", "added")) 
    return JsonResponse(json_return_error_status("Location", "not found")) 

def edit_planner(request, id, data):
    plan = Plan.objects.get(pk=id)
    waypoints = plan.route_data[0]['waypoints']
    waypoint_coords = [(waypoint['latLng']['lat'], waypoint['latLng']['lng']) for waypoint in waypoints]
    locations_waypoints = []
    for lat, lng in waypoint_coords:
        found_location = Location.get_nearest(lat, lng)
        if found_location:
            locations_waypoints.append((found_location.location_id, 1))
        else:
            locations_waypoints.append(((lat, lng), -1))
    refill_data = {
        "plan_id": plan.pk,
        "plan_name": plan.plan_name,
        "location_waypoints": locations_waypoints
    }
    refill_data = json.dumps(refill_data, cls=DjangoJSONEncoder)
    return render(request, 'planner.html', {'locations_json': data, 'current_user': request.user, 'refill_data': refill_data})
    

@login_required(login_url='home')
def planner(request, id=None):
    data = json.dumps(
            Location.get_list_loc_w_bookmark(request.user, None, '', True),
            cls=DjangoJSONEncoder)
    if id is None:
        return render(request, 'planner.html', {'locations_json': data, 'current_user': request.user})
    else:
        plan = Plan.objects.get(pk=id)
        if plan.can_be_edited():
            return edit_planner(request, id, data)
        return JsonResponse(json_return_error_status("Plan", "is completed, cannot be edited", 400))
        
def save_edit_route(request, plan, data):
    plan.update_plan(
        plan_name=data['plan_name'], 
        est_distance=data['est_distance'],
        est_duration=data['est_duration'],
        route_data=data['route_data']
    )
    create_edit_plan_log(request.user, plan)
    return JsonResponse(json_return_success_status("Plan", "edited"))

def create_edit_plan_log(user, plan):
    new_log = Log.create_edit_plan_log(user, plan)
    new_log.save()
    print(new_log)
    
def create_plan_log(user, plan):
    new_log = Log.create_plan_log(user, plan)
    new_log.save()
    print(new_log)
    
@login_required(login_url='home')
def save_route(request, id=None):
    if request.method == 'POST':
        data = json.loads(request.body)
        if id is None:
            plan = Plan.create_from_json(request.user, data)
            if plan:
                plan.save()
                create_plan_log(request.user, plan)
                return JsonResponse(json_return_success_status("Plan", "created"))
        else:   # updating existing plan
            # print(data)
            save_edit_route(request, id, data)            
            return JsonResponse(json_return_success_status("Plan", "edited"))
        return JsonResponse(json_return_error_status())
    return JsonResponse(json_return_error_status("Request method", "invalid"))

@login_required(login_url='home')
def view_plans(request):      
    return render(request, 'view_plans.html', {
        'plans_json': json.dumps(Plan.get_plans()), 
        'current_user': request.user
        })

@login_required(login_url='home')
def get_plan_route(request, plan_id):
    return JsonResponse(Plan.get_plan_data_by_id(plan_id))

def create_update_plan_status_log(user, plan, old_status, new_status):
    new_log = Log.create_update_plan_status_log(user, plan, old_status, new_status)
    new_log.save()
    print(new_log)

def update_plan_status(request, plan_id):
    if request.method == 'POST':
        # Get the plan
        plan = get_object_or_404(Plan, pk=plan_id)

        old_status = plan.status
        # Get the new status from the request
        new_status = request.POST.get('status')

        # Check if the new status is valid
        if new_status not in dict(STATUS.choices):
            return JsonResponse(json_return_error_status("Plan status", "invalid", 400))

        # Check if the status is 'complete'
        if plan.status == STATUS.COMPLT:
            return JsonResponse(json_return_error_status("Plan", "is completed, cannot be edited", 400))

        # Update the status
        plan.status = new_status
        plan.save()

        # Log the change
        create_update_plan_status_log(request.user, plan, old_status, new_status)

        return JsonResponse(json_return_success_status("Plan", "updated"))

    else:
        return JsonResponse(json_return_error_status("Request method", "invalid", 405))

@login_required
def delete_note(request):
    if request.method == 'POST':
        data = request.body
        note_id = request.POST.get('id')
        note = get_object_or_404(Note, id=note_id)

        if request.user == note.author:
            note.delete()
            return JsonResponse({'message': 'Note deleted successfully'})
        else:
            return JsonResponse({'error': 'You do not have permission to delete this note'}, status=403)

@login_required(login_url='home')
@require_http_methods(["DELETE"])
def delete_route(request, plan_id):
    return delete_object(request, plan_id, Plan)
    
def delete_object(request, obj_id, model):
    try:
        # get the object
        obj = model.objects.get(pk=obj_id)
        
        # permission check
        if not request.user.can_modify():
            return JsonResponse(JSON_INSUFFICIENT_PERMISSION)
        
        # check if deletion is implemented for class
        if not callable(getattr(obj, "can_be_deleted", None)):
            # return JsonResponse({'status': 'error', 'error': 'Deletion is not implemented/allowed'})
            return JsonResponse(json_return_error_status(model.__name__, "deletion is not implemented/allowed"))
        
        # check if this object can be deleted
        if obj.can_be_deleted():
            new_log = Log.create_delete_obj_log(
                user=request.user, 
                obj=obj,
                obj_type=model.__name__
            )
            new_log.save()
            print(new_log)
            obj.delete()
            
            return JsonResponse({'status': 'success'})
        # return JsonResponse({'status': 'error', 'error': f'This {model.__name__} cannot be deleted.'})
        return JsonResponse(json_return_error_status(model.__name__, "cannot be deleted"))
    except model.DoesNotExist:
        # return JsonResponse({'status': 'error', 'error': f'{model.__name__} not found'})
        return JsonResponse(json_return_error_status(model.__name__, "not found"))
    
@login_required(login_url='home')
def view_logs(request):
    logs = Log.objects.all().order_by('-timestamp')
    return render(request, 'view_logs.html', {'logs': logs})