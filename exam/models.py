from django.db import models
import datetime

# Create your models here.
class Exam(models.Model):
    exam_id = models.CharField(primary_key=True, max_length=60)
    exam_title = models.TextField()
    date = models.DateTimeField()
    content_id = models.CharField(max_length=32)
    channel_id = models.CharField(max_length=32)
    question_count = models.IntegerField()
    student_id = models.CharField(max_length=60)
    correct_questions = models.IntegerField()
    #attempted_questions = models.IntegerField(default=0)
    question_sources = models.TextField(default="")

    def __str__(self):
    	return self.exam_title

class creation(models.Model):
    student_id = models.CharField(max_length=60)
    exam_count = models.IntegerField()
    active_exam_count = models.IntegerField()
    complete_exam_count = models.IntegerField()

    def __str__(self):
        return self.student_id

