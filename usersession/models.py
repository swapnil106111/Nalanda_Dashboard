from django.db import models
from account.models import UserInfoStudent, UserInfoClass, UserInfoSchool
# Create your models here.
class Student(models.Model):
	student_id = models.ForeignKey(UserInfoStudent, on_delete=models.CASCADE)
	date = models.DateTimeField()
	total_usage = models.BigIntegerField(default=0)

class Class(models.Model):
	class_id = models.ForeignKey(UserInfoClass, on_delete=models.CASCADE)
	date = models.DateTimeField()
	total_usage = models.BigIntegerField(default=0)

class School(models.Model):
	school_id = models.ForeignKey(UserInfoSchool, on_delete=models.CASCADE)
	date = models.DateTimeField()
	total_usage = models.BigIntegerField(default=0)
	
		