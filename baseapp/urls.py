from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Main Pages
    path('', views.dashboard_view, name='dashboard'),
    path('map/', views.map_overview_view, name='map_overview'),
    path('search/route/', views.search_route_view, name='search_route'),

    # Profile & User-Specific Pages
    path('profile/', views.profile_view, name='profile'),
    path('my-items/', views.my_items_view, name='my_items'),

    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='baseapp/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Password Reset Flow (Built-in)
    path('password-reset/',
         auth_views.PasswordResetView.as_view(template_name='baseapp/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='baseapp/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='baseapp/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='baseapp/password_reset_complete.html'),
         name='password_reset_complete'),

    # Item Actions
    path('item/add/', views.add_item_view, name='add_item'),
    path('item/<int:item_id>/', views.item_detail_view, name='item_detail'),
    path('item/<int:item_id>/edit/', views.edit_item_view, name='edit_item'),
    path('item/<int:item_id>/delete/', views.delete_item_view, name='delete_item'),
    path('item/<int:item_id>/resolve/', views.resolve_item_view, name='resolve_item'),
    path('item/<int:item_id>/contact/', views.contact_reporter_view, name='contact_reporter'),

    #verfication of answer
    path('ajax/verify-answer/', views.verify_answer_view, name='verify_answer'),

    #notification
    path('notifications/', views.notifications_view, name='notifications'),

    #verification
    path('send-verification-email/', views.send_verification_email_view, name='send_verification_email'),
    path('verify-email/<str:token>/', views.verify_email_view, name='verify_email'),

    # Messaging
    path('inbox/', views.inbox_view, name='inbox'),
    path('conversation/<int:conversation_id>/', views.conversation_detail_view, name='conversation_detail'),
    path('item/<int:item_id>/start-chat/', views.start_conversation_view, name='start_conversation'),

    #leaderboard
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),

    # Export
    path('export/csv/', views.export_items_csv, name='export_csv'),
]