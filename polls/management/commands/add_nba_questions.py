from django.core.management.base import BaseCommand
from polls.models import Question, Choice
from django.utils import timezone

class Command(BaseCommand):
    help = 'Adds NBA poll questions to the database'

    def handle(self, *args, **kwargs):
        questions = [
            {
                "question_text": "Who is the greatest NBA player of all time?",
                "choices": ["Michael Jordan", "LeBron James", "Kobe Bryant", "Kareem Abdul-Jabbar", "Magic Johnson"],
                "category": "NBA"
            },
            {
                "question_text": "Which NBA team has the brightest future?",
                "choices": ["Boston Celtics", "Minnesota Timberwolves", "Oklahoma City Thunder", "San Antonio Spurs", "New Orleans Pelicans"],
                "category": "NBA"
            },
            {
                "question_text": "What's the most exciting part of an NBA game?",
                "choices": ["Clutch moments", "Dunks and highlights", "Team strategies", "Individual matchups", "Comeback victories"],
                "category": "NBA"
            },
            {
                "question_text": "Which playing style is most entertaining to watch?",
                "choices": ["High-scoring offense", "Lockdown defense", "Fast-paced transition", "Three-point shooting", "Post play and fundamentals"],
                "category": "NBA"
            },
            {
                "question_text": "What change would most improve the NBA?",
                "choices": ["Shorter regular season", "In-season tournament", "Eliminating the draft", "Rule changes for less fouls", "Expanded playoffs"],
                "category": "NBA"
            }
        ]
        
        for q_data in questions:
            # Check if question already exists
            if not Question.objects.filter(question_text=q_data["question_text"]).exists():
                q = Question.objects.create(
                    question_text=q_data["question_text"],
                    pub_date=timezone.now(),
                    category=q_data["category"],
                    is_published=True
                )
                
                # Add choices
                for choice_text in q_data["choices"]:
                    Choice.objects.create(
                        question=q,
                        choice_text=choice_text,
                        votes=0
                    )
                
                self.stdout.write(self.style.SUCCESS(f'Added question: "{q_data["question_text"]}"'))
            else:
                self.stdout.write(self.style.WARNING(f'Question already exists: "{q_data["question_text"]}"'))
        
        self.stdout.write(self.style.SUCCESS('Successfully added NBA questions')) 