"""
合并参考：复制需要的 class／field 到嘉伦的 main/models.py。

假设原专案已经存在：
- django.contrib.auth.models.User
- CourseChapter
- CourseLesson
- LessonProgress

不要直接把这个文件当成独立 Django app 使用。
"""
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# 若嘉伦的 LessonProgress 尚无这些栏位，加入原 class：
# view_count = models.PositiveIntegerField(default=0, verbose_name="开启观看次数")
# page_open_count = models.PositiveIntegerField(default=0, verbose_name="单元页开启次数")
# replayed_seconds = models.PositiveIntegerField(default=0, verbose_name="重复观看秒数")


class Quiz(models.Model):
    QUIZ_TYPE_CHOICES = [
        ('standard', '章节测验'),
        ('remedial', 'AI 补救练习'),
    ]

    chapter = models.OneToOneField(
        'CourseChapter', on_delete=models.CASCADE,
        related_name='quiz', verbose_name='章节',
    )
    title = models.CharField(max_length=200, verbose_name='测验标题')
    pass_score = models.PositiveSmallIntegerField(
        default=60,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='及格分数',
    )
    is_published = models.BooleanField(default=True, verbose_name='是否启用')
    quiz_type = models.CharField(
        max_length=20, choices=QUIZ_TYPE_CHOICES,
        default='standard', verbose_name='测验类型',
    )
    source_attempt = models.ForeignKey(
        'QuizAttempt', on_delete=models.SET_NULL, blank=True, null=True,
        related_name='remedial_quizzes',
        verbose_name='弱点来源作答（仅 AI 补救练习使用）',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立时间')

    def question_count(self):
        return self.questions.count()

    def __str__(self):
        return f'{self.chapter.title} - {self.title}'

    class Meta:
        verbose_name = '章节测验'
        verbose_name_plural = '章节测验'


class QuizQuestion(models.Model):
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE,
        related_name='questions', verbose_name='测验',
    )
    question_text = models.TextField(verbose_name='题目')
    options = models.JSONField(default=list, verbose_name='选项清单')
    correct_index = models.PositiveSmallIntegerField(default=0, verbose_name='正确选项索引')
    explanation = models.TextField(blank=True, default='', verbose_name='解析')
    sort_order = models.PositiveIntegerField(default=1, verbose_name='题目顺序')
    topic_tag = models.CharField(
        max_length=100, blank=True, default='', verbose_name='知识点标签',
    )

    def __str__(self):
        return f'{self.quiz.title} - Q{self.sort_order}'

    class Meta:
        verbose_name = '测验题目'
        verbose_name_plural = '测验题目'
        ordering = ['quiz', 'sort_order', 'id']


class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='使用者')
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE,
        related_name='attempts', verbose_name='测验',
    )
    score = models.PositiveSmallIntegerField(default=0, verbose_name='分数')
    correct_count = models.PositiveSmallIntegerField(default=0, verbose_name='答对题数')
    total_count = models.PositiveSmallIntegerField(default=0, verbose_name='总题数')
    weak_topics = models.JSONField(
        default=list, blank=True, verbose_name='AI 弱点知识点',
        help_text='[{"topic": str, "issue_description": str, "severity": "low|medium|high"}, ...]',
    )
    strong_topics = models.JSONField(default=list, blank=True, verbose_name='AI 已掌握知识点')
    overall_feedback = models.TextField(blank=True, default='', verbose_name='AI 整体回馈')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作答时间')

    @property
    def accuracy_rate(self):
        return self.correct_count / self.total_count if self.total_count else 0

    def is_passed(self):
        return self.score >= self.quiz.pass_score

    def __str__(self):
        return f'{self.user.username} - {self.quiz.title} - {self.score}分'

    class Meta:
        verbose_name = '测验作答纪录'
        verbose_name_plural = '测验作答纪录'
        ordering = ['-created_at']


class QuizAnswer(models.Model):
    attempt = models.ForeignKey(
        QuizAttempt, on_delete=models.CASCADE,
        related_name='answers', verbose_name='作答纪录',
    )
    question = models.ForeignKey(
        QuizQuestion, on_delete=models.CASCADE, verbose_name='题目',
    )
    selected_index = models.SmallIntegerField(default=-1, verbose_name='所选选项索引')
    is_correct = models.BooleanField(default=False, verbose_name='是否答对')

    def __str__(self):
        return f'{self.attempt_id} - Q{self.question_id} - {"对" if self.is_correct else "错"}'

    class Meta:
        verbose_name = '测验答题明细'
        verbose_name_plural = '测验答题明细'
        ordering = ['attempt', 'question']


class CourseSummary(models.Model):
    """Power BI 匯出会使用；若只整合两项 AI 功能，可以暂时不加入。"""
    course = models.OneToOneField(
        'Course', on_delete=models.CASCADE,
        related_name='ai_summary', verbose_name='课程',
    )
    summary = models.TextField(blank=True, default='', verbose_name='摘要内容')
    core_concepts = models.JSONField(default=list, blank=True, verbose_name='核心概念')
    key_terms = models.JSONField(default=list, blank=True, verbose_name='关键名词')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    def __str__(self):
        return f'{self.course.title} - AI 摘要'

