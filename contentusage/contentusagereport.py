from account.models import * 
from django.contrib.auth.models import User, Group
from account.constants import *
import datetime
import json, time
from django.db.models import Count
from contentusage.constants import *
from account.usermastery import BaseRoleAccess

# import the logging library
import logging

logger = logging.getLogger(__name__)

class BaseRoleAccess(object):
	def __init__(self, user, parentLevel):
		""" Used to set meta data of content usage metrics 
		Args:
			user(object) : login user
			parentLevel(int) : Used to maintain hierarchy of channe data 
		"""
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
		This function is used to fetch the mapping of classes and schools,channels based on the user role 
		"""
		try:
			userMapping = UserRoleCollectionMapping.objects.filter(user_id = self.user)
			schools = list(userMapping.values_list('institute_id_id', flat = True))
			classes = list(userMapping.values_list('class_id_id', flat = True))
			channels = list(MasteryLevelClass.objects.filter(class_id__in = classes).values_list('channel_id', flat = True).annotate(dcount=Count('channel_id')))[:-1]
			return schools, classes, channels
		except Exception as e:
			logger.error(e)

	def schoolLeader(self):
		"""
		This function is used to fetch the mapping of classes and schools,channels based on the user role 
		"""
		try:
			userMapping = UserRoleCollectionMapping.objects.filter(user_id= self.user)
			schools = list(userMapping.values_list('institute_id_id', flat=True))
			classes = list(UserInfoClass.objects.filter(parent = schools[0]).values_list('class_id', flat = True))
			channels = list(MasteryLevelSchool.objects.filter(school_id__in = schools).values_list('channel_id', flat = True).annotate(dcount=Count('channel_id')))[:-1]
			return schools, classes, channels
		except Exception as e:
			logger.error(e)

	def boardMember(self):
		"""
		This function is used to fetch the mapping of classes and schools,channels based on the user role 
		"""
		try:
			userMapping = UserRoleCollectionMapping.objects.filter(user_id=self.user)
			schools = list(userMapping.values_list('institute_id_id', flat=True))
			classes = None
			channels = list(MasteryLevelSchool.objects.filter(school_id__in = schools).values_list('channel_id', flat = True).annotate(dcount=Count('channel_id')))[:-1]
			return schools, classes, channels
		except Exception as e:
			logger.error(e)

class ContentUsageMeta(BaseRoleAccess): 
	def __init__(self, user, parentLevel, contentId, channelId, previousContentID, previousChannelID):
		""" Used to set the meta related information of channel based on the user role 
		Args:
			user(object) : login user
			parentLevel(int) : It's used to retrieve channels specific data
			contentId(str) : It's indicate content id of topic from channelID
			channelid(str) : ChannelId 
			previousContentID(list) : It's list of content id to set breadcrumb data for selected topic/content from channel(We don't have the parent child relations of content in current strucure)
			previousChannelID(list) : It's list of channel id's
		"""
		super(self.__class__, self).__init__(user, parentLevel)
		self.contentId = contentId
		self.channelId = channelId
		self.parentLevel = parentLevel
		self.parentLevelMethods = [self.getChannelMeta, self.getChannelTopicMeta, self.getChannelTopicMeta, self.getChannelTopicMeta, self.getChannelTopicMeta, self.getChannelTopicMeta, self.getChannelTopicMeta]
		self.previousContentlIDs = previousContentID
		self.previousChannelIDs = previousChannelID
	# Construct the breadcrumb format
	def construct_breadcrumb(self, parentName, parentLevel, parentId, channelId):
		""" It's used to bulid the breadcrumb data for selected topic
		Args:
			parentName(str) : Name of topic
			parentLevel(int) : It's used to maintain the hierarchy of topics while showing the breadcrumb data
			parentId(str) : Used to maintain parent - child relations 
			channelId(str) : It's contains channel id
		Return:
			res(dict) : It returns topic breadcrumb data
		"""
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
		""" Used to fetch the channel meta information
		Args:
			None
		Returns:
			objBreadcrumb(list) : it returns metadata(parentId, parentLevel, parentName, channelId) of topic
			rows(list) : it returns channel information
		"""
		try:
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
		except Exception as e:
			logger.error(e)

	def getChannelTopicMeta(self):
		""" It's used to fetch the channel subtopics meta upto the N level
		Args:
			None
		Returns:
			objBreadcrumb(list) : it returns metadata(parentId, parentLevel, parentName, channelId) of topic
			rows(list) : it returns channel information
		"""
		try:
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
		except Exception as e:
			logger.error(e)

	def getSubtopicDetails(self, subtopics, rows):
		""" It's used to get the subtopic details(i.e contet_id,channel_id of that topic)
		Args:
			subtopics(dict) : It's dict of childrens of selected topic
			rows(list) : It's an empty list to store the results
		Returns:
			rows(list) : It's contains the subtopic details
		"""
		try:
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
		except Exception as e:
			logger.error(e)

	def setBreadcrumbData(self, objBreadcrumb):
		""" It's used to set breadcrumb data of topic
		Args:
			objBreadcrumb(list) : It's list of dict of content parent-child hierarchy
		Returns : 
			objBreadcrumb(list) : It's return the result of breadcrumb data
		"""
		try:
			for content in zip(self.previousChannelIDs, self.previousContentlIDs):
				if content[1] != '-1':
					self.parentLevel += 1
					topic = Content.objects.filter(content_id = content[1], channel_id = content[0]).values('topic_name','content_id').first()
					objBreadcrumb.append(self.construct_breadcrumb(topic['topic_name'], self.parentLevel, topic['content_id'], content[0]))
			return objBreadcrumb
		except Exception as e:
			logger.error(e)

	def pageMeta(self, objMetrics):
		rows, objBreadcrumb = self.parentLevelMethods[self.parentLevel]()
		data = { 'breadcrumb': objBreadcrumb, 'metrics': objMetrics, 'rows': rows }
		response_object = self.construct_response(0, "", "", data)
		return response_object 

class ContentUsageData(BaseRoleAccess):
	def __init__(self, user, parentLevel, topicID, channelID, startTimestamp, endTimestamp, filterCriteria, filtetContentUsage, current_time1, level):
		""" It's used to set the conte usage data based on channel selection
		Args:
			user(object) : logined user
			parentLevel(int) : Used to call the channeldata methods
			topicID(str) : It's unique topc id
			channelID(str) : channel id 
			startTimestamp(datetime) : start time from where you want see the content usage data
			endTimestamp(datetime) : end time to view the data upto that datetime
			filterCriteria(bool) : its boolean value. True if user used school/class/student filter
			filtetContentUsage(list) : It's list of classes/schools or studnets based on selection
		"""
		super(self.__class__, self).__init__(user, parentLevel)
		self.topicID = topicID if topicID != '-1' else ''
		self.channelID = channelID if channelID != '-1' else ''
		endTimestamp = str(int(endTimestamp) + 86400)
		self.startTimestamp = datetime.date.fromtimestamp(int(startTimestamp)).strftime('%Y-%m-%d')
		self.endTimestamp = datetime.date.fromtimestamp(int(endTimestamp)).strftime('%Y-%m-%d')
		self.parentLevelMethods = [self.getChannelData, self.getChannelData, self.getChannelData, self.getChannelData]
		self.filterCriteria = filterCriteria
		self.filtetContentUsage = filtetContentUsage
		self.level = level
		# self.current_time = datetime.date.fromtimestamp(current_time1/1e3).strftime('%Y-%m-%d %H:%S')
		# self.current_time1 = current_time1

	def getChannelData(self):
		""" Used to get the content usage data 
		Args:
			None
		Returns:
			data(list) : It stores the content usage of details with metrics values(i.e attempt_questions, completed_questions). Also metrics aggregation result
		"""
		try:
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
		except Exception as e:
			logger.error(e)

	def getContentUsageData(self, channel):
		""" Used to get content usage data based on user role and filterCriteria of channel level
		Args:
			channel(str) : chnnel id (Get the metrics values of that channel)
		Returns:
			channeldata(queryset): It returns the queryset based on filters. i.e content used in class/schools/student
		"""
		try:
			filterTopics = {}
			filterTopics['date__range'] = (self.startTimestamp, self.endTimestamp)
			filterTopics['channel_id'] = channel
			filterTopics['content_id'] = channel

			if not self.filterCriteria and self.role != 3 and self.level == 0:
				filterTopics['school_id__in'] = self.institutes
				channeldata = MasteryLevelSchool.objects.filter(**filterTopics)
			elif self.filterCriteria and self.role != 3 and self.level == 2:
				filterTopics['school_id__in'] = self.filtetContentUsage
				channeldata = MasteryLevelSchool.objects.filter(**filterTopics)
			elif self.filterCriteria and self.role != 3 and self.level == 3:
				filterTopics['class_id__in'] = self.filtetContentUsage
				channeldata = MasteryLevelClass.objects.filter(**filterTopics)
			elif self.filterCriteria and self.role != 3 and self.level == 4:
				filterTopics['student_id_id__in'] = self.filtetContentUsage
				channeldata = MasteryLevelStudent.objects.filter(**filterTopics)
			elif not self.filterCriteria  and self.role == 3 and  self.level == 0:
				filterTopics['class_id__in'] = self.classes
				channeldata = MasteryLevelClass.objects.filter(**filterTopics)
			elif self.filterCriteria  and self.role == 3 and  self.level == 2:
				filterTopics['class_id__in'] = self.filtetContentUsage
				channeldata = MasteryLevelClass.objects.filter(**filterTopics)
			elif self.filterCriteria  and self.role == 3 and  self.level == 1:
				filterTopics['class_id__in'] = self.classes
				channeldata = MasteryLevelClass.objects.filter(**filterTopics)
			else:
				filterTopics['student_id_id__in'] = self.filtetContentUsage
				channeldata = MasteryLevelStudent.objects.filter(**filterTopics)
			return channeldata
		except Exception as e:
			logger.error(e)


	def getContentData(self, content_id, channel_id):
		""" Used to get content details to show the data for respective content usage meta ids
		Args:
			content_id(str) : content id who's content data and meta would be shown in table
			channel_id(str) : channel id 
		Returns:
			rows(list) : it contains list of dict from content details(i.e id, topic name, channelid etc...)
		"""
		try:
			rows = []
			objsubtopics = list(Content.objects.filter(content_id=content_id, channel_id=channel_id).values_list('sub_topics', flat = True))
			for obj in objsubtopics:
				result = json.loads(obj)
				if (result['children']):
					subtopics = result['children']
					rows = self.getSubtopicDetails(subtopics, rows)
			return rows
		except Exception as e:
			logger.error(e)

	def getSubtopicDetails(self, subtopics, rows):
		""" Used to get the subtopic(content) details
		Args:
			subtopics(dict) : subtopics data of content(i.e childrens of any content)
			rows (list) : It's an empty list to store the result
		Returns:
			rows(list) : It returns the content meta details

		"""
		try:
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
		except Exception as e:
			logger.error(e)

	def getChannelDataforsubtopics(self, content_id, channel_id):
		""" Used to get the topic usage at different level i.e school/class/students based on the user role and filterCriteria
		Args:
			channel_id (str) : content_id  belongs to this channel
			content_id (str) : content id
		Returns:
			channel_content_usage(queryset) : It returns the content usage of that topic with respective filter(class, school or class)
		"""
		
		try:
			filterTopics = {}
			filterTopics['date__range'] = (self.startTimestamp, self.endTimestamp)
			filterTopics['channel_id'] = channel_id
			filterTopics['content_id'] = content_id

			
			if not self.filterCriteria and self.role != 3 and self.level == 0:
				filterTopics['school_id__in'] = self.institutes
				channel_content_usage = MasteryLevelSchool.objects.filter(**filterTopics)

			elif self.filterCriteria and self.role != 3 and self.level == 2:
				filterTopics['school_id__in'] = self.filtetContentUsage
				channel_content_usage = MasteryLevelSchool.objects.filter(**filterTopics)
			elif self.filterCriteria and self.role != 3 and self.level == 3:
				filterTopics['class_id__in'] = self.filtetContentUsage
				channel_content_usage = MasteryLevelClass.objects.filter(**filterTopics)
			elif self.filterCriteria and self.role != 3 and self.level == 4:
				filterTopics['student_id_id__in'] = self.filtetContentUsage
				channel_content_usage = MasteryLevelStudent.objects.filter(**filterTopics)
			elif not self.filterCriteria  and self.role == 3 and  self.level == 0:
				filterTopics['class_id__in'] = self.classes
				channel_content_usage = MasteryLevelClass.objects.filter(**filterTopics)
			elif self.filterCriteria  and self.role == 3 and  self.level == 2:
				filterTopics['class_id__in'] = self.filtetContentUsage
				channeldata = MasteryLevelClass.objects.filter(**filterTopics)
			elif self.filterCriteria  and self.role == 3 and  self.level == 1:
				filterTopics['class_id__in'] = self.classes
				channel_content_usage = MasteryLevelClass.objects.filter(**filterTopics)
			else:
				filterTopics['student_id_id__in'] = self.filtetContentUsage
				channel_content_usage = MasteryLevelStudent.objects.filter(**filterTopics)
			# 	filterTopics['student_id_id__in'] = self.filtetContentUsage
			# 	channel_content_usage = MasteryLevelStudent.objects.filter(**filterTopics)
			return channel_content_usage
		except Exception as e:
			logger.error(e)

	def getContentUsageDrillDownDetails(self, content_id, channel_id, maxval):
		""" Used to get the topic details upto N level
		Args:
			content_id(str) : content id from channel who's metrics data will shown in table
			channel_id(str) : channel_id
			maxval(bool) : True/False. Used to identify should provide link in table or nor for content
		Returns:
			row(dict) : It stores the values and aggregation result of that content with it's detail to show on UI
		"""
		try:
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
		except Exception as e:
			logger.error(e)

	def getTopicsData(self):
		""" Used to calculate the total_questions based on the selected topicID and channelID
		Args:
			None
		Returns:
			total_questions(int) : Count of total_questions
		"""
		try:
			total_questions = 0
			if self.role == 3 and self.parentLevel == 0:
				topic = Content.objects.filter(channel_id__in = self.channels, content_id__in = self.channels).first()
				total_questions = topic.total_questions
			elif self.role == 2 and self.parentLevel == 0:
				topic = Content.objects.filter(channel_id__in = self.channels, content_id__in = self.channels).first()
				total_questions = topic.total_questions
			elif self.role == 1 and self.parentLevel == 0:
				topic = Content.objects.filter(channel_id__in = self.channels, content_id__in = self.channels).first()
				total_questions = topic.total_questions
			else:
				filterTopics = {'content_id':self.topicID}
				if self.topicID:
					filterTopics['channel_id'] = self.channelID
				topic = Content.objects.filter(**filterTopics).first()
				total_questions = topic.total_questions
			return total_questions
		except Exception as e:
			logger.error(e)

	def getContentUsageAggregationData(self, aggregationResult,contentUsageData):
		""" Used to Calculate the aggregation of each Content Usage Elements
		Args:
			aggregationResult(list) : list of percentage vaue of four metrics
			contentUsageData(dict) = mastry data of Content Usage Elements
		Returns:
			data(dict) = it contains aggregation result and content usage  data of channels with it's filters i.e school, class, students
		"""
		try:
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
		except Exception as e:
			logger.error(e)

	def getContentUsageDetails(self, channel):
		""" Used to fetch the content usage deails of only channel
		Args:
			channel(str): channel id 
		Returns:
			row(dict) : it stores the values and aggregation of that channel_id and it's own meta details
		"""
		try:
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
				objcontent = Content.objects.filter(topic_id=channel).values('topic_name','content_id','channel_id').first()
				row = {'id': str(objcontent['content_id']), 'name': objcontent['topic_name'], 'channelid': str(objcontent['channel_id']),'values': values, 'aggregation':aggregation,'maxval':False, 'total_questions':total_questions}	
				# if self.parentLevel == 0:
				# 	row = {'id': str(masteryElement.school_id), 'name': masteryElement.school_name, 'total_questions': total_questions, 'total_subtopics': total_subtopics, 'values': values, 'aggregation':aggregation}	
				# else:
				# 	row = {'id': str(masteryElement.class_id), 'name': masteryElement.class_name, 'total_questions': total_questions, 'total_subtopics': total_subtopics, 'values': values, 'aggregation': aggregation}
			return row
		except Exception as e:
			logger.error(e)

	def getAggrigation(self, numberOfAttemptsList,percentCompleteList):
		""" Used to calculate the aggregation for content usage metrics
		Args:
			percentCompleteList(list) :  List of completed questions(percentage)
			numberOfAttemptsList(int) : List of number of attempts 

		Returns:
			aggregation[list] = returns average of metrics data in list
		"""
		try:
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
		except Exception as e:
			logger.error(e)

	def pageData(self):
		result = self.parentLevelMethods[self.role]()
		return result

class SchoolDetails(BaseRoleAccess):
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
		try:
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
		except Exception as e:
			logger.error(e)

	def getClassData(self):
		""" Used to get class data for user 
		Args:
			None
		Returns:
			totalschools(dict) : returns class details with it's students
		"""
		try:
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
		except Exception as e:
			logger.error(e)

	def getPageData(self):
		result = self.parentLevelMethods[self.role]()
		return result

class TrendDetails(BaseRoleAccess):
	def __init__(self, user, startTimestamp,endTimestamp, parentLevel, itemId, itemchannelid, std, topicid, channelid, filetrcontetusage):
		""" Used to get the trend details of selected topic
		Args:
			user(object) :  Used to get graph detail for that user
			startTimestamp(datetime) : start date from where metrics data you want in graph 
			endTimestamp(datetime) : end date 
			parentLevel(int) : Used to show the data of channel of topic
			itemID(str) : channel_id or topic id
			itemchannelid(str) : channel id
			std(bool) : True/False. True if user select filter from facility dropdown
			topicid(str) : topic id to fetch total questions for that topic
			channelid(str) : channel_id
			filtetContentUsage(list) : It contains list of schools/class/students based on selection from Facility dropdown
		"""
		super(self.__class__, self).__init__(user, parentLevel)
		self.topicID = topicid if topicid != '-1' else ''
		self.channelID = channelid if channelid != '-1' else ''
		self.start = datetime.datetime.fromtimestamp(startTimestamp)
		self.end = datetime.datetime.fromtimestamp(endTimestamp)
		self.itemID = itemId
		self.itemchannelID = itemchannelid
		self.filterCriteria = std
		self.level = parentLevel
		self.filtetContentUsage = filetrcontetusage

	def get_trend(self):
		""" Used to get the trend details of topic based on role and filetrcontetusage selection
		Args:
			None
		Returns:
			res(list): It contains metrics value and it's series with datetime data
		"""
		try:
			total_questions = 0
			sub_topics_total = 0
			data = None
			content = None
			if self.parentLevel == 0:
				content = Content.objects.filter(topic_id='',content_id = '')
			else:
				content = Content.objects.filter(content_id=self.topicID,channel_id=self.channelID)

			for objcontent in content:
				total_questions += objcontent.total_questions

			total_students = 1.0

			if self.role == 0 or self.role == 1 or self.role == 2 and self.level >= 0:
				content = Content.objects.filter(content_id = self.itemID, channel_id = self.itemchannelID).values('topic_id','channel_id').first()
				if not self.filterCriteria:
					data = MasteryLevelSchool.objects.filter(school_id__in=self.institutes, content_id=content['topic_id'], channel_id = content['channel_id'], date__gte=self.start,date__lte=self.end).order_by('date')
				else:
					data = MasteryLevelStudent.objects.filter(student_id__in=self.filtetContentUsage, content_id=content['topic_id'], channel_id = content['channel_id'],\
					date__gte=self.start,date__lte=self.end).order_by('date')
			elif self.role == 3 and self.level >= 0:
				# classroom = UserInfoClass.objects.filter(class_id=item_id).first()
				# total_students = classroom.total_students
				content = Content.objects.filter(content_id = self.itemID, channel_id = self.itemchannelID).values('topic_id','channel_id').first()
				if not self.filterCriteria:
					data = MasteryLevelClass.objects.filter(class_id__in=self.classes,content_id=content['topic_id'],channel_id=content['channel_id'],date__gte=self.start,date__lte=self.end).order_by('date')
				else:
					data = MasteryLevelStudent.objects.filter(student_id__in=self.filtetContentUsage, content_id=content['topic_id'], channel_id=content['channel_id'],\
					date__gte=start,date__lte=end).order_by('date')
			# elif self.level == 3:
			# 	if topic_id[0] == "-1":
			# 		data = MasteryLevelStudent.objects.filter(student_id=item_id,content_id="",date__gte=start,date__lte=end).order_by('date')
			# 	else:
			# 		data = MasteryLevelStudent.objects.filter(student_id=item_id, content_id__in=topic_id, channel_id__in=channel_id,\
			# 		date__gte=start,date__lte=end).order_by('date')
			res = {}
			series = []
			# print ("Data:", data)
			# series.append({'name':'# Exercsie mastered','isPercentage':False})
			# series.append({'name':'# Exercsie attempts','isPercentage':False})
			# series.append({'name':'% Exercsie mastered','isPercentage':True})
			# series.append({'name':'# Question correct','isPercentage':False})
			series.append({'name':'# Question attempts','isPercentage':False})
			# series.append({'name':'% Question Correct','isPercentage':True})
			series.append({'name':'% Question completed','isPercentage':True})

			points = []
			completed_questions_sum = 0
			correct_questions_sum = 0
			attempt_questions_sum = 0
			attempts_exercise_sum = 0
			completed_sum = 0
			mastered_topics = 0
			percent_mastered_topics = 0
			for ele in data:
				temp = []
				completed_questions_sum += ele.completed_questions
				# mastered_topics += ele.mastered # future change
				# correct_questions_sum += ele.correct_questions
				attempt_questions_sum += ele.attempt_questions
				# attempts_exercise_sum += ele.attempt_exercise
				temp.append(time.mktime(ele.date.timetuple()))
				# temp.append(mastered_topics)
				# temp.append(attempts_exercise_sum)
				temp.append(attempt_questions_sum)
				# temp.append(100.0*mastered_topics/(sub_topics_total))
				# temp.append(correct_questions_sum)
				# temp.append(100.0*correct_questions_sum/(attempt_questions_sum))
				# temp.append(completed_questions_sum)
				temp.append(100.0*completed_questions_sum/(total_questions))
				points.append(temp)
			res['series'] = series
			res['points'] = points
			return res
		except Exception as e:
			logger.error(e)






