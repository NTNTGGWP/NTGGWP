"""把这些 import／admin class 合并到 main/admin.py。"""
from django.contrib import admin
from .models import Quiz, QuizQuestion, QuizAttempt


class QuizQuestionInline(admin.StackedInline):
    model = QuizQuestion
    extra = 1
    fields = (
        'sort_order', 'question_text', 'options', 'correct_index',
        'explanation', 'topic_tag',
    )


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('chapter', 'title', 'question_count', 'pass_score', 'is_published')
    search_fields = ('chapter__course__title', 'chapter__title', 'title')
    list_filter = ('is_published', 'chapter__course')
    autocomplete_fields = ('chapter',)
    inlines = [QuizQuestionInline]


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'correct_count', 'total_count', 'created_at')
    search_fields = ('user__username', 'quiz__title')
    list_filter = ('quiz__chapter__course',)
    readonly_fields = (
        'user', 'quiz', 'score', 'correct_count', 'total_count',
        'weak_topics', 'strong_topics', 'overall_feedback', 'created_at',
    )

