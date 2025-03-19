from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone

from .models import Question, Choice, UserResponse, QuestionAnalytics
from .serializers import (
    QuestionSerializer, 
    ChoiceSerializer, 
    UserResponseSerializer,
    QuestionAnalyticsSerializer,
    UserSerializer
)


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow authors of a question to edit it
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the author
        return obj.author == request.user


class QuestionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing poll questions
    """
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['question_text', 'category']
    ordering_fields = ['pub_date', 'category']
    ordering = ['-pub_date']
    
    def get_queryset(self):
        """
        This view returns a list of all questions,
        but can be filtered by category or published status
        """
        queryset = Question.objects.all()
        
        # Filter by category if provided
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
            
        # Filter by published status if provided
        is_published = self.request.query_params.get('is_published')
        if is_published is not None:
            is_published = is_published.lower() == 'true'
            queryset = queryset.filter(is_published=is_published)
            
        return queryset
    
    def perform_create(self, serializer):
        """Set the author to the current user when creating a question"""
        serializer.save(author=self.request.user, pub_date=timezone.now())
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def vote(self, request, pk=None):
        """Custom action to vote on a question"""
        question = self.get_object()
        
        try:
            choice_id = request.data.get('choice')
            if not choice_id:
                return Response(
                    {'detail': 'You must specify a choice'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            choice = get_object_or_404(Choice, id=choice_id, question=question)
            
            with transaction.atomic():
                # Try to get existing response
                try:
                    user_response = UserResponse.objects.get(
                        user=request.user,
                        question=question
                    )
                    
                    # If changing vote, update
                    if user_response.choice != choice:
                        user_response.choice.votes -= 1
                        user_response.choice.save()
                        
                        user_response.choice = choice
                        user_response.save()
                        
                        choice.votes += 1
                        choice.save()
                        
                        message = "Your vote has been updated"
                    else:
                        message = "You have already voted for this choice"
                        
                except UserResponse.DoesNotExist:
                    # Create new response
                    UserResponse.objects.create(
                        user=request.user,
                        question=question,
                        choice=choice
                    )
                    
                    choice.votes += 1
                    choice.save()
                    
                    message = "Your vote has been recorded"
                
                # Update analytics
                analytics, created = QuestionAnalytics.objects.get_or_create(question=question)
                analytics.update_analytics()
            
            return Response({'detail': message})
            
        except Exception as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class ChoiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing choices
    """
    serializer_class = ChoiceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """
        This view returns all choices,
        but can be filtered by question if provided
        """
        queryset = Choice.objects.all()
        
        # Filter by question if provided
        question_id = self.request.query_params.get('question')
        if question_id:
            queryset = queryset.filter(question_id=question_id)
            
        return queryset
    
    def perform_create(self, serializer):
        """Set the question when creating a choice"""
        question_id = self.request.data.get('question')
        question = get_object_or_404(Question, pk=question_id)
        
        # Check if the user is the author of the question
        if question.author != self.request.user:
            raise permissions.PermissionDenied("You can only add choices to your own questions")
            
        serializer.save(question=question)


class UserResponseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing user responses
    """
    serializer_class = UserResponseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        This view returns all responses for the current user,
        or for a specific question if question_id is provided
        """
        user = self.request.user
        queryset = UserResponse.objects.filter(user=user)
        
        # Filter by question if provided
        question_id = self.request.query_params.get('question')
        if question_id:
            queryset = queryset.filter(question_id=question_id)
            
        return queryset.order_by('-response_date')


class QuestionAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing question analytics
    """
    serializer_class = QuestionAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Staff can see all analytics, authors can see their own questions' analytics
        """
        user = self.request.user
        
        if user.is_staff:
            return QuestionAnalytics.objects.all()
        else:
            return QuestionAnalytics.objects.filter(question__author=user) 