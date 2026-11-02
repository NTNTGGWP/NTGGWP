"""把这些 path 加入 main/urls.py 的 urlpatterns。"""
from django.urls import path
from . import views

urlpatterns = [
    path('chapter/<int:chapter_id>/quiz/', views.take_quiz, name='take_quiz'),
    path('quiz/<int:quiz_id>/submit/', views.submit_quiz, name='submit_quiz'),
    path('quiz/attempt/<int:attempt_id>/result/', views.quiz_result, name='quiz_result'),
    path('course/<int:course_id>/diagnosis/', views.learning_diagnosis, name='learning_diagnosis'),
    path('chapter/<int:chapter_id>/remedial/', views.remedial_quiz, name='remedial_quiz'),
]

