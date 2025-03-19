from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.db.models import Count, Sum, F
from django.conf import settings
import csv
import io
import logging

logger = logging.getLogger(__name__)

@shared_task
def update_all_analytics():
    """
    Update all question analytics records
    """
    from .models import QuestionAnalytics
    
    count = 0
    for analytics in QuestionAnalytics.objects.select_related('question').all():
        try:
            analytics.update_analytics()
            count += 1
        except Exception as e:
            logger.error(f"Error updating analytics for question {analytics.question_id}: {str(e)}")
    
    logger.info(f"Updated analytics for {count} questions")
    return f"Updated analytics for {count} questions"


@shared_task
def generate_daily_report():
    """
    Generate a daily report of polling activity
    """
    from .models import Question, UserResponse, QuestionWithMetadata
    
    today = timezone.now().date()
    yesterday = today - timezone.timedelta(days=1)
    
    # Get yesterday's data
    new_questions = Question.objects.filter(pub_date__date=yesterday).count()
    total_votes = UserResponse.objects.filter(response_date__date=yesterday).count()
    
    # Most active categories yesterday
    category_activity = Question.objects.filter(
        userresponse__response_date__date=yesterday
    ).values('category').annotate(
        votes=Count('userresponse')
    ).order_by('-votes')[:5]
    
    # Popular questions by tags
    popular_tags = QuestionWithMetadata.objects.filter(
        question__userresponse__response_date__date=yesterday
    ).values('tags').annotate(
        count=Count('question__userresponse')
    ).order_by('-count')[:5]
    
    # Format report
    report = f"Daily Report for {yesterday.strftime('%Y-%m-%d')}\n\n"
    report += f"New questions: {new_questions}\n"
    report += f"Total votes: {total_votes}\n\n"
    
    report += "Popular categories:\n"
    for cat in category_activity:
        report += f"- {cat['category'] or 'Uncategorized'}: {cat['votes']} votes\n"
    
    report += "\nPopular tags:\n"
    for tag_data in popular_tags:
        tags = tag_data['tags'] if tag_data['tags'] else ["No tags"]
        report += f"- {', '.join(tags)}: {tag_data['count']} votes\n"
    
    # Log report
    logger.info(report)
    
    # Email report to admins if configured
    if hasattr(settings, 'ADMIN_EMAILS') and settings.ADMIN_EMAILS:
        try:
            send_mail(
                f"Polls Daily Report - {yesterday.strftime('%Y-%m-%d')}",
                report,
                settings.DEFAULT_FROM_EMAIL,
                settings.ADMIN_EMAILS,
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send daily report email: {str(e)}")
    
    return report


@shared_task
def export_poll_data(question_id):
    """
    Export all votes for a specific poll to CSV
    """
    from .models import Question, UserResponse
    
    try:
        question = Question.objects.get(id=question_id)
        responses = UserResponse.objects.filter(question=question).select_related('user', 'choice')
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Username', 'Choice', 'Timestamp'])
        
        # Write data
        for response in responses:
            writer.writerow([
                response.user.username,
                response.choice.choice_text,
                response.response_date.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        # Get CSV content
        csv_content = output.getvalue()
        
        # Log success
        logger.info(f"Successfully exported data for question {question_id}")
        
        return csv_content
        
    except Question.DoesNotExist:
        logger.error(f"Question {question_id} not found")
        return f"Question {question_id} not found"
    except Exception as e:
        logger.error(f"Error exporting poll data for question {question_id}: {str(e)}")
        return f"Error: {str(e)}" 