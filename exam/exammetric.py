from contentusage.contentusagereport import BaseRoleAccess
from account.models import *
from account.constants import *
from exam.models import Exam, creation
import datetime
import json, time
from itertools import *

class Exam_details(BaseRoleAccess):
	def __init__(self, user, parentLevel):
		super(self.__class__, self).__init__(user, parentLevel)
		self.parentLevelMethods = [self.getExamsData, self.getExamsData, self.getExamsData, self.getClassData]
		self.totalexams = {}
		self.studentexamdata = {}

	def convert_to_string(self, data):
		data['id'] = str (data['id']) 
		return data

	def getExamsData(self):
		""" Used to fetch the exam hierarchy for user
		Args:
			None
		Returns:
			totalstudent(dict) : dict of schools with it's classes and exams as a children
		"""
		school_list = []
		schools = UserInfoSchool.objects.filter(school_id__in = self.institutes)
		# Get all the schools, if schools exist
		for school in schools:
			school_info = {}
			classes_in_school = list(UserInfoClass.objects.filter(parent=school.school_id).extra(select={'id':'class_id','name':'class_name'}).values('id','name'))
			for classid in classes_in_school:
				exams_in_class = list(Exam.objects.filter(class_id=classid['id']).extra(select={'id':'exam_id','name':'exam_title'}).values('id','name'))
				classid['children']={}
				for exam in exams_in_class:
					exam['id'] = str(exam['id'])
					if exam['name'] not in classid['children'].keys():
						classid['children'][exam['name']]= exam
				classid['children']=list(map(lambda x: classid['children'][x],classid['children']))
			school_info['id'] = str(school.school_id)
			school_info['name'] = school.school_name
			school_info['children'] = list(map(self.convert_to_string, classes_in_school))
			school_list.append(school_info)
		self.totalexams["schools"] = school_list
		return self.totalexams
	
	def getClassData(self):
		""" Used to get class data for user 
		Args:
			None
		Returns:
			totalstudent(dict) : returns exam details with class/schools 
		"""
		class_info = {}
		class_list = []
		classes = list(UserInfoClass.objects.filter(class_id__in = self.classes).extra(select={'id':'class_id','name':'class_name'}).values('id','name'))
		for classid in classes:
			class_info = {}
			exams_in_class = list(Exam.objects.filter(class_id=classid['id']).extra(select={'id':'exam_id','name':'exam_title'}).values('id','name'))
			for exam in exams_in_class:
				exam['id'] = str(exam['id'])
			class_info['children'] = exams_in_class
			class_info['id'] = str(classid['id'])
			class_info['name'] = classid['name']
			class_list.append(class_info)
		self.totalexams["schools"] = class_list
		return self.totalexams


	def getPageData(self):
		result = self.parentLevelMethods[self.role]()
		return result	

class Exammetric(object):
	def __init__(self, exam_id, start_time, end_time):

		self.exam_id = exam_id
		self.user_id = Exam.objects.filter(exam_id = self.exam_id).values('student_id')
		self.class_id = Exam.objects.filter(exam_id=self.exam_id).values('class_id')[0]['class_id']
		self.total_question = Exam.objects.filter(exam_id=self.exam_id).values('question_count')[0]['question_count']
		self.startTimestamp = datetime.date.fromtimestamp(int(start_time)).strftime('%Y-%m-%d')
		self.endTimestamp = datetime.date.fromtimestamp(int(end_time)).strftime('%Y-%m-%d')

	def get_user_content(self):
		""" 
		Args:
			None
		Returns:
			columns(list): It returns list of columns
		"""
		columns = [{'name':'first', 'title':'Student Name'},{'name':'second', 'title':'Correct Questions'},
					{'name':'third', 'title':'% Correct Questions'}]
	
		return columns

	def get_exam_metric(self):
		""" It's used to fetch the exam metrics result of respective user_id used in exam
		Args:
			None
		Returns:
			exam_metriclist(list):It returns student list including metrics result
		"""
		exam_metriclist = []
		i_exam =[]
		
		total_question =Exam.objects.filter(exam_id=self.exam_id).values('question_count')[0]['question_count']
		filter_students= {}
		filter_students['date__range'] = (self.startTimestamp, self.endTimestamp)
		filter_students['exam_id']=self.exam_id
		count=0
		student_list = UserInfoStudent.objects.filter(parent = self.class_id).values('student_id', 'student_name')		
		for student in student_list:
			i_exam =[]
			
			i_exam.append(student['student_name'])
			
			filter_students['student_id']=student['student_id']

			res = list(Exam.objects.filter(**filter_students).values_list('correct_questions'))
			res1 = list(chain(*res))
			
			if not res:
				for i in range(2):
					i_exam.append(0)
			if res:
				
				correct = Exam.objects.filter(**filter_students).values('correct_questions')[0]['correct_questions']
				i_exam.extend(res1)
				percent_correct_float = float(correct) / total_question 
				percent_correct = "{0:.2%}".format(percent_correct_float)		
				i_exam.append(percent_correct)
				
			exam_metriclist.append(i_exam)
				
		return exam_metriclist

	def aggregateresult(self, get_exam_metric, tc):
		correct_sum = 0
		count = 0
		correct_percent = 0.0

		aggregation = []
		for record in get_exam_metric:
			count+=1
			correct_sum += record[1]
			if(record[2] !=0):
				percent = float(record[2].strip('%'))
				correct_percent += (percent)


		aggregation = [correct_sum,correct_percent,count,tc]
		print("aggregateresult",aggregation)
		result = self.getAggregationData(aggregation)
		print('agg=====',result)
		return result

	def getAggregationData(self, aggregateresult):
		# avg_correct = 0
		aggregation = []
	
		student_percent = aggregateresult[2]
		student_percent *= 100

		avg_correct = aggregateresult[0]
		avg_correct /= aggregateresult[2]
		print('correct avg:',avg_correct)
		avg_percent_correct = aggregateresult[1]
		avg_percent_correct /=student_percent
		print('correct % avg:',avg_percent_correct)
		values = [str( "%.2f"%(avg_correct)),"{0:.2%}".format(avg_percent_correct)] 
		average = {'name': 'Average', 'values': values}
		aggregation.append(average)
		return aggregation
		

	def getStudentData(self):
		questionCount= {}
		student_data = Exam.objects.filter(exam_id = self.exam_id).extra(select ={'question_count':'question_count'}).values('question_count')
		for student in student_data:
			questionCount = {}
			questionCount['question_count'] = student['question_count']
		return questionCount

	def getTopics(self):
	
		topics = Exam.objects.filter(exam_id = self.exam_id).values_list('question_sources')
		# for topic in topics:
		# 	topic_data =[]
		# 	topic_data.append(topic['question_sources'])
		topic_data = list(chain(*topics))
		return topic_data

	def get_exam_metric_data(self):
		data = {}
		columns = self.get_user_content()
		rows = self.get_exam_metric()
		average = self.aggregateresult(self.get_exam_metric(),self.total_question)
		data['columns'] = columns
		data['rows'] = rows
		data['header'] = self.getStudentData()
		data['topic'] = self.getTopics()
		data['average']= average
		#print('data:',data)
		return data
	

