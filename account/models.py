from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
# Create your models here.

class UserInfoSchool(models.Model):
    school_id = models.BigIntegerField(primary_key=True)
    school_name = models.CharField(max_length=60)
    total_students = models.IntegerField()

    def __str__(self):
    	return self.school_name

class UserInfoClass(models.Model):
    class_id = models.BigIntegerField(primary_key=True)
    class_name = models.CharField(max_length=60)
    parent = models.BigIntegerField()
    total_students = models.IntegerField()
    
    def __str__(self):
        return self.class_name

class UserInfoStudent(models.Model):
    student_id = models.BigIntegerField(primary_key=True)
    student_name = models.CharField(max_length=60)
    parent = models.BigIntegerField()

class UserRoleCollectionMapping(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    institute_id = models.ForeignKey(UserInfoSchool, on_delete=models.CASCADE, null=True, blank=True)
    class_id = models.ForeignKey(UserInfoClass, on_delete=models.CASCADE, null=True, blank=True)

class Content(models.Model):
    topic_id = models.CharField(max_length=32,primary_key=True)
    topic_name = models.CharField(max_length=140)
    content_id = models.CharField(max_length=32)
    channel_id = models.CharField(max_length=32)
    total_questions = models.IntegerField()
    sub_topics = models.TextField()
    sub_topics_total = models.IntegerField(default=0)

class MasteryLevelStudent(models.Model):
    id = models.CharField(max_length=40,primary_key=True)
    student_id = models.ForeignKey(UserInfoStudent, on_delete=models.CASCADE)
    content_id = models.CharField(max_length=32)
    channel_id = models.CharField(max_length=32)
    date = models.DateTimeField()
    completed_questions = models.IntegerField(default=0)
    correct_questions = models.IntegerField(default=0)
    attempt_questions = models.IntegerField(default=0)
    # completed = models.BooleanField(default=False)
    mastered = models.IntegerField(default=0)
    attempt_exercise = models.IntegerField(default=0)

class MasteryLevelClass(models.Model):
    id = models.CharField(max_length=40,primary_key=True)
    class_id = models.ForeignKey(UserInfoClass, on_delete=models.CASCADE)
    content_id = models.CharField(max_length=32)
    channel_id = models.CharField(max_length=32)
    date = models.DateTimeField()
    completed_questions = models.IntegerField(default=0)
    correct_questions = models.IntegerField(default=0)
    attempt_questions = models.IntegerField(default=0)
    # students_completed = models.IntegerField(default=0)
    mastered = models.IntegerField(default=0)
    attempt_exercise = models.IntegerField(default=0)

class MasteryLevelSchool(models.Model):
    id = models.CharField(max_length=40,primary_key=True)
    school_id = models.ForeignKey(UserInfoSchool, on_delete=models.CASCADE)
    content_id = models.CharField(max_length=32)
    channel_id = models.CharField(max_length=32)
    date = models.DateTimeField()
    completed_questions = models.IntegerField(default=0)
    correct_questions = models.IntegerField(default=0)
    attempt_questions = models.IntegerField(default=0)
    # students_completed = models.IntegerField(default=0)
    mastered = models.IntegerField(default=0)
    attempt_exercise = models.IntegerField(default=0)

class LatestFetchDate(models.Model):
    date_id = models.IntegerField(primary_key=True)
    latest_date = models.DateTimeField()

