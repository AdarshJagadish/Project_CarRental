from django.urls import path
from . import views

urlpatterns = [
    path('', views.carhub_home),
    path('login', views.carhub_login),
    path('register', views.register),
    path('logout', views.carhub_logout),

    # -------admin----------
    path('admin_home', views.admin_home),
    path('add_car', views.add_car),
    path('edit_car/<id>', views.edit_car),
    path('add_category', views.add_category),
    path('view_cat/<id>', views.view_cat),
    path('delete_car/<id>', views.delete_car),
    path('delete_category/<id>', views.delete_category),
    path('manage_rentals/', views.manage_rentals, name='manage_rentals'),
    path('update_rental_status/<int:rental_id>/<str:status>/', views.update_rental_status, name='update_rental_status'),
    path('admin/mark_full_paid/<int:rental_id>/', views.mark_full_paid, name='mark_full_paid'),
    path('export_rentals_csv/', views.export_rentals_csv, name='export_rentals_csv'),
    path('adminpanel/mark_full_paid/<int:rental_id>/', views.mark_full_paid, name='mark_full_paid'),


    # ------user------------
    path('view_car/<id>', views.view_car),
    path('contact', views.contact),
    path('rent_car/<id>', views.rent_car),
    path('view_category/<id>', views.view_category),
    path('profile', views.user_profile, name='user_profile'),
    path("payment/<int:rental_id>/", views.create_razorpay_order, name="payment"),
    path("pay-balance/<int:rental_id>/", views.create_balance_order, name="pay_balance"),  # ✅ new
    path("payment/success/", views.razorpay_success, name="payment_success"),
    path("cancel-rental/<int:rental_id>/", views.cancel_rental, name="cancel_rental"),
]