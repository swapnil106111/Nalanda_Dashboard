from account.models import * 
from django.contrib.auth.models import User, Group
from account.constants import *
import datetime
import json
from django.db.models import Count
from contentusage.constants import *
from account.usermastery import BaseRoleAccess


class BaseRoleAccess(object):
	def __init__(self, user, parentLevel):
		parentLevelMethods = {1:self.boardMember, 2:self.schoolLeader, 3:self.teacher}	
		self.user = user
		self.role = 0

		# Check if user is superuser i.e admin. admin doesn't belongs to any group
		if not user.is_superuser:
			self.role = user.groups.values()[0]['id']

		if self.role in parentLevelMethods: 
			schools, classes, channels = parentLevelMethods[self.role]()

			if self.role == 1 and classes is None:
				if (len(schools) > 0):
					self.institutes = UserInfoSchool.objects.filter(school_id__in = schools)
					self.channels = channels
				else:
					self.institutes = UserInfoSchool.objects.filter(school_id = schools[0])
					self.channels = channels
				self.classes = None
			elif self.role == 3:
				self.institutes = UserInfoSchool.objects.filter(school_id = schools[0])
				self.classes = UserInfoClass.objects.filter(class_id__in = classes)
				self.channels = channels
			else:
				self.institutes = UserInfoSchool.objects.filter(school_id = schools[0])
				self.channels = channels

		elif self.role == 0:
			# userMapping = UserRoleCollectionMapping.objects.filter(user_id= self.user)
			# schools = list(userMapping.values_list('institute_id_id', flat=True))
			self.institutes = UserInfoSchool.objects.all()
			channelMapping = Content.objects.filter(topic_id__in=CHANNELDBLIST).values('sub_topics')
			self.channels = list(channelMapping.values_list('topic_id', flat = True))
			self.classes = None
		self.parentLevel = int(parentLevel)

	def teacher(self):
		"""
		This function is used to fetch the mapping of classes and schools based on the user role 
		"""
		userMapping = UserRoleCollectionMapping.objects.filter(user_id = self.user)
		schools = list(userMapping.values_list('institute_id_id', flat = True))
		classes = list(userMapping.values_list('class_id_id', flat = True))
		channels = list(MasteryLevelClass.objects.filter(class_id__in = classes).values_list('channel_id', flat = True).annotate(dcount=Count('channel_id')))[:-1]
		return schools, classes, channels

	def schoolLeader(self):
		"""
		This function is used to fetch the mapping of classes and schools based on the user role 
		"""
		userMapping = UserRoleCollectionMapping.objects.filter(user_id= self.user)
		schools = list(userMapping.values_list('institute_id_id', flat=True))
		classes = list(UserInfoClass.objects.filter(parent = schools[0]).values_list('class_id', flat = True))
		channels = list(MasteryLevelSchool.objects.filter(school_id__in = schools).values_list('channel_id', flat = True).annotate(dcount=Count('channel_id')))[:-1]
		return schools, classes, channels

	def boardMember(self):
		userMapping = UserRoleCollectionMapping.objects.filter(user_id=self.user)
		schools = list(userMapping.values_list('institute_id_id', flat=True))
		classes = None
		channels = list(MasteryLevelSchool.objects.filter(school_id__in = schools).values_list('channel_id', flat = True).annotate(dcount=Count('channel_id')))[:-1]
		return schools, classes, channels

class ContentUsageMeta(BaseRoleAccess): 
	def __init__(self, user, parentLevel, contentId, channelId, previousContentID, previousChannelID):
		super(self.__class__, self).__init__(user, parentLevel)
		self.contentId = contentId
		self.channelId = channelId
		self.parentLevel = parentLevel
		self.parentLevelMethods = [self.getChannelMeta, self.getChannelTopicMeta, self.getChannelTopicMeta, self.getChannelTopicMeta, self.getChannelTopicMeta, self.getChannelTopicMeta, self.getChannelTopicMeta]
		self.previousContentlIDs = previousContentID
		self.previousChannelIDs = previousChannelID
	# Construct the breadcrumb format
	def construct_breadcrumb(self, parentName, parentLevel, parentId, channelId):
		
		res = {
		"parentName": parentName,
		"parentLevel": parentLevel,
		"parentId": parentId,
		"channelId": channelId
		}
		return res

	def construct_response(self, code, title, message, data):
		response_object = {}
		response_object["code"] = code
		response_object["info"] = {"title": title,"message": message}
		response_object["data"] = data
		return response_object

	def getChannelMeta(self):
		""" Used to fetch the institute meta information
		Args:
			objBreadcrumb(list) = used to set metadata(parentId, parentLevel, parentName) of institutes
			rows(list) = []
		Returns:
			objBreadcrumb(list) = it returns metadata(parentId, parentLevel, parentName) of institutes
			rows(list) = it returns institutes information
		"""
		objBreadcrumb = []
		rows = []
		objBreadcrumb.append(self.construct_breadcrumb("channels", 0, "-1", "-1"))
		objBreadcrumb = self.setBreadcrumbData(objBreadcrumb)
		objcontent = Content.objects.filter(topic_id__in=self.channels).values('topic_name','content_id','channel_id')
		for content in objcontent:
			channel_info = {
				"id": str(content['content_id']),
				"name": content['topic_name'],
				"channelid":str(content['channel_id']),
				"maxval":False
			}
			rows.append(channel_info)
		return rows, objBreadcrumb

	def getChannelTopicMeta(self):
		objBreadcrumb = []
		rows = []
		self.parentLevel = 0
		objBreadcrumb.append(self.construct_breadcrumb("channels", 0, "-1", self.channelId))
		objBreadcrumb = self.setBreadcrumbData(objBreadcrumb)
		objsubtopics = list(Content.objects.filter(content_id=self.contentId, channel_id=self.channelId).values_list('sub_topics', flat = True))
		for obj in objsubtopics:
			result = json.loads(obj)
			if (result['children']):
				subtopics = result['children']
				rows = self.getSubtopicDetails(subtopics, rows)
		return rows, objBreadcrumb

	def getSubtopicDetails(self, subtopics, rows):
		maxval = False;
		for subtopic in subtopics:
			if len(subtopic['children']) == 0:
				maxval = True;
			else:
				maxval = False
			topic_info = {
				"id": str(subtopic['contentId']),
				"name": subtopic['name'],
				"channelid":str(subtopic['channelId']),
				"maxval":maxval
			}
			rows.append(topic_info)
		return rows

	def setBreadcrumbData(self, objBreadcrumb):
		for content in zip(self.previousChannelIDs, self.previousContentlIDs):
			if content[1] != '-1':
				self.parentLevel += 1
				topic = Content.objects.filter(content_id = content[1], channel_id = content[0]).values('topic_name','content_id').first()
				objBreadcrumb.append(self.construct_breadcrumb(topic['topic_name'], self.parentLevel, topic['content_id'], content[0]))
		return objBreadcrumb

	def pageMeta(self, objMetrics):
		rows, objBreadcrumb = self.parentLevelMethods[self.parentLevel]()
		data = { 'breadcrumb': objBreadcrumb, 'metrics': objMetrics, 'rows': rows }
		response_object = self.construct_response(0, "", "", data)
		return response_object 

class ContentUsageData(BaseRoleAccess):
	def __init__(self, user, parentLevel, topicID, channelID, startTimestamp, endTimestamp, filterCriteria, filtetContentUsage, current_time1):
		super(self.__class__, self).__init__(user, parentLevel)
		self.topicID = topicID if topicID != '-1' else ''
		self.channelID = channelID if channelID != '-1' else ''
		endTimestamp = str(int(endTimestamp) + 86400)
		self.startTimestamp = datetime.date.fromtimestamp(int(startTimestamp)).strftime('%Y-%m-%d')
		self.endTimestamp = datetime.date.fromtimestamp(int(endTimestamp)).strftime('%Y-%m-%d')
		self.parentLevelMethods = [self.getInstitutesData, self.getInstitutesData, self.getInstitutesData, self.getInstitutesData]
		self.filterCriteria = filterCriteria
		self.filtetContentUsage = filtetContentUsage
		self.current_time = datetime.date.fromtimestamp(current_time1/1e3).strftime('%Y-%m-%d %H:%S')
		self.current_time1 = current_time1

	def getInstitutesData(self):
		if self.parentLevel == 0:
			res = list(map(self.getContentUsageDetails, self.channels))
			aggregationResult = [res['aggregation'] for res in res]
			data = self.getContentUsageAggregationData(aggregationResult, res)
		else:
			topicIDs = []
			channelIDs = []
			maxValues = []
			res = self.getContentData(self.topicID, self.channelID)
			for obj in res:
				topicID = Content.objects.filter(content_id = obj['id'], channel_id = obj['channelid']).values_list('topic_id',flat=True).first()
				channelID = Content.objects.filter(content_id = obj['id'], channel_id = obj['channelid']).values_list('channel_id', flat = True).first()
				maxValues.append(obj['maxval'])
				topicIDs.append(topicID)
				channelIDs.append(channelID)
			res = list(map(self.getContentUsageDrillDownDetails, topicIDs, channelIDs, maxValues))
			aggregationResult = [res['aggregation'] for res in res]
			data = self.getContentUsageAggregationData(aggregationResult, res)
		return data

	def getContentUsageData(self, channel):
		filterTopics = {}
		filterTopics['date__range'] = (self.startTimestamp, self.endTimestamp)
		filterTopics['channel_id'] = channel
		filterTopics['content_id'] = channel

		if not self.filterCriteria and self.role != 3:
			filterTopics['school_id__in'] = self.institutes
			channeldata = MasteryLevelSchool.objects.filter(**filterTopics)
		elif self.role == 3:
			filterTopics['class_id__in'] = self.classes
			channeldata = MasteryLevelClass.objects.filter(**filterTopics)
		else:
			filterTopics['student_id_id__in'] = self.filtetContentUsage
			channeldata = MasteryLevelStudent.objects.filter(**filterTopics)
		return channeldata

	def getContentData(self, content_id, channel_id):
		rows = []
		objsubtopics = list(Content.objects.filter(content_id=content_id, channel_id=channel_id).values_list('sub_topics', flat = True))
		for obj in objsubtopics:
			result = json.loads(obj)
			if (result['children']):
				subtopics = result['children']
				rows = self.getSubtopicDetails(subtopics, rows)
		return rows

	def getSubtopicDetails(self, subtopics, rows):
		maxval = False;
		for subtopic in subtopics:
			if len(subtopic['children']) == 0:
				maxval = True;
			else:
				maxval = False
			topic_info = {
				"id": str(subtopic['contentId']),
				"name": subtopic['name'],
				"channelid":str(subtopic['channelId']),
				"maxval":maxval
			}
			rows.append(topic_info)
		return rows

	def getChannelDataforsubtopics(self, content_id, channel_id):
		filterTopics = {}
		filterTopics['date__range'] = (self.startTimestamp, self.endTimestamp)
		filterTopics['channel_id'] = channel_id
		filterTopics['content_id'] = content_id

		if not self.filterCriteria and self.role != 3:
			filterTopics['school_id__in'] = self.institutes
			channel_content_usage = MasteryLevelSchool.objects.filter(**filterTopics)
		elif self.role == 3:
			filterTopics['class_id__in'] = self.classes
			channel_content_usage = MasteryLevelClass.objects.filter(**filterTopics)
		else:
			filterTopics['student_id_id__in'] = self.filtetContentUsage
			channel_content_usage = MasteryLevelStudent.objects.filter(**filterTopics)

		return channel_content_usage
	def getContentUsageDrillDownDetails(self, content_id, channel_id, maxval):
		aggregation = []
		rows = []
		values = []
		completed_questions = 0
		number_of_attempts = 0

		total_questions = self.getTopicsData()
		channel_content_usage = self.getChannelDataforsubtopics(content_id, channel_id)
		if  len(channel_content_usage) == 0:
			values = [0, "0.00%"]
			aggregation = [0, 0.00]
			objcontent = Content.objects.filter(channel_id=channel_id,topic_id = content_id).values('topic_name','content_id','channel_id').first()
			# row = {'id': str(masteryElement.class_id), 'name': masteryElement.class_name, 'total_questions': total_questions, 'total_subtopics': total_subtopics, 'values': values, 'aggregation': aggregation}
			row = {'id': str(objcontent['content_id']), 'name': objcontent['topic_name'],'channelid':channel_id ,'values': values, 'aggregation':aggregation,'maxval':maxval, 'total_questions':total_questions}	
			# return row
		else:
			for objContent in channel_content_usage:
				# mastered_topics += objContent.mastered
				completed_questions += objContent.completed_questions
				# correct_questions += objContent.correct_questions
				number_of_attempts += objContent.attempt_questions
				# number_of_exercise_attempts += objContent.attempt_exercise
			#Calculate the percentage of completed questions 
			percent_complete_float = float(completed_questions)/(total_questions)
			percent_complete = "{0:.2%}".format(percent_complete_float)

			# Calculate the percentage of correct questions
			# percent_correct_float = float(correct_questions) / (number_of_attempts) # changed the formula to calculate the % correct based on total_attempts instead of total_questions of respective content. As discussed with Harish
			# percent_correct = "{0:.2%}".format(percent_correct_float)

			# Calculate the percentage of exercise mastered
			# percent_mastered_topics_float = float(mastered_topics) / (number_of_exercise_attempts) # changed formula to calculate the % exrecise mastered based on total_exercise_attempts instead of total_subtopics of respective content.
			# percent_mastered_topics = "{0:.2%}".format(percent_mastered_topics_float)

			# values = [mastered_topics, number_of_exercise_attempts,percent_mastered_topics, correct_questions,number_of_attempts,percent_correct]
			# aggregation = [mastered_topics, number_of_exercise_attempts,percent_mastered_topics_float, correct_questions, number_of_attempts,percent_correct_float]
			values = [number_of_attempts, percent_complete]
			aggregation = [number_of_attempts, percent_complete_float]

			objcontent = Content.objects.filter(channel_id=channel_id, topic_id = content_id).values('topic_name','content_id','channel_id').first()
			row = {'id': str(objcontent['content_id']), 'name': objcontent['topic_name'], 'channelid': str(objcontent['channel_id']),'values': values, 'aggregation':aggregation,'maxval':maxval, 'total_questions':total_questions}
		return row
	def getTopicsData(self):
		""" Used to calculate the total_questions based on the selected topicID and channelID
		Args:
			None
		Returns:
			total_questions(int) : Count of total_questions
		"""
		total_questions = 0

		filterTopics = {'content_id':self.topicID}
		if self.topicID:
			filterTopics['channel_id'] = self.channelID
		topic = Content.objects.filter(**filterTopics).first()
		total_questions = topic.total_questions
		return total_questions

	def getContentUsageAggregationData(self, aggregationResult,contentUsageData):
		""" Used to Calculate the aggregation of each masteryElements
		Args:
			aggregationResult(list) : list of percentage vaue of four metrics
			contentUsageData(dict) = mastry data of masteryElements
		Returns:
			data(dict) = it contains aggregation result and mastery data of class, school
		"""
		data = {}	
		percent_complete_array = []
		# percent_correct_array = []
		number_of_attempts_array = []
		# percent_student_completed_array = []
		sample_metrix = []
		# mastered_topics = []
		# percent_mastered_topics = []
		# correct_questionsList = []
		# completed_questionsList =[]
		# number_of_exercise_attempts_list = []
		for row in aggregationResult:
			# mastered_topics.append(row[0])
			# number_of_exercise_attempts_list.append(row[1])
			# percent_mastered_topics.append(row[2])
			# correct_questionsList.append(row[3])
			number_of_attempts_array.append(row[0])
			# percent_correct_array.append(row[5])
			# completed_questionsList.append(row[5])
			percent_complete_array.append(row[1])

		# Removed unwanted data of aggregation
		for row in contentUsageData:
			row.pop('aggregation', None)

		aggregation = self.getAggrigation(number_of_attempts_array,percent_complete_array)
		data['rows'] = contentUsageData
		data['aggregation'] = aggregation
		return data

	def getContentUsageDetails(self, channel):
		""" Used to fetch mastery details of any masteryElement(i.e class, school and student)
		Args:
			masteryElement(obj): fetched the school and class mastery
		Returns:
			row(dict) : It contains the mastery data of school or class
		"""
		aggregation = []
		rows = []
		values = []
		completed_questions = 0
		correct_questions = 0
		number_of_attempts = 0
		students_completed = 0
		total_students = 0
		mastered_topics = 0
		number_of_exercise_attempts = 0
		percent_mastered_topics = 0

		total_questions = self.getTopicsData()
		# total_subtopics = self.getSubTopicsData()

		objChannelContentUsage = self.getContentUsageData(channel)

		# Filter mastery level belongs to a certain class with certain topic id, and within certain time range
		# total_students = masteryElement.total_students
		if  len(objChannelContentUsage) == 0:
			values = [0, "0.00%"]
			aggregation = [0, 0.00] 
			# if self.parentLevel == 0:
			# 	row = {'id': str(masteryElement.school_id), 'name': masteryElement.school_name, 'total_questions': total_questions, 'total_subtopics': total_subtopics, 'values': values, 'aggregation': aggregation}
			# else:
			objcontent = Content.objects.filter(topic_id=channel).values('topic_name','content_id','channel_id').first()
			# row = {'id': str(masteryElement.class_id), 'name': masteryElement.class_name, 'total_questions': total_questions, 'total_subtopics': total_subtopics, 'values': values, 'aggregation': aggregation}
			row = {'id': str(objcontent['content_id']), 'name': objcontent['topic_name'], 'channelid': objcontent['channel_id'],'values': values, 'aggregation':aggregation, 'maxval':False, 'total_questions':total_questions}	
			# return row
		else:
			for objContent in objChannelContentUsage:
				# mastered_topics += objContent.mastered
				completed_questions += objContent.completed_questions
				# correct_questions += objContent.correct_questions
				number_of_attempts += objContent.attempt_questions

				# number_of_exercise_attempts += objContent.attempt_exercise
			#Calculate the percentage of completed questions 
			percent_complete_float = float(completed_questions)/(92950)
			percent_complete = "{0:.2%}".format(percent_complete_float)

			# Calculate the percentage of correct questions
			# percent_correct_float = float(correct_questions) / (number_of_attempts) # changed the formula to calculate the % correct based on total_attempts instead of total_questions of respective content. As discussed with Harish
			# percent_correct = "{0:.2%}".format(percent_correct_float)

			# Calculate the percentage of exercise mastered
			# percent_mastered_topics_float = float(mastered_topics) / (number_of_exercise_attempts) # changed formula to calculate the % exrecise mastered based on total_exercise_attempts instead of total_subtopics of respective content.
			# percent_mastered_topics = "{0:.2%}".format(percent_mastered_topics_float)

			# values = [mastered_topics, number_of_exercise_attempts,percent_mastered_topics, correct_questions,number_of_attempts,percent_correct]
			# aggregation = [mastered_topics, number_of_exercise_attempts,percent_mastered_topics_float, correct_questions, number_of_attempts,percent_correct_float]
			values = [number_of_attempts, percent_complete]
			aggregation = [number_of_attempts, percent_complete_float]
			objcontent = Content.objects.filter(topic_id=channel).values('topic_name','content_id','channel_id').first()
			row = {'id': str(objcontent['content_id']), 'name': objcontent['topic_name'], 'channelid': str(objcontent['channel_id']),'values': values, 'aggregation':aggregation,'maxval':False, 'total_questions':total_questions}	
			# if self.parentLevel == 0:
			# 	row = {'id': str(masteryElement.school_id), 'name': masteryElement.school_name, 'total_questions': total_questions, 'total_subtopics': total_subtopics, 'values': values, 'aggregation':aggregation}	
			# else:
			# 	row = {'id': str(masteryElement.class_id), 'name': masteryElement.class_name, 'total_questions': total_questions, 'total_subtopics': total_subtopics, 'values': values, 'aggregation': aggregation}
		return row

	def getAggrigation(self, numberOfAttemptsList,percentCompleteList):
		""" Used to calculate the aggregation for each masteryElement based on metrics data
		Args:
			percentCompleteList(list) :  List of completed questions(percentage)
			percentCorrectList(list) : List of correct questions(percentage)
			percentStudentCompletedList(list) : List of students completed the topic(percentage)
			numberOfAttemptsList(int) : List of number of attempts 

		Returns:
			aggregation[list] = returns average of metrics data in list
		"""
		aggregation = []
		avg_complete = 0
		avg_percent_complete = 0
		avg_correct = 0
		avg_percent_correct = 0
		avg_number_of_attempts = 0
		avg_percent_student_completed = 0
		avg_mastered_topics = 0
		avg_percent_mastered_topics = 0
		avg_number_of_exercise_attempts = 0
		# Calculate the average for these four metrics
		length = len(percentCompleteList)
		if length != 0:
		    for i in range(length):
		    	# avg_mastered_topics += mastered_topics[i]
		    	# avg_number_of_exercise_attempts += percent_of_exercise_attempts_list[i]
		    	# avg_percent_mastered_topics += percent_mastered_topics[i]
		    	# avg_correct += correctQuestionsList[i]
		    	avg_number_of_attempts += numberOfAttemptsList[i]
		    	# avg_percent_correct += percentCorrectList[i]
		    	# avg_complete += completedQuestionsList[i]
		    	avg_percent_complete +=  percentCompleteList[i]
		   
		    # avg_mastered_topics /= length
		    # avg_number_of_exercise_attempts /= length
		    # avg_percent_mastered_topics /= length
		    # avg_correct /= length
		    avg_number_of_attempts /= length
		    # avg_percent_correct /= length
		    # avg_complete /= length
		    avg_percent_complete /= length
		    
		   
		    # if self.parentLevel == 2: # Added for Testing
		    #     avg_percent_student_completed = "" # Added for Testing
		    # else: # Added for Testing
		    #      avg_percent_student_completed /= length # Added for Testing
		    #      avg_percent_student_completed = "{0:.2%}".format(avg_percent_student_completed) # Added for Testing
		    values = [str(int(avg_number_of_attempts)),"{0:.2%}".format(avg_percent_complete)] #, avg_percent_student_completed, 15] # Added for testing last parameter

		    average = {'name': 'Average', 'values': values}
		    aggregation.append(average)
		return aggregation

	def pageData(self):
		result = self.parentLevelMethods[self.role]()
		return result

class SchoolDetails(BaseRoleAccess):
	def __init__(self, user, parentLevel):
		super(self.__class__, self).__init__(user, parentLevel)
		self.parentLevelMethods = [self.getSchoolsData, self.getSchoolsData, self.getSchoolsData, self.getClassData]	
		self.totalschools = {}

	def convert_to_string(self, data):
		data['id'] = str(data['id'])
		return data

	def getSchoolsData(self):
		school_list = []
		schools = UserInfoSchool.objects.filter(school_id__in = self.institutes)
		# Get all the schools, if schools exist
		for school in schools:
			school_info = {}
			classes_in_school = list(UserInfoClass.objects.filter(parent=school.school_id).extra(select={'id':'class_id','name':'class_name'}).values('id','name'))
			for classid in classes_in_school:
				students_in_class = list(UserInfoStudent.objects.filter(parent=classid['id']).extra(select={'id':'student_id','name':'student_name'}).values('id','name'))
				for std in students_in_class:
					std['id'] = str(std['id'])
				classid['children'] = students_in_class
			school_info['id'] = str(school.school_id)
			school_info['name'] = school.school_name
			school_info['children'] = list(map(self.convert_to_string, classes_in_school))
			school_list.append(school_info)
		self.totalschools["schools"] = school_list
		return self.totalschools

	def getClassData(self):
		class_info = {}
		class_list = []
		classes = list(UserInfoClass.objects.filter(class_id__in = self.classes).extra(select={'id':'class_id','name':'class_name'}).values('id','name'))
		for classid in classes:
			class_info = {}
			students_in_class = list(UserInfoStudent.objects.filter(parent=classid['id']).extra(select={'id':'student_id','name':'student_name'}).values('id','name'))
			for std in students_in_class:
					std['id'] = str(std['id'])
			class_info['children'] = students_in_class
			class_info['id'] = str(classid['id'])
			class_info['name'] = classid['name']
			class_list.append(class_info)
		self.totalschools["schools"] = class_list
		return self.totalschools

	def getPageData(self):
		result = self.parentLevelMethods[self.role]()
		return result






