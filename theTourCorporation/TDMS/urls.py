from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Home and auth
    path('TDMS/home', views.home_view, name='home'),
    path('TDMS/', views.login_view, name='login'),
    path('TDMS/logout', views.logout_view, name='logout'),
    
    # Register
    path('TDMS/register', views.account_create_view, name='register'),
    # path('TDMS/register_success', views.register_success_view, name='register_success'),
    
    # Location (openstreetmap)
    path('TDMS/add_loc_view', views.add_loc_view, name='add_loc_view'),
    
    # Location (db)
    path('TDMS/lookup_loc', views.display_locations, name='lookup_loc'),
    path('TDMS/search', views.search, name='search'),
    path('TDMS/delete_location/<int:location_id>/', views.delete_location, name='delete_location'),
    path('TDMS/edit_location/<int:location_id>/', views.edit_location, name='edit_location'),
    path('TDMS/get_location_name', views.get_location_name, name='get_location_name'),

    # bookmark
    path('TDMS/bookmark_location', views.bookmark_location, name='bookmark_location'),
    
    # note
    path('TDMS/fetch_notes', views.fetch_notes, name='fetch_notes'),
    path('TDMS/add_note', views.add_note, name='add_note'),
    path('TDMS/delete_note', views.delete_note, name='delete_note'),
    
    # Planner
    path('TDMS/planner', views.planner, name='planner'),
    path('TDMS/planner/<int:id>/', views.planner, name='planner'),
    path('TDMS/save_route', views.save_route, name='save_route'),
    path('TDMS/planner/<int:id>/save_route', views.save_route, name='save_route'),
    path('TDMS/view_plans', views.view_plans, name='view_plans'),
    path('TDMS/get_plan_route/<int:plan_id>/', views.get_plan_route, name='get_plan_route'),
    path('TDMS/delete_route/<int:plan_id>/', views.delete_route, name='delete_route'),
    path('TDMS/update_plan_status/<int:plan_id>/', views.update_plan_status, name='update_plan_status'),
    
    # Logs
    path('TDMS/view_logs', views.view_logs, name='view_logs'),
    
    # Password reset
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),

    path('password_reset/', views.password_reset_view, name='password_reset'),
    path('password_reset/done/', views.home_view, name='password_reset_done'),
    path('reset/done/', views.home_view, name='password_reset_complete'),
]