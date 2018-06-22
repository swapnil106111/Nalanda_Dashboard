from contentusage.contentusagereport import BaseRoleAccess
from account.models import * 
from account.constants import *
from lesson.models import Lesson

import datetime
import json, time
from django.db.models import Count

class LessonDetails(BaseRoleAccess):
	""" Used to fetch the school/class of users based on role
	"""
	def __init__(self, user, parentLevel):
		super(self.__class__, self).__init__(user, parentLevel)
		self.parentLevelMethods = [self.getSchoolsData, self.getSchoolsData, self.getSchoolsData, self.getClassData]	
		self.totalschools = {}

	def convert_to_string(self, data):
		data['id'] = str(data['id'])
		return data

	def getSchoolsData(self):
		""" Used to show schools hierarchy for user
		Args:
			None
		Returns:
			totalschools(dict) : dict of schools with it's classes and students as a children
		"""
		school_list = []
		schools = UserInfoSchool.objects.filter(school_id__in = self.institutes)
		# Get all the schools, if schools exist
		for school in schools:
			school_info = {}
			classes_in_school = list(UserInfoClass.objects.filter(parent=school.school_id).extra(select={'id':'class_id','name':'class_name'}).values('id','name'))
			for classid in classes_in_school:
				lessons_in_class = list(Lesson.objects.filter(class_id=classid['id']).extra(select={'id':'lesson_id','name':'lesson_name'}).values('id','name'))
				for lesson in lessons_in_class:
					lesson['id'] = str(lesson['id'])
				classid['children'] = lessons_in_class
			school_info['id'] = str(school.school_id)
			school_info['name'] = school.school_name
			school_info['children'] = list(map(self.convert_to_string, classes_in_school))
			school_list.append(school_info)
		self.totalschools["schools"] = school_list
		return self.totalschools

	def getClassData(self):
		""" Used to get class data for user 
		Args:
			None
		Returns:
			totalschools(dict) : returns class details with it's students
		"""
		class_info = {}
		class_list = []
		classes = list(UserInfoClass.objects.filter(class_id__in = self.classes).extra(select={'id':'class_id','name':'class_name'}).values('id','name'))
		for classid in classes:
			class_info = {}
			lessons_in_class = list(UserInfoStudent.objects.filter(class_id=classid['id']).extra(select={'id':'lesson_id','name':'lesson_name'}).values('id','name'))
			for lesson in lessons_in_class:
					lesson['id'] = str(lesson['id'])
			class_info['children'] = lessons_in_class
			class_info['id'] = str(classid['id'])
			class_info['name'] = classid['name']
			class_list.append(class_info)
		self.totalschools["schools"] = class_list
		return self.totalschools

	def getPageData(self):
		result = self.parentLevelMethods[self.role]()
		return result