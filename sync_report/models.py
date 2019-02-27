from django.db import models
import datetime
from django.utils import timezone
from account.models import UserInfoSchool, UserInfoClass
# Create your models here.

class last_sync_date(models.Model):
	school_id = models.ForeignKey(UserInfoSchool)
	school_name = models.CharField(max_length=100, default="")
	# class_id = models.ForeignKey(UserInfoClass)
	class_name = models.CharField(max_length=150)
	sync_date = models.DateField(default=datetime.date.today)
	id_class_name = models.CharField(max_length=200)
	class Meta:
		db_table = 'last_sync_date'
