from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from .models import Question, Choice, UserResponse, QuestionAnalytics, QuestionWithMetadata, POSTGRES_AVAILABLE

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2
    min_num = 2

class QuestionAnalyticsInline(admin.StackedInline):
    model = QuestionAnalytics
    can_delete = False
    verbose_name_plural = 'Analytics'
    readonly_fields = ('total_votes', 'last_vote_date')

class QuestionMetadataInline(admin.StackedInline):
    model = QuestionWithMetadata
    can_delete = False
    verbose_name_plural = 'Metadata'

class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["question_text", "author", "category", "is_published"]}),
        ("Date information", {"fields": ["pub_date"]}),
    ]
    inlines = [ChoiceInline, QuestionAnalyticsInline, QuestionMetadataInline]
    list_display = ["question_text", "pub_date", "category", "is_published", "was_published_recently", "vote_count"]
    list_filter = ["pub_date", "category", "is_published", "author"]
    search_fields = ["question_text", "category"]
    list_editable = ["category", "is_published"]
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            vote_count=Count('userresponse')
        )
        return queryset
    
    def vote_count(self, obj):
        return obj.vote_count
    vote_count.admin_order_field = 'vote_count'
    vote_count.short_description = 'Votes'

class UserResponseAdmin(admin.ModelAdmin):
    list_display = ["user", "question_link", "choice_text", "response_date"]
    list_filter = ["response_date", "question", "user"]
    search_fields = ["user__username", "question__question_text"]
    
    def question_link(self, obj):
        url = f"/admin/polls/question/{obj.question.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.question.question_text)
    question_link.short_description = 'Question'
    
    def choice_text(self, obj):
        return obj.choice.choice_text
    choice_text.short_description = 'Choice'

class QuestionAnalyticsAdmin(admin.ModelAdmin):
    list_display = ["question", "total_votes", "last_vote_date"]
    list_filter = ["last_vote_date"]
    search_fields = ["question__question_text"]
    readonly_fields = ["total_votes", "last_vote_date"]

class QuestionWithMetadataAdmin(admin.ModelAdmin):
    list_display = ["question", "display_tags"]
    search_fields = ["question__question_text"]
    
    def display_tags(self, obj):
        if POSTGRES_AVAILABLE:
            return ", ".join(obj.tags) if obj.tags else "No tags"
        else:
            return obj.tags_text if obj.tags_text else "No tags"
    display_tags.short_description = 'Tags'

admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)
admin.site.register(UserResponse, UserResponseAdmin)
admin.site.register(QuestionAnalytics, QuestionAnalyticsAdmin)
admin.site.register(QuestionWithMetadata, QuestionWithMetadataAdmin)
