from contentusage.contentusagereport import BaseRoleAccess
from account.models import *
from account.constants import *
from exam.models import Exam, creation
import datetime
import json, time

class Exam_details(BaseRoleAccess):
	def __init__(self, user, parentLevel):
		super(self.__class__, self).__init__(user, parentLevel)
		self.parentLevelMethods = [self.getExamsData, self.getExamsData, self.getExamsData, self.getClassData]
		self.totalstudent = {}
		self.studentexamdata = {}

	def convert_to_string(self, data):
		data['id'] = str (data['id']) 
		return data

	def getExamsData(self):
		""" Used to fetch the exam hierarchy for user
		Args:
			None
		Returns:
			totalstudent(dict) : dict of schools with it's classes and students as a children
		"""
		school_list = []
		schools = UserInfoSchool.objects.filter(school_id__in = self.institutes)
		# Get all the schools, if schools exist
		for school in schools:
			school_info = {}
			classes_in_school = list(UserInfoClass.objects.filter(parent=school.school_id).extra(select={'id':'class_id','name':'class_name'}).values('id','name'))
			for classid in classes_in_school:
				students_in_class = list(UserInfoStudent.objects.filter(parent=classid['id']).extra(select={'id':'student_id','name':'student_name'}).values('id','name'))
				for student in students_in_class:
					student['id'] = str(student['id'])
				classid['children'] = students_in_class
			school_info['id'] = str(school.school_id)
			school_info['name'] = school.school_name
			school_info['children'] = list(map(self.convert_to_string, classes_in_school))
			school_list.append(school_info)
		self.totalstudent["schools"] = school_list

		return self.totalstudent
	
	def getClassData(self):
		""" Used to get class data for user 
		Args:
			None
		Returns:
			totalstudent(dict) : returns student details with class/schools 
		"""
		class_info = {}
		class_list = []
		classes = list(UserInfoClass.objects.filter(class_id__in = self.classes).extra(select={'id':'class_id','name':'class_name'}).values('id','name'))
		for classid in classes:
			class_info = {}
			students_in_class =list(UserInfoStudent.objects.filter(parent=classid['id']).extra(select={'id':'student_id','name':'student_name'}).values('id','name'))
			for student in students_in_class:
				student['id'] = str(student['id'])
			class_info['children'] = students_in_class
			class_info['id'] = str(classid['id'])
			class_info['name'] = classid['name']
			class_list.append(class_info)
		self.totalstudent["schools"] = class_list
		return self.totalstudent

	def getPageData(self):
		result = self.parentLevelMethods[self.role]()
		return result	

class Exammetric(object):
	def __init__(self, user_id, start_time, end_time):

		self.user_id = user_id
		self.exam_id = Exam.objects.filter(student_id = self.user_id).values('exam_id')
		self.startTimestamp = datetime.date.fromtimestamp(int(start_time)).strftime('%Y-%m-%d')
		self.endTimestamp = datetime.date.fromtimestamp(int(end_time)).strftime('%Y-%m-%d')

	def get_user_content(self):
		""" 
		Args:
			None
		Returns:
			columns(list): It returns list of columns
		"""
		columns = [{'name':'first', 'title':'Exam Title'},{'name':'second', 'title':'Correct Questions'},
					{'name':'third', 'title':'% Correct Questions'},{'name':'fourth', 'title':'Total Questions'}]
	
		return columns

	def get_exam_metric(self):
		""" It's used to fetch the exam metrics result of respective user_id used in exam
		Args:
			None
		Returns:
			exam_metriclist(list):It returns student list including metrics result
		"""
		res1 = []
		exam_metriclist = []
		i_exam =[]
		filter_exams= {}
		filter_exams['date__range'] = (self.startTimestamp, self.endTimestamp)
		student_list = Exam.objects.filter(student_id = self.user_id).filter(**filter_exams).values_list('student_id', 'exam_title', 'correct_questions' ,'question_count')
		for student in student_list:
			i_exam = []
			i_exam.append(student[1])
			i_exam.append(student[2])
			percent_correct_float = float(student[2]) / student[3] 
			percent_correct = "{0:.2%}".format(percent_correct_float)
			i_exam.append(percent_correct)
			i_exam.append(student[3])
			exam_metriclist.append(i_exam)
		return exam_metriclist

	def getStudentData(self):
		student_info = {}
		student_data = list(creation.objects.filter(student_id = self.user_id).extra(select ={'exam_count':'exam_count', 'active_exam':'active_exam_count', 'complete_exam':'complete_exam_count'}).values('exam_count','active_exam','complete_exam'))
		for student in student_data:
			student_info = {}
			student_info['exam_count'] = student['exam_count']
			student_info['active_exam'] = student['active_exam']
			student_info['complete_exam'] = student['complete_exam']
		return student_info

	def get_exam_metric_data(self):
		data = {}
		columns = self.get_user_content()
		rows = self.get_exam_metric()
		data['columns'] = columns
		data['rows'] = rows
		data['header'] = self.getStudentData()
		return data
	

