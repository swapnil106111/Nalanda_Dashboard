from contentusage.contentusagereport import BaseRoleAccess
from account.models import * 
from account.constants import *
from lesson.models import Lesson

import datetime
import json, time
from django.db.models import Count
from itertools import chain

class LessonDetails(BaseRoleAccess):
	def __init__(self, user, parentLevel):
		""" Used to fetch the school/class based on user role
		Args:
			user(object): It used to get the school and class details for the respective user
			parentLevel(int): It used to check the parentLevel of each user i.e 1-BM, 2-SL, 3-Teacher
		"""
		super(self.__class__, self).__init__(user, parentLevel)
		self.parentLevelMethods = [self.getLessonsData, self.getLessonsData, self.getLessonsData, self.getClassData]	
		self.totallessons = {}

	def convert_to_string(self, data):
		data['id'] = str(data['id'])
		return data

	def getLessonsData(self):
		""" Used to fetch the lessons hierarchy for user
		Args:
			None
		Returns:
			totalscho(dict) : dict of schools with it's classes and students as a children
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
		self.totallessons["schools"] = school_list
		return self.totallessons

	def getClassData(self):
		""" Used to get class data for user 
		Args:
			None
		Returns:
			totallessons(dict) : returns lesson details with class/schools 
		"""
		class_info = {}
		class_list = []
		classes = list(UserInfoClass.objects.filter(class_id__in = self.classes).extra(select={'id':'class_id','name':'class_name'}).values('id','name'))
		for classid in classes:
			class_info = {}
			lessons_in_class = list(Lesson.objects.filter(class_id=classid['id']).extra(select={'id':'lesson_id','name':'lesson_name'}).values('id','name'))
			for lesson in lessons_in_class:
					lesson['id'] = str(lesson['id'])
			class_info['children'] = lessons_in_class
			class_info['id'] = str(classid['id'])
			class_info['name'] = classid['name']
			class_list.append(class_info)
		self.totallessons["schools"] = class_list
		return self.totallessons

	def getPageData(self):
		result = self.parentLevelMethods[self.role]()
		return result

class LessonMastery(object):
	def __init__(self, lesson_id, start_time, end_time):
		""" Used to fetch the mastery details of lesson
		Args:
			lesson_id(str) : lesson_id selected by user from UI(lessons dropdown)
		Returns:
			None 
		"""
		self.lesson_id = lesson_id
		self.lesson_content = Lesson.objects.filter(lesson_id=self.lesson_id).values('lesson_content')
		self.res = json.loads(self.lesson_content[0]['lesson_content'])
		self.content_list = list((map(lambda x: x['contentnode_id'], self.res)))
		self.class_id = Lesson.objects.filter(lesson_id=self.lesson_id).values('class_id')[0]['class_id']
		self.metrics_list = ['completed_questions', 'correct_questions', 'mastered']
		self.startTimestamp = datetime.date.fromtimestamp(int(start_time)).strftime('%Y-%m-%d')
		self.endTimestamp = datetime.date.fromtimestamp(int(end_time)).strftime('%Y-%m-%d')
	
	def get_lesson_content(self):
		""" It's used to fetch the topic name used into lesson
		Args:
			None
		Returns:
			columns(list): It returns list of topic names
		"""
		columns = [{'name':'first', 'title':'Student Name'}]
		topic_dict = {}
		metrics_dict = {}
		topic_list = Content.objects.filter(topic_id__in=self.content_list).values_list('topic_name', flat=True)
		for topic in topic_list:
			topic_dict['title'] = topic
			columns.append(topic_dict)
			topic_dict = {}
			for metrics in self.metrics_list:
				metrics_dict['title'] = metrics
				columns.append(metrics_dict)
				metrics_dict = {}

		return columns

	def get_lesson_mastery_results(self):
		""" It's used to fetch the mastry metrics result of respective content_id used in lesson
		Args:
			None
		Returns:
			student_res_list(list):It returns student list includingg metrics result
		"""
		student_res_list = []
		i_student = []
		filter_lessons= {}
		filter_lessons['date__range'] = (self.startTimestamp, self.endTimestamp)
		student_list = UserInfoStudent.objects.filter(parent = self.class_id).values('student_id', 'student_name')		
		for student in student_list:
			i_student.append(student['student_name'])
			for content_id in self.content_list:
				res1 = []
				filter_lessons['student_id']=student['student_id']
				filter_lessons['content_id'] = content_id
				res = (MasteryLevelStudent.objects.filter(**filter_lessons).values_list('completed_questions','correct_questions','mastered')) 
				
				if not res:
					for i in range(len (self.metrics_list)):
						i_student.append(0)
				if res:
					res1 = list(chain(*res))
					#print ('RES :',res1)
					i_student.extend(res1)	
			student_res_list.append(i_student)
			i_student = []
		return student_res_list

	def get_lesson_mastery_data(self):
		data = {}
		columns = self.get_lesson_content()
		rows = self.get_lesson_mastery_results()
		data['columns'] = columns
		data['rows'] = rows
		return data
		




