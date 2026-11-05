from django.urls import path
from . import views

urlpatterns = [
<<<<<<< HEAD
    # Module 06 original routes
    path('', views.student_registration, name='student_registration'),
    path('success/', views.registration_success, name='registration_success'),

    # Module 07 new routes
    path('students/', views.student_list, name='student_list'),
    path('students/create/', views.student_create, name='student_create'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),
    path('students/<int:pk>/edit/', views.student_update, name='student_update'),
    path('students/<int:pk>/delete/', views.student_delete, name='student_delete'),
=======
    path('', views.student_registration, name='student_registration'),
    path('success/', views.registration_success, name='registration_success'),
>>>>>>> b3114560e65592d8b734db312cc8757bf09a4770
]
