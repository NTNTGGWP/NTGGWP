"""
合并参考：把这些 import 与 view 合并到嘉伦既有 main/views.py。
不要整份覆盖嘉伦的 views.py。
"""
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import (
    Course, CourseChapter, Enrollment, Quiz, QuizAnswer, QuizAttempt,
)


@login_required
def take_quiz(request, chapter_id):
    chapter = get_object_or_404(
        CourseChapter.objects.select_related('course'), id=chapter_id,
    )
    course = chapter.course
    quiz = Quiz.objects.filter(chapter=chapter, is_published=True).first()
    if not quiz:
        return redirect('watch_course', course_id=course.id)

    enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    is_teacher = course.teacher_id == request.user.id
    if not (enrolled or is_teacher):
        return redirect('course_detail', course_id=course.id)

    questions = list(quiz.questions.all())
    if not questions:
        return redirect('watch_course', course_id=course.id)

    last_attempt = QuizAttempt.objects.filter(user=request.user, quiz=quiz).first()
    return render(request, 'main/take_quiz.html', {
        'course': course,
        'chapter': chapter,
        'quiz': quiz,
        'questions': questions,
        'last_attempt': last_attempt,
    })


@login_required
def submit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz.objects.select_related('chapter__course'), id=quiz_id)
    course = quiz.chapter.course

    enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    is_teacher = course.teacher_id == request.user.id
    if not (enrolled or is_teacher):
        return redirect('course_detail', course_id=course.id)
    if request.method != 'POST':
        return redirect('take_quiz', chapter_id=quiz.chapter_id)

    questions = list(quiz.questions.all())
    if not questions:
        return redirect('watch_course', course_id=course.id)

    with transaction.atomic():
        attempt = QuizAttempt.objects.create(
            user=request.user, quiz=quiz, total_count=len(questions),
        )
        correct = 0
        for question in questions:
            raw = request.POST.get(f'q_{question.id}')
            try:
                selected = int(raw)
            except (TypeError, ValueError):
                selected = -1
            is_correct = selected == question.correct_index
            correct += int(is_correct)
            QuizAnswer.objects.create(
                attempt=attempt,
                question=question,
                selected_index=selected,
                is_correct=is_correct,
            )
        attempt.correct_count = correct
        attempt.score = round(correct / len(questions) * 100)
        attempt.save(update_fields=['correct_count', 'score'])

        # 依真实错题写入结构化弱点，供 AI 与 Power BI 使用。
        from . import ai_diagnosis
        ai_diagnosis.diagnose_attempt(attempt)

    return redirect('quiz_result', attempt_id=attempt.id)


@login_required
def quiz_result(request, attempt_id):
    attempt = get_object_or_404(
        QuizAttempt.objects.select_related('quiz__chapter__course'), id=attempt_id,
    )
    if attempt.user_id != request.user.id and not request.user.is_superuser:
        return redirect('home')

    answers = attempt.answers.select_related('question').all()
    previous_attempt = (
        QuizAttempt.objects.filter(
            user=attempt.user,
            quiz=attempt.quiz,
            created_at__lt=attempt.created_at,
        )
        .order_by('-created_at')
        .first()
    )
    score_delta = attempt.score - previous_attempt.score if previous_attempt else None

    return render(request, 'main/quiz_result.html', {
        'attempt': attempt,
        'quiz': attempt.quiz,
        'chapter': attempt.quiz.chapter,
        'course': attempt.quiz.chapter.course,
        'answers': answers,
        'previous_attempt': previous_attempt,
        'score_delta': score_delta,
    })


@login_required
def learning_diagnosis(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    is_teacher = course.teacher_id == request.user.id
    if not (enrolled or is_teacher):
        return JsonResponse(
            {'ok': False, 'error': '请先加入课程再使用学习诊断。'}, status=403,
        )

    from . import ai_diagnosis
    return JsonResponse(ai_diagnosis.diagnose(request.user, course))


@login_required
def remedial_quiz(request, chapter_id):
    chapter = get_object_or_404(
        CourseChapter.objects.select_related('course'), id=chapter_id,
    )
    course = chapter.course
    enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    is_teacher = course.teacher_id == request.user.id
    if not (enrolled or is_teacher):
        return JsonResponse({'ok': False, 'error': '请先加入课程。'}, status=403)

    from . import ai_remedial
    return JsonResponse(ai_remedial.generate_remedial(request.user, chapter))

