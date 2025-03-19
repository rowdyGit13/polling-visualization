from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Question, Choice, UserResponse, QuestionAnalytics


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'choice_text', 'votes']
        read_only_fields = ['votes']


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True, source='choice_set')
    author_username = serializers.ReadOnlyField(source='author.username')
    
    class Meta:
        model = Question
        fields = ['id', 'question_text', 'pub_date', 'category', 
                  'is_published', 'author_username', 'choices']
        read_only_fields = ['author_username']
        
    def create(self, validated_data):
        choices_data = self.context.get('choices', [])
        
        # Create the question
        question = Question.objects.create(**validated_data)
        
        # Create choices for the question
        for choice_data in choices_data:
            Choice.objects.create(question=question, **choice_data)
            
        return question


class UserResponseSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    question_text = serializers.ReadOnlyField(source='question.question_text')
    choice_text = serializers.ReadOnlyField(source='choice.choice_text')
    
    class Meta:
        model = UserResponse
        fields = ['id', 'username', 'question_text', 'choice_text', 'response_date']
        read_only_fields = ['response_date']


class QuestionAnalyticsSerializer(serializers.ModelSerializer):
    question_text = serializers.ReadOnlyField(source='question.question_text')
    
    class Meta:
        model = QuestionAnalytics
        fields = ['id', 'question_text', 'total_votes', 'last_vote_date']
        read_only_fields = ['total_votes', 'last_vote_date']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined']
        read_only_fields = ['date_joined'] 