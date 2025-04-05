# urls.py
from django.urls import path
from .views import (
    StudentListView,
    StudentDetailView,
    ReportLostCardView,
    VerifyQRCodeView,
    EntryLogListView,
    LostCardScansListView,
    RequestNewCardView,
    AdminDashboardStatsView,
    BulkImportStudentsView,
    ExpireStudentIDView,
)

urlpatterns = [
    
    # Student URLs
    path('students/', StudentListView.as_view(), name='student_list'),
    path('students/<uuid:id>/', StudentDetailView.as_view(), name='student_detail'),
    path('students/profile/', StudentDetailView.as_view(), name='student_own_profile'),
    path('students/<uuid:pk>/report-lost/', ReportLostCardView.as_view(), name='report_lost_card'),
    path('students/report-lost/', ReportLostCardView.as_view(), name='report_own_lost_card'),
    path('students/<uuid:pk>/request-new-card/', RequestNewCardView.as_view(), name='request_new_card'),
    path('students/request-new-card/', RequestNewCardView.as_view(), name='request_own_new_card'),
    path('students/<uuid:pk>/expire/', ExpireStudentIDView.as_view(), name='expire_student_id'),
    path('students/bulk-import/', BulkImportStudentsView.as_view(), name='bulk_import_students'),
    
    # Entry and Scanning URLs
    path('verify-qr/', VerifyQRCodeView.as_view(), name='verify_qr_code'),
    path('entry-logs/', EntryLogListView.as_view(), name='entry_log_list'),
    path('lost-card-scans/', LostCardScansListView.as_view(), name='lost_card_scans_list'),
    
    # Admin Dashboard
    path('admin/dashboard/stats/', AdminDashboardStatsView.as_view(), name='admin_dashboard_stats'),
]