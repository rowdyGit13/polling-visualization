from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from . import api_views

# Create a router for API views
router = DefaultRouter()
router.register(r'questions', api_views.QuestionViewSet, basename='question')
router.register(r'choices', api_views.ChoiceViewSet, basename='choice')
router.register(r'responses', api_views.UserResponseViewSet, basename='response')
router.register(r'analytics', api_views.QuestionAnalyticsViewSet, basename='analytics')

app_name = "polls"
urlpatterns = [
    # Debug view for Vercel
    path("vercel-test/", views.vercel_landing, name="vercel_landing"),
    
    # Standard web views
    path("", views.index, name="index"),
    path("<int:question_id>/", views.detail, name="detail"),
    path("<int:question_id>/results/", views.results, name="results"),
    path("<int:question_id>/vote/", views.vote, name="vote"),
    path("dashboard/", views.user_dashboard, name="dashboard"),
    path("register/", views.register, name="register"),
    path("category/<str:category>/", views.category_view, name="category"),
    path("statistics/", views.statistics_view, name="statistics"),
    
    # API endpoints
    path('api/', include(router.urls)),
]