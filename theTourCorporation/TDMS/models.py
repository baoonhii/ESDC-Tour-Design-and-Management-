from django.db import models
from django.db.models import Model, Q
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import User
from django.db.models import JSONField
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid
import numpy as np
from sklearn.neighbors import BallTree

class ROLE(models.TextChoices):
    OWNER = "ownr", ("Owner")
    MANAGER = "mngr", ("Manager")
    TOUROP = "tour", ("Tour Operator")

class STATUS(models.TextChoices):
    PENDNG = "pendng", ("Pending")
    ACCEPT = "accept", ("Accepted")
    REJECT = "reject", ("Rejected")
    CANCEL = "cancel", ("Canceled")
    PROGRS = "progrs", ("In-progress")
    COMPLT = "complt", ("Complete")
    
class ACTION(models.TextChoices):
    CREATE = "crt", ("Created")
    UPDATE = "upd", ("Updated")
    DELETE = "del", ("Deleted")
    LOGIN  = "lgn", ("Logged In")
    LOGOUT = "lgt", ("Logged Out")
    NONE = "non", ("None")

class MyAccountManager(BaseUserManager):
    def create_user(self, email, password=None, full_name=None, ssn=None, username=None, user_role=None):
        self.validate_email(email)
        if username is None:
            username = self.generate_username(email)
        if user_role is None:
            user_role = ROLE.TOUROP
        user = self.create_user_instance(username, email, password, full_name, ssn, user_role)
        user.save(using=self._db)
        return user
    
    def validate_ssn(self, ssn):
        if not ssn:
            raise ValueError('User must have an SSN')

    def validate_username(self, username):
        if not username:
            raise ValueError('User must have username')
        
    def validate_email(self, email):
        if not email:
            raise ValueError('User must have an email')
    
    def generate_username(self, email):
        return email.split('@')[0]

    def create_user_instance(self, username, email, password, full_name, ssn, user_role):
        user = self.model(
            username=username, 
            email=self.normalize_email(email),
            full_name=full_name,
            ssn=ssn,
            user_role=user_role
        )
        user.set_password(password)
        return user

    def create_superuser(self, username, password=None, full_name=None):
        email=f"{username}@superuser.com"
        unique_ssn = str(uuid.uuid4().int)[:9]
        user = self.create_user(email, password, full_name, unique_ssn, username=username)
        self.set_superuser_permissions(user)
        user.save(using=self._db)
        return user

    def set_superuser_permissions(self, user):
        user.user_role = ROLE.OWNER
        user.is_admin = user.is_staff = user.is_superuser = True

class Account(AbstractBaseUser):
    username = models.CharField(verbose_name="username", max_length=20, unique=True)
    email = models.EmailField(verbose_name='email', max_length=60, unique=True)
    
    full_name = models.CharField(verbose_name='full name', max_length=60, unique=False, null=True)
    ssn = models.CharField(verbose_name='ssn', max_length=9, unique=True)
    
    user_role = models.CharField(max_length=4, choices=ROLE.choices, default=ROLE.TOUROP)
    
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    USERNAME_FIELD = 'username'
    objects = MyAccountManager()

    def __str__(self) -> str:
        return f"user: {self.username}, role={self.user_role}, email={self.email}, full name={self.full_name}, ssn={self.ssn}"
    
    def has_perm(self, perm, obj=None):
        """For checking permissions. to keep it simple all admin have ALL permissions"""
        return self.is_admin

    def has_module_perms(self, app_label):
        """Does this user have permission to view this app? (ALWAYS YES FOR SIMPLICITY)"""
        return True

    def can_modify(self):
        return self.user_role in [ROLE.OWNER, ROLE.MANAGER]

def process_json(data, fields: list[str]):
    return {field: data.get(field) for field in fields}

class Location(models.Model):
    JSON_FIELDS = ['lat', 'lng', 'name', 'address', 'location_type']
    
    location_id = models.AutoField(primary_key=True)
    lat = models.FloatField()
    lng = models.FloatField()
    name = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    location_type = models.CharField(max_length=255, blank=True, null=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    def __str__(self) -> str:
        return f"({self.lat}, {self.lng}) {self.name} at {self.address}"
    
    def is_bookmarked_by(self, user):
        if user is None:
            return False
        return Bookmark.objects.filter(user=user, location=self).exists()
    
    def serialize(self, user=None):
        return {
            'pk': str(self.pk),
            'lat': self.lat, 
            'lng': self.lng, 
            'name': self.name, 
            'address': self.address,
            'location_type': self.location_type,
            'is_bookmarked': self.is_bookmarked_by(user),
            'modified_at': self.modified_at
        }
        
    def can_be_deleted(self):
        return True
    
    @classmethod
    def get_nearest(cls, lat, lng, max_distance_meters=200):
        locations = list(Location.objects.all())
        location_coords = np.radians([(location.lat, location.lng) for location in locations])

        tree = BallTree(location_coords, leaf_size=15, metric='haversine')
        distances, indices = tree.query([np.radians([float(lat), float(lng)])], return_distance=True)

        if max_distance_meters is not None:
            max_distance_rad = max_distance_meters / 6371000  # Earth's radius in meters
            close_enough = distances[0] < max_distance_rad

            if not np.any(close_enough):
                return None  # No locations are close enough

            nearest_index = indices[0][np.argmin(distances[0][close_enough])]
        else:
            nearest_index = indices[0][np.argmin(distances)]
        return locations[nearest_index]


    @staticmethod
    def get_list_loc_w_bookmark(user, n=None, query='', sort_bookmark=False):
        if query:
            locations = Location.objects.filter(Q(name__icontains=query) | Q(address__icontains=query))
        else:
            locations = Location.objects.all()

        # Sort by date modified
        locations = locations.order_by('-modified_at')

        loc_w_bookmark = [loc.serialize(user) for loc in locations]
        loc_w_bookmark.sort(key=lambda x: x['modified_at'], reverse=True)
        if sort_bookmark:
            # If sort_bookmark is True, sort by is_bookmarked first and then by date modified
            loc_w_bookmark.sort(key=lambda x: x['is_bookmarked'], reverse=True)

        # Limit the number of locations if n is not None
        if n is not None:
            loc_w_bookmark = loc_w_bookmark[:n]

        return loc_w_bookmark
    
    @staticmethod
    def create_from_json(data):
        try:
            return Location(**process_json(data, Location.JSON_FIELDS))
        except:
            return None



class Bookmark(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __repr__(self):
        return f"{self.user.username} bookmarked {self.location.name}"

class Note(models.Model):
    author = models.ForeignKey(Account, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note by {self.author.username} on {self.location.name}"
    
    def serialize(self):
        return {
            'id': self.id,
            'content': self.content,
            'created_at': self.created_at,
            'author': self.author.username,
            'location': self.location.name,
        }
        
    @staticmethod
    def create_note(user, location_id, content):
        location = Location.objects.get(location_id=location_id)
        new_note = None
        if location:
            new_note = Note(author=user, location=location, content=content)
        
        return new_note
    
    @staticmethod
    def get_note_list_by_loc_id(location_id):
        location = Location.objects.get(location_id=location_id)
        loc_notes = []
        notes = Note.objects.filter(location=location)
        if location:
            loc_notes = [note.serialize() for note in notes]
        
        return loc_notes
    

class Plan(models.Model):
    JSON_FIELDS = ['plan_name', 'est_distance', 'est_duration', 'route_data']
    
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    plan_name = models.CharField(max_length=255, blank=True, null=True)
    est_distance = models.FloatField(blank=True, null=True)
    est_duration = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
            max_length=6,
            choices=STATUS.choices,
            default=STATUS.PENDNG
        )
    route_data = JSONField(blank=True, null=True)
    
    def serialize(self):
        return {
            'pk': self.pk,  
            'plan_name': self.plan_name, 
            'username' : self.user.username,
            'est_distance' : self.est_distance,
            'est_duration' : self.est_duration,
            'status' : self.get_status_display(),
        }
    
    def can_be_deleted(self):
        return self.status != STATUS.COMPLT
    
    def can_be_updated(self):
        return self.status != STATUS.COMPLT
    
    def can_be_edited(self):
        return self.status == STATUS.PENDNG
    
    def __repr__(self) -> str:
        return f"{self.plan_name}, created by {self.username}"
    
    def update_plan(self, plan_name=None, est_distance=None, 
                    est_duration=None, created_at=None, route_data=None):
        if plan_name is not None:
            self.plan_name = plan_name
        if est_distance is not None:
            self.est_distance = est_distance
        if est_duration is not None:
            self.est_duration = est_duration
        if created_at is not None:
            self.created_at = created_at
        if route_data is not None:
            self.route_data = route_data
        self.save()
    
    @staticmethod
    def get_plans(n=10, order="status"):
        plans = Plan.objects.order_by(order)
        return {str(plan.pk): plan.serialize() for plan in plans}
     
    @staticmethod
    def get_plan_data_by_id(plan_id):
        plan = Plan.objects.get(pk=plan_id)
        return {
            'route_data': plan.route_data
        }    
        
    @staticmethod
    def create_from_json(user, data):
        try:
            return Plan(user=user, **process_json(data, Plan.JSON_FIELDS))
        except:
            return None
    
    @staticmethod
    def get_plan_and_update_status(user, plan_id):
        if not user.can_modify():
            return None
        plan = Plan.objects.get(pk=plan_id)
        if plan and plan.can_be_updated():
            return plan 
        return None

class Log(models.Model):
    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    username = models.CharField(max_length=255)
    action = models.CharField(
        max_length=3,
        choices=ACTION.choices,
        default=ACTION.NONE
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    field_name = models.CharField(max_length=255, null=True)
    old_value = models.TextField(null=True)
    new_value = models.TextField(null=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} {self.get_action_display()} a {self.content_type} | {self.field_name} at {self.timestamp}"
        
    @staticmethod
    def create_login_log(user: Account):
        return Log(
            user=user, username=user.username, 
            action=ACTION.LOGIN, content_object=user
        )

    @staticmethod
    def create_logout_log(user: Account):
        return Log(
            user=user, username=user.username, 
            action=ACTION.LOGOUT, content_object=user
        )
    
    @staticmethod
    def create_add_loc_log(user: Account, location: Location):
        return Log(
            user=user, username=user.username, 
            action=ACTION.CREATE, content_object=location
        )
    
    @staticmethod
    def create_edit_loc_log(user: Account, location: Location, 
                            field_name, old_value, new_value):
        return Log(
            user=user, username=user.username, 
            action=ACTION.UPDATE, content_object=location, 
            field_name=field_name, old_value=old_value, new_value=new_value
        )

    @staticmethod 
    def create_plan_log(user: Account, plan: Plan):
        return Log(
            user=user, username=user.username, 
            action=ACTION.CREATE, content_object=plan
        )
    
    @staticmethod
    def create_update_plan_status_log(user: Account, plan: Plan, old_status, new_status):
        return Log(
            user=user,
            username=user.username,
            action=ACTION.UPDATE,
            content_object=plan,
            field_name='status',
            old_value=old_status,
            new_value=new_status
        )
        
    @staticmethod
    def create_edit_plan_log(user: Account, plan: Plan):
        return Log(
            user=user, username=user.username, 
            action=ACTION.UPDATE, content_object=plan,
            field_name="plan information"
        )
    
    @staticmethod
    def create_delete_obj_log(user: Account, obj, obj_type):
        return Log(
            user=user, 
            username=user.username, 
            action=ACTION.DELETE, 
            content_object=obj,
            field_name='whole object',
            old_value=f'{obj_type} with info={obj}'
        )
