from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.UploadView.as_view()),
    path('summary/<int:upload_id>/', views.SummaryView.as_view()),
    path('data/<int:upload_id>/', views.DataView.as_view()),
    path('history/', views.HistoryView.as_view()),
    path('report/<int:upload_id>/pdf/', views.ReportPdfView.as_view()),
]
