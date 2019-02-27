from contentusage.contentusagereport import BaseRoleAccess
from account.models import *
from account.constants import *
from sync_report.models import last_sync_date
from django.db.models import Max
import datetime
import json, time
from itertools import *
from datetime import date


def getCities():
	city_list = []
	cities = list(City.objects.all())
	for i in range(0,len(cities)):
		city_dict = {}
		city_dict['id'] = cities[i].city_id
		city_dict['name'] = cities[i].city_name
		city_dict['city_initial'] = cities[i].city_initial
		city_list.append(city_dict)
	return(city_list)

def get_history_list(temp):
	final_1 = list(last_sync_date.objects.filter(id_class_name__in = temp).values('sync_date','id_class_name').order_by('-sync_date'))
	key_dict = {}
	for i in temp:
		key_dict[i] = []
	[(key_dict[i['id_class_name']].append(str(i['sync_date']))) for i in final_1 for j in temp if j == i['id_class_name']]
	return(key_dict)

def all_data():
	temp1 = list(last_sync_date.objects.values('id_class_name'))
	temp = list(set([i['id_class_name'] for i in temp1]))
	print("Temp",temp)
	final = list(last_sync_date.objects.filter(id_class_name__in = temp).values('school_id','school_name','class_name','id_class_name').annotate(sync_date=Max('sync_date')))
	return(final,get_history_list(temp))

def all_selected_data(user_id):
	temp = get_selected_city(user_id)
	final = list(last_sync_date.objects.filter(id_class_name__in = temp).values('school_id','school_name','class_name','id_class_name').annotate(sync_date=Max('sync_date')))
	print(final)
	return(final, get_history_list(temp))


def get_selected_city(user_id):	
	temp = list(UserRoleCollectionMapping.objects.values_list('institute_id').filter(user_id=user_id))
	temp_list = [element for tupl in temp for element in tupl]
	temp1 = list(last_sync_date.objects.values('id_class_name').filter(school_id__in = temp_list))
	temp = list(set([i['id_class_name'] for i in temp1]))
	return(temp)


def get_userID_one_selected_city(selected_city):	
	temp1 = list(last_sync_date.objects.values('id_class_name'))
	temp = list(set([i['id_class_name'] for i in temp1]))
	final = list(last_sync_date.objects.filter(id_class_name__in = temp).values('school_id','school_name','class_name','id_class_name').annotate(sync_date=Max('sync_date')).filter(school_name__startswith=selected_city[0]))
	return(final,get_history_list(temp))


def get_userID_other_selected_city(selected_city,user_id):
	temp = get_selected_city(user_id)
	final = list(last_sync_date.objects.filter(id_class_name__in = temp).values('school_id','school_name','class_name','id_class_name').annotate(sync_date=Max('sync_date')).filter(school_name__startswith=selected_city[0]))
	return(final, get_history_list(temp))


def getSyncData(selected_city,user_id=1):
	sync_alert = [] 
	data_list = []
	if selected_city == "All":
		if user_id == 1:
			data1 = all_data()
		else:			
			data1 = all_selected_data(user_id)
	else:
		if user_id == 1:
			data1 = get_userID_one_selected_city(selected_city)
		else:
			data1 = get_userID_other_selected_city(selected_city,user_id)

	for i in range(0,len(data1[0])):
		data_dict = []
		# print(data1[0][i]['school_name'])
		data_dict.append(data1[0][i]['school_name'])
		data_dict.append(data1[0][i]['class_name'])
		data_dict.append(str(data1[0][i]['sync_date']))
		data_dict.append(data1[1][data1[0][i]['id_class_name']][1:])
		if (abs(date.today() - data1[0][i]['sync_date']).days) > 20:
			sync_alert.append(data1[0][i]['school_name'])
			data_dict.append("Active")

		data_list.append(data_dict)
	return(data_list, sync_alert)

	
def get_user_content():
	""" 
	Args:
		None
	Returns:
		columns(list): It returns list of columns
	"""
	columns = [{'title':'School Name'},{'title':'Class Name'},{'title':'Last Sync Date'},{'title':''}]

	return columns

def get_bit(user_id):
	temp = list(UserRoleCollectionMapping.objects.filter(user_id=user_id).values('institute_id'))
	temp1 = [i['institute_id'] for i in temp]
	temp = list(UserInfoSchool.objects.filter(school_id__in = temp1).values('school_name'))
	return(len(set([i['school_name'][0] for i in temp])))



def all_selected_data_mail(user_id):
	temp = get_selected_city(user_id)
	final = list(last_sync_date.objects.filter(id_class_name__in = temp).values('school_name','class_name').annotate(sync_date=Max('sync_date')))
	date = datetime.date.today()
	final1 = []
	for i in final:
		if ((date - i['sync_date']).days) > 7 or ((date - i['sync_date']).days) < -7: 
			final1.append(i['school_name'])
			final1.append(i['class_name'])
			# final1["class_name"].append(i["class_name"])
	return(final1)

# 	def convert_to_string(self, data):
# 		data['id'] = str (data['id']) 
# 		return data

# 	def getExamsData(self):
# 		""" Used to fetch the exam hierarchy for user
# 		Args:
# 			None
# 		Returns:
# 			totalstudent(dict) : dict of schools with it's classes and exams as a children
# 		"""
# 		school_list = []
# 		schools = UserInfoSchool.objects.filter(school_id__in = self.institutes)
# 		# Get all the schools, if schools exist
# 		for school in schools:
# 			school_info = {}
# 			classes_in_school = list(UserInfoClass.objects.filter(parent=school.school_id).extra(select={'id':'class_id','name':'class_name'}).values('id','name'))
# 			for classid in classes_in_school:
# 				exams_in_class = list(Exam.objects.filter(class_id=classid['id']).extra(select={'id':'exam_id','name':'exam_title'}).values('id','name'))
# 				classid['children']={}
# 				for exam in exams_in_class:
# 					exam['id'] = str(exam['id'])
# 					if exam['name'] not in classid['children'].keys():
# 						classid['children'][exam['name']]= exam
# 				classid['children']=list(map(lambda x: classid['children'][x],classid['children']))
# 			school_info['id'] = str(school.school_id)
# 			school_info['name'] = school.school_name
# 			school_info['children'] = list(map(self.convert_to_string, classes_in_school))
# 			school_list.append(school_info)
# 		self.totalexams["schools"] = school_list
# 		return self.totalexams
	
# 	def getClassData(self):
# 		""" Used to get class data for user 
# 		Args:
# 			None
# 		Returns:
# 			totalstudent(dict) : returns exam details with class/schools 
# 		"""
# 		class_info = {}
# 		class_list = []
# 		classes = list(UserInfoClass.objects.filter(class_id__in = self.classes).extra(select={'id':'class_id','name':'class_name'}).values('id','name'))
# 		for classid in classes:
# 			class_info = {}
# 			exams_in_class = list(Exam.objects.filter(class_id=classid['id']).extra(select={'id':'exam_id','name':'exam_title'}).values('id','name'))
# 			for exam in exams_in_class:
# 				exam['id'] = str(exam['id'])
# 			class_info['children'] = exams_in_class
# 			class_info['id'] = str(classid['id'])
# 			class_info['name'] = classid['name']
# 			class_list.append(class_info)
# 		self.totalexams["schools"] = class_list
# 		return self.totalexams


# 	def getPageData(self):
# 		result = self.parentLevelMethods[self.role]()
# 		return result	

# class Exammetric(object):
# 	def __init__(self, exam_id, start_time, end_time):

# 		self.exam_id = exam_id
# 		self.user_id = Exam.objects.filter(exam_id = self.exam_id).values('student_id')
# 		self.class_id = Exam.objects.filter(exam_id=self.exam_id).values('class_id')[0]['class_id']
# 		self.total_question = Exam.objects.filter(exam_id=self.exam_id).values('question_count')[0]['question_count']
# 		self.startTimestamp = datetime.date.fromtimestamp(int(start_time)).strftime('%Y-%m-%d')
# 		self.endTimestamp = datetime.date.fromtimestamp(int(end_time)).strftime('%Y-%m-%d')

# 	def get_user_content(self):
# 		""" 
# 		Args:
# 			None
# 		Returns:
# 			columns(list): It returns list of columns
# 		"""
# 		columns = [{'name':'first', 'title':'Student Name'},{'name':'second', 'title':'Correct Questions'},
# 					{'name':'third', 'title':'% Correct Questions'}]
	
# 		return columns

# 	def get_exam_metric(self):
# 		""" It's used to fetch the exam metrics result of respective user_id used in exam
# 		Args:
# 			None
# 		Returns:
# 			exam_metriclist(list):It returns student list including metrics result
# 		"""
# 		exam_metriclist = []
# 		i_exam =[]
		
# 		total_question =Exam.objects.filter(exam_id=self.exam_id).values('question_count')[0]['question_count']
# 		filter_students= {}
# 		filter_students['date__range'] = (self.startTimestamp, self.endTimestamp)
# 		filter_students['exam_id']=self.exam_id
# 		count=0
# 		student_list = UserInfoStudent.objects.filter(parent = self.class_id).values('student_id', 'student_name')		
# 		for student in student_list:
# 			i_exam =[]
# 			i_exam.append(student['student_name'])
# 			filter_students['student_id']=student['student_id']
# 			res = list(Exam.objects.filter(**filter_students).values_list('correct_questions'))
# 			res1 = list(chain(*res))
# 			if not res:
# 				for i in range(2):
# 					i_exam.append(0)
# 			if res:
# 				correct = Exam.objects.filter(**filter_students).values('correct_questions')[0]['correct_questions']
# 				i_exam.extend(res1)
# 				percent_correct_float = float(correct) / total_question 
# 				percent_correct = "{0:.2%}".format(percent_correct_float)		
# 				i_exam.append(percent_correct)
# 			exam_metriclist.append(i_exam)
# 		return exam_metriclist

# 	def aggregateresult(self, get_exam_metric, tc):
# 		correct_sum = 0
# 		count = 0
# 		correct_percent = 0.0
# 		aggregation = []
# 		for record in get_exam_metric:
# 			count+=1
# 			correct_sum += record[1]
# 			if(record[2] !=0):
# 				percent = float(record[2].strip('%'))
# 				correct_percent += (percent)
# 		aggregation = [correct_sum,correct_percent,count,tc]
# 		result = self.getAggregationData(aggregation)
# 		return result

# 	def getAggregationData(self, aggregateresult):
# 		aggregation = []
# 		student_percent = aggregateresult[2]
# 		student_percent *= 100
# 		avg_correct = aggregateresult[0]
# 		avg_correct /= aggregateresult[2]
# 		avg_percent_correct = aggregateresult[1]
# 		avg_percent_correct /=student_percent
# 		values = [str( "%.2f"%(avg_correct)),"{0:.2%}".format(avg_percent_correct)] 
# 		average = {'name': 'Average', 'values': values}
# 		aggregation.append(average)
# 		return aggregation
		

# 	def getStudentData(self):
# 		questionCount= {}
# 		student_data = Exam.objects.filter(exam_id = self.exam_id).extra(select ={'question_count':'question_count'}).values('question_count')
# 		for student in student_data:
# 			questionCount = {}
# 			questionCount['question_count'] = student['question_count']
# 		return questionCount        	
        

# 	def getTopics(self):
# 		topics =(Exam.objects.filter(exam_id = self.exam_id).values_list('question_sources')) 
# 		content_title =[]
# 		topic_id = []
# 		topic_details = []
# 		channel_path =[]
# 		topic_data = list(chain(*topics))
# 		td = json.loads(topic_data [0])
# 		topic_id = [item['exercise_id'] for item in td]
	
# 		for data in topic_id:
# 			topic_title=[]
# 			topic_list=self.get_topic_path(data,topic_title)
# 			topic_details.append(topic_list)
# 		for i in topic_details:
# 			i.reverse()
# 			i = ''.join(map(str, i))
# 			channel_path.append(i)
# 			channel_path= [' ' + x + ' ' for x in channel_path]
# 		for data in topic_id:
# 			topic = Content.objects.filter(topic_id = data).values('topic_name')[0]['topic_name']
# 			content_title.append(topic)
# 		content_title= [' ' + x + ' ' for x in content_title]
# 		return channel_path,content_title


# 	def get_topic_path(self,data,topic_title):
# 		topic_id =[]
# 		content = Content.objects.filter(topic_id = data).values('parent_id')[0]['parent_id']
# 		if content:
# 			topic = Content.objects.filter(topic_id = data).values('topic_name')[0]['topic_name']
# 			topic_id.append(data)
# 			topic_title.append(topic)
# 			topic_title.append("--->")
# 			self.get_topic_path(content,topic_title)
# 		else:
# 			topic = Content.objects.filter(topic_id = data).values('topic_name')[0]['topic_name']
# 			topic_title.append(topic)
# 		return topic_title

# 	def get_exam_metric_data(self):
# 		data = {}
# 		columns = self.get_user_content()
# 		rows = self.get_exam_metric()
# 		average = self.aggregateresult(self.get_exam_metric(),self.total_question)
# 		data['columns'] = columns
# 		data['rows'] = rows
# 		data['header'] = self.getStudentData()
# 		data['details'],data['topic'] = self.getTopics()
# 		data['average']= average
# 		#print('data:',data)
# 		return data
	

