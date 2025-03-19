import datetime
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Sum
from django.conf import settings

# Conditionally import PostgreSQL-specific fields
try:
    from django.contrib.postgres.fields import ArrayField
    from django.contrib.postgres.search import SearchVectorField
    from django.contrib.postgres.indexes import GinIndex
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    # Create dummy ArrayField for SQLite compatibility
    class ArrayField(models.TextField):
        def __init__(self, base_field, size=None, **kwargs):
            kwargs['null'] = kwargs.get('null', True)
            super().__init__(**kwargs)
        
        def deconstruct(self):
            name, path, args, kwargs = super().deconstruct()
            kwargs['base_field'] = models.CharField(max_length=50)
            return name, path, args, kwargs


class PublishedQuestionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions', null=True)
    category = models.CharField(max_length=100, blank=True)
    is_published = models.BooleanField(default=True)
    
    # Add custom manager
    objects = models.Manager()
    published = PublishedQuestionManager()
    
    class Meta:
        indexes = [
            models.Index(fields=['pub_date']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return self.question_text
    
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    def __str__(self):
        return self.choice_text

class UserResponse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    response_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'question']
        
    def __str__(self):
        return f"{self.user.username} - {self.question.question_text[:30]}"

class QuestionAnalytics(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE)
    total_votes = models.IntegerField(default=0)
    last_vote_date = models.DateTimeField(null=True, blank=True)
    
    def update_analytics(self):
        self.total_votes = self.question.choice_set.aggregate(Sum('votes'))['votes__sum'] or 0
        latest_response = UserResponse.objects.filter(question=self.question).order_by('-response_date').first()
        if latest_response:
            self.last_vote_date = latest_response.response_date
        self.save()
        
    def __str__(self):
        return f"Analytics for {self.question.question_text[:30]}"

# Only create this model if PostgreSQL is available, otherwise create a simplified version
if POSTGRES_AVAILABLE:
    class QuestionWithMetadata(models.Model):
        question = models.OneToOneField(Question, on_delete=models.CASCADE)
        tags = ArrayField(models.CharField(max_length=50), blank=True, default=list)
        metadata = models.JSONField(default=dict, blank=True)
        search_vector = SearchVectorField(null=True)
        
        class Meta:
            indexes = [
                GinIndex(fields=['search_vector'])
            ]
            
        def __str__(self):
            return f"Metadata for {self.question.question_text[:30]}"
else:
    class QuestionWithMetadata(models.Model):
        question = models.OneToOneField(Question, on_delete=models.CASCADE)
        tags_text = models.TextField(blank=True, help_text="Comma-separated tags")
        metadata_text = models.TextField(blank=True, help_text="JSON-formatted metadata")
        
        def __str__(self):
            return f"Metadata for {self.question.question_text[:30]}"