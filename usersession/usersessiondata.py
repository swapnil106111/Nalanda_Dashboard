from account.usermastery import BaseRoleAccess
from usersession.models import * 
from django.contrib.auth.models import User, Group
import datetime


class userSessionPageData(BaseRoleAccess):
	"""
	This function is used to fetch the user session data of the user
	"""
	def __init__(self, user, parentID, parentLevel, startTimestamp, endTimestamp):
		super(self.__class__, self).__init__(user, parentID, parentLevel)
		# self.topicID = topicID if topicID != '-1' else ''
		# self.channelID = channelID
		endTimestamp = str(int(endTimestamp) + 86400)
		self.startTimestamp = datetime.date.fromtimestamp(int(startTimestamp)).strftime('%Y-%m-%d')
		self.endTimestamp = datetime.date.fromtimestamp(int(endTimestamp)).strftime('%Y-%m-%d')
		self.parentLevelMethods = [self.getInstitutesData, self.getClassData, self.getStudentData]
		self.parentLevels = { 'institutes':0, 'school':1, 'class':2, 'students': 3 }

	def getLogData(self, userSessionElement):
		""" Used to fetch the log data of each user sessionElement(class, school, student)
		Args:
			userSessionElement(obj): It could be class, school and student
		Returns:
			usesSessionData(Queryset): It contains User session logs of each userSessionElement
		"""

		filterTopics = {}
		filterTopics['date__range'] = (self.startTimestamp, self.endTimestamp)

		if self.parentLevel == 0:
			filterTopics['school_id'] = userSessionElement
			usesSessionData = School.objects.filter(**filterTopics)
		elif self.parentLevel == 1:
			filterTopics['class_id'] = userSessionElement
			usesSessionData = Class.objects.filter(**filterTopics)
		elif self.parentLevel == 2:
			filterTopics['student_id'] = userSessionElement
			usesSessionData = Student.objects.filter(**filterTopics)
		return usesSessionData

	def getInstitutesData(self):
		""" Used to fetch the institutes tab session details
		Args:
			None
		Returns:
			data(dict): It contains rows of session usage data and it's aggregation
		"""
		res = list(map(self.getUserSessionLogDetails, self.institutes))
		aggregationResult = [res['aggregation'] for res in res]
		data = self.getUserSessionAggregationData(aggregationResult, res)
		return data

	def getUserSessionAggregationData(self, aggregationResult, userSessionData):
		""" Used to Calculate the aggregation of each user sessionElements
		Args:
			aggregationResult(list) : list of hours of total session usage 
			userSessionData(dict) = session data of user sessionElements
		Returns:
			data(dict) = it contains aggregation result and usersession data of class, school
		"""
		data = {}	
		sample_metrix = []
		total_active_time = []
		# minutes = []
		# seconds = []
		for row in aggregationResult:
			total_active_time.append(row[0])
			# minutes.append(row[1])
			# seconds.append(row[2])
		# Removed unwanted data of aggregation
		for row in userSessionData:
			row.pop('aggregation', None)

		aggregation = self.getAggrigation(total_active_time)  # New matrix
		# aggregation = self.getAggrigation(percent_complete_array, percent_correct_array, number_of_attempts_array)#( percent_student_completed_array, 15) # Added for testing last paramter
		data['rows'] = userSessionData
		data['aggregation'] = aggregation
		return data

	def getClassData(self):	
		""" Used to fetch usersession class data
		Args:
			None
		Returns:
			data(dict): It contains rows of usersession data and it's aggregation
		"""
		school = self.institutes.filter(school_id = self.parentId)
		objClasses = self.classes
		if self.classes == None:
			objClasses = UserInfoClass.objects.filter(parent = school[0].pk)

		res = list(map(self.getUserSessionLogDetails, objClasses))
		aggregationResult = [res['aggregation'] for res in res]
		data = self.getUserSessionAggregationData(aggregationResult, res)
		return data

	def getStudentData(self):
		""" Used to fetch user session data
		Args:
			None
		Returns:
			data(dict): It contains rows of user session data and it's aggregation
		"""
		students = UserInfoStudent.objects.filter(parent = self.parentId)
		if not students:
			return None
		res = list(map(self.getStudentDetails, students))
		
		aggregationResult = [res['aggregation'] for res in res] 
		data = self.getUserSessionAggregationData(aggregationResult, res)
		return data

	def getStudentDetails(self, student):
		""" Used to fetch the stduent session details
		Args:
			studnt(obj): passed each student as args
			row(dict) : list of user session data
		"""
		total_usage = 0
		usersession_students = self.getLogData(student)
		for usersession_student in usersession_students:
			total_usage += usersession_student.total_usage
			
		if len(usersession_students) == 0:
			values = [0]
			aggregation = [0] 
			row = {'id': str(student.student_id), 'name': student.student_name, 'values': values, 'aggregation': aggregation}
		else:
			m, s = divmod(total_usage, 60)
			h, m = divmod(m, 60)
			total_active_usage = "%d:%02d:%02d" % (h, m, s)
			values = [total_active_usage]
			
			aggregation = [total_active_usage]
			row = {'id': str(student.student_id), 'name': student.student_name, 'values': values, 'aggregation': aggregation}
		return row

	def getUserSessionLogDetails(self, usersessionElement):
		""" Used to fetch user session details of any usersessionElement(i.e class, school and student)
		Args:
			usersessionElement(obj): fetched the school and class session details 
		Returns:
			row(dict) : It contains the usersession data of school or class
		"""
		aggregation = []
		rows = []
		values = []
		total_usage = 0
		
		objUsersessionData = self.getLogData(usersessionElement)

		for objUsersession in objUsersessionData:
			total_usage += objUsersession.total_usage
		
		# Filter mastery level belongs to a certain class with certain topic id, and within certain time range
		total_students = usersessionElement.total_students
		if total_usage == 0:
			values = [0]
			aggregation = [0] 
			if self.parentLevel == 0:
				row = {'id': str(usersessionElement.school_id), 'name': usersessionElement.school_name, 'values': values, 'aggregation': aggregation}
			else:
				row = {'id': str(usersessionElement.class_id), 'name': usersessionElement.class_name, 'values': values, 'aggregation': aggregation}
		else:
			# Calculate the percentage of completed questions
			total_usersession_usage = float(total_usage) / total_students
			m, s = divmod(total_usersession_usage, 60)
			h, m = divmod(m, 60)
			total_active_usage = "%d:%02d:%02d" % (h, m, s)
			
			values = [total_active_usage]
			aggregation = [total_active_usage]
			if self.parentLevel == 0:
				row = {'id': str(usersessionElement.school_id), 'name': usersessionElement.school_name, 'values': values, 'aggregation':aggregation}	
			else:
				row = {'id': str(usersessionElement.class_id), 'name': usersessionElement.class_name, 'values': values, 'aggregation': aggregation}
		return row


	def getAggrigation(self, hoursList): 
		""" Used to calculate the aggregation for each usersessionElement based on metrics data
		Args:
			hoursList(list) :  List of total_usage(hours) of kolibri server

		Returns:
			aggregation[list] = returns average of metrics data in list
		"""
		aggregation = []
		avg_hours_usage = 0
		# avg_minutes_usage = 0
		# avg_seconds_usage = 0
	
		# Calculate the average for these four metrics
		length = len(hoursList)
		if length != 0:
		    for i in range(length):
		    	if hoursList[i] == 0:
		    		continue
		    	p = hoursList[i].split(':')
		    	avg_hours_usage += int(p[0]) * 3600 + int(p[1])*60 + int(p[2])
		    	# avg_minutes_usage += minutesList[i]
		    	# avg_seconds_usage += secondsList[i]
		   
		    avg_hours_usage /= length
		    m, s = divmod(avg_hours_usage, 60)
		    h, m = divmod(m, 60)
		    total_active_usage = "%d:%02d:%02d" % (h, m, s)
		    # avg_minutes_usage /= length
		    # avg_seconds_usage /= length 
		  
		    values = [total_active_usage] #, avg_percent_student_completed, 15] # Added for testing last parameter
		    average = {'name': 'Average', 'values': values}
		    aggregation.append(average)
		return aggregation
	
	def getPageData(self):
		result = self.parentLevelMethods[self.parentLevel]()
		return result





