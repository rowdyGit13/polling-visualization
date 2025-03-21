from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.db.models import Count, F, Sum, Q
from django.contrib.auth.models import User
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import numpy as np
import os

from .models import Question, Choice, UserResponse, QuestionAnalytics
from .forms import CustomUserCreationForm

# Index view to show a list of questions
def index(request):
    cache_key = 'latest_questions'
    latest_question_list = cache.get(cache_key)
    
    if not latest_question_list:
        # Only get published questions
        latest_question_list = Question.published.order_by("-pub_date")[:5]
        cache.set(cache_key, latest_question_list, 60 * 5)  # Cache for 5 minutes
    
    # Get categories, filtering out empty ones
    categories = Question.objects.exclude(
        Q(category__isnull=True) | Q(category='')
    ).values('category').annotate(
        count=Count('id')
    ).order_by('category')
        
    context = {
        "latest_question_list": latest_question_list,
        "categories": categories,
    }
    return render(request, "polls/index.html", context)

# Detail view to see a specific question and its choices
def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    # Check if the user has already responded to this question
    user_response = None
    if request.user.is_authenticated:
        try:
            user_response = UserResponse.objects.get(
                user=request.user, 
                question=question
            )
        except UserResponse.DoesNotExist:
            pass
    
    return render(request, "polls/detail.html", {
        "question": question,
        "user_response": user_response
    })

# Results view to see the results of a specific question
@cache_page(60 * 15)  # Cache for 15 minutes
def results(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    choices = list(question.choice_set.all())
    total_votes = sum(choice.votes for choice in choices)
    
    # Calculate percentages
    choices_with_percentage = []
    for choice in choices:
        if total_votes > 0:
            percentage = round((choice.votes / total_votes) * 100)
        else:
            percentage = 0
        choices_with_percentage.append({
            'choice': choice,
            'percentage': percentage
        })
    
    # Generate matplotlib chart
    chart_img = generate_results_chart(question, choices, total_votes)
    
    # Check if user has responded
    user_response = None
    if request.user.is_authenticated:
        try:
            user_response = UserResponse.objects.get(user=request.user, question=question)
        except UserResponse.DoesNotExist:
            pass
    
    return render(request, "polls/results.html", {
        "question": question,
        "choices_with_percentage": choices_with_percentage,
        "total_votes": total_votes,
        "chart_img": chart_img,
        "user_response": user_response
    })

def generate_results_chart(question, choices, total_votes):
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Data for plotting
    labels = [choice.choice_text for choice in choices]
    values = [choice.votes for choice in choices]
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(values)))
    
    # Create horizontal bar chart
    bars = ax.barh(labels, values, color=colors)
    
    # Add values and percentage annotations
    for bar in bars:
        width = bar.get_width()
        percentage = f'{(width/total_votes)*100:.1f}%' if total_votes > 0 else '0%'
        ax.text(
            width + 0.5, 
            bar.get_y() + bar.get_height()/2, 
            f'{int(width)} ({percentage})', 
            va='center'
        )
    
    # Customize chart
    ax.set_title(f'Results: {question.question_text}', fontsize=14, pad=20)
    ax.set_xlabel('Number of Votes', fontsize=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    
    # Convert plot to base64 image for template rendering
    buffer = io.BytesIO()
    canvas = FigureCanvas(fig)
    canvas.print_png(buffer)
    plt.close(fig)
    
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f'data:image/png;base64,{image_base64}'

# Vote view to submit a response to a question
@login_required
def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    
    # Use transaction to ensure data consistency
    with transaction.atomic():
        # Try to get existing response
        try:
            user_response = UserResponse.objects.get(
                user=request.user,
                question=question
            )
            # If changing vote, decrement the previous choice's votes
            if user_response.choice != selected_choice:
                user_response.choice.votes = F('votes') - 1
                user_response.choice.save()
                # Update the response to the new choice
                user_response.choice = selected_choice
                user_response.save()
                
                # Increment the selected choice's votes
                selected_choice.votes = F('votes') + 1
                selected_choice.save()
                
                messages.success(request, "Your vote has been updated!")
            else:
                messages.info(request, "You've already voted for this choice!")
                
        except UserResponse.DoesNotExist:
            # Create new response
            UserResponse.objects.create(
                user=request.user,
                question=question,
                choice=selected_choice
            )
            
            # Increment the vote count
            selected_choice.votes = F('votes') + 1
            selected_choice.save()
            
            messages.success(request, "Your vote has been recorded!")
        
        # Update analytics
        analytics, created = QuestionAnalytics.objects.get_or_create(question=question)
        analytics.update_analytics()
        
        # Invalidate cache for results page
        cache.delete(f'views.decorators.cache.cache_page.{request.path}')
    
    return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))

# Dashboard to view all user's responses
@login_required
def user_dashboard(request):
    user_responses = UserResponse.objects.filter(user=request.user).select_related(
        'question', 'choice'
    ).order_by('-response_date')
    
    # Aggregate user stats
    stats = {
        'total_votes': user_responses.count(),
        'questions_by_category': Question.objects.filter(
            userresponse__user=request.user
        ).values('category').annotate(count=Count('id')).order_by('-count'),
    }
    
    return render(request, "polls/dashboard.html", {
        "user_responses": user_responses,
        "stats": stats
    })

# User registration view
def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log in the user after registration
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect("polls:index")
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/register.html", {"form": form})

# Category view to filter questions by category
def category_view(request, category):
    questions = Question.published.filter(category=category).order_by('-pub_date')
    return render(request, "polls/category.html", {
        "category": category,
        "questions": questions
    })

# Statistics view for admin insights
@login_required
def statistics_view(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect("polls:index")
    
    # Get overall stats
    stats = {
        'total_questions': Question.objects.count(),
        'total_votes': UserResponse.objects.count(),
        'total_users': User.objects.count(),
        'active_users': UserResponse.objects.values('user').distinct().count(),
        'questions_by_category': Question.objects.values('category').annotate(count=Count('id')).order_by('-count'),
        'most_popular_questions': Question.objects.annotate(response_count=Count('userresponse')).order_by('-response_count')[:5],
    }
    
    return render(request, "polls/statistics.html", {"stats": stats})

# Add this simple view for Vercel debugging
def vercel_landing(request):
    """Super simple view to test Vercel deployment"""
    return HttpResponse(
        '<html><body><h1>Polls App is Running!</h1>'
        '<p>This is a minimal page for testing Vercel deployment.</p>'
        f'<p>Running in environment: {os.environ.get("VERCEL_DEPLOYMENT", "local")}</p>'
        '</body></html>'
    )
