from django.db import models

# Create your models here.
class Lesson(models.Model):
    lesson_id = models.BigIntegerField(primary_key=True)
    lesson_name = models.CharField(max_length=60)
    class_id = models.IntegerField()
    lesson_content = models.TextField(null=False, blank=False)
    date = models.DateTimeField()

    def __str__(self):
    	return self.lesson_name
