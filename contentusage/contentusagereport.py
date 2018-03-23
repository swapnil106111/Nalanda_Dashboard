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
		print("schools:", schools)
		return schools, classes, channels

class ContentUsageMeta(BaseRoleAccess): 
	def __init__(self, user, parentLevel):
		super(self.__class__, self).__init__(user, parentLevel)
		print ("self.channels:", self.channels)
	# Construct the breadcrumb format
	def construct_breadcrumb(self, parentName, parentLevel, parentId):
		
		res = {
		"parentName": parentName,
		"parentLevel": parentLevel,
		"parentId": parentId
		}
		return res

	def construct_response(self, code, title, message, data):
		response_object = {}
		response_object["code"] = code
		response_object["info"] = {"title": title,"message": message}
		response_object["data"] = data
		return response_object

	def getInstituteMeta(self,objMetrics):
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
		objBreadcrumb.append(self.construct_breadcrumb("channels", 0, "-1"))
		objcontent = Content.objects.filter(topic_id__in=self.channels).values('topic_name','content_id','channel_id')
		for content in objcontent:
			print (content)
			channel_info = {
				"id": str(content['content_id']),
				"name": content['topic_name'],
				"channelid":str(content['channel_id'])
			}
			rows.append(channel_info)
		data = { 'breadcrumb': objBreadcrumb, 'metrics': objMetrics, 'rows': rows }
		response_object = self.construct_response(0, "", "", data)
		return response_object 

class ContentUsageData(BaseRoleAccess):
	def __init__(self, user, parentLevel, topicID, channelID, filtercriteria, startTimestamp, endTimestamp):
		super(self.__class__, self).__init__(user, parentLevel)
		self.topicID = topicID if topicID[0] != '-1' else ['']
		self.channelID = channelID if channelID[0] != '-1' else ['']
		endTimestamp = str(int(endTimestamp) + 86400)
		self.startTimestamp = datetime.date.fromtimestamp(int(startTimestamp)).strftime('%Y-%m-%d')
		self.endTimestamp = datetime.date.fromtimestamp(int(endTimestamp)).strftime('%Y-%m-%d')
		# self.parentLevelMethods = [self.getInstitutesData, self.getClassData, self.getStudentData]
		# self.parentLevels = { 'institutes':0, 'school':1, 'class':2, 'students': 3 }
		print ("institutes:", self.institutes)

	def getInstituteData(self, filtercriteria):
		if (filtercriteria == False):
			self.getContentUsageData(1);

	def getContentUsageData(self, contentusagecriteria):
		if (contentusagecriteria == 1):
			ContentUsageData1 = MasteryLevelSchool.objects.all()
		return ContentUsageData1

	def getContentUsageDetails():
		pass

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
			class_info['children'] = students_in_class
			class_info['id'] = classid['id']
			class_info['name'] = classid['name']
			class_list.append(class_info)
		self.totalschools["schools"] = class_list
		return self.totalschools

	def getPageData(self):
		print("Here")
		result = self.parentLevelMethods[self.role]()
		return result






