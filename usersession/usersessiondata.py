from account.usermastery import BaseRoleAccess
from usersession.models import * 
from django.contrib.auth.models import User, Group
import datetime
from dateutil import parser

import traceback
import logging
logger = logging.getLogger(__name__)

class userSessionPageData(BaseRoleAccess):
	"""
	This function is used to fetch the user session data of the user
	"""
	def __init__(self, user, parentID, parentLevel, startTimestamp, endTimestamp, flag):
		super(self.__class__, self).__init__(user, parentID, parentLevel)
		# self.topicID = topicID if topicID != '-1' else ''
		# self.channelID = channelID
		# 
		self.flag = flag
		if self.flag == 0:
			start_date = Student.objects.all().order_by('-date').first()
			endTimestamp = int(start_date.date.timestamp())
			self.end = endTimestamp
			end_date = start_date.date + datetime.timedelta(-7)
			startTimestamp = int(end_date.timestamp())
			self.start = startTimestamp 
			self.startTimestamp = datetime.date.fromtimestamp(int(startTimestamp)).strftime('%Y-%m-%d')
			self.endTimestamp = datetime.date.fromtimestamp(int(endTimestamp)).strftime('%Y-%m-%d')
		else:
			# endTimestamp = str(int(endTimestamp) + 86400)
			self.start = startTimestamp
			self.end = endTimestamp
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
		try:
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
		except Exception as e:
			print (e)
			traceback.print_exc()
			logger.error(e)

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
		try:
			data = {}	
			sample_metrix = []
			total_active_time = []
			avg_active_time = []
			# minutes = []
			# seconds = []
			for row in aggregationResult:
				total_active_time.append(row[0])
				avg_active_time.append(row[1])
				# minutes.append(row[1])
				# seconds.append(row[2])
			# Removed unwanted data of aggregation
			for row in userSessionData:
				row.pop('aggregation', None)

			aggregation = self.getAggrigation(total_active_time, avg_active_time)  # New matrix
			# aggregation = self.getAggrigation(percent_complete_array, percent_correct_array, number_of_attempts_array)#( percent_student_completed_array, 15) # Added for testing last paramter
			data['rows'] = userSessionData
			data['aggregation'] = aggregation
			print ("getUserSessionAggregationData")
			return data
		except Exception as e:
			traceback.print_exc()
			print (e)
			logger.error(e)

	def getClassData(self):	
		""" Used to fetch usersession class data
		Args:
			None
		Returns:
			data(dict): It contains rows of usersession data and it's aggregation
		"""
		try:

			school = self.institutes.filter(school_id = self.parentId)
			objClasses = self.classes
			if self.classes == None:
				objClasses = UserInfoClass.objects.filter(parent = school[0].pk)

			res = list(map(self.getUserSessionLogDetails, objClasses))
			aggregationResult = [res['aggregation'] for res in res]
			data = self.getUserSessionAggregationData(aggregationResult, res)
			return data
		except Exception as e:
			traceback.print_exc()
			print (e)
			logger.error(e)

	def getStudentData(self):
		""" Used to fetch user session data
		Args:
			None
		Returns:
			data(dict): It contains rows of user session data and it's aggregation
		"""
		try:
			students = UserInfoStudent.objects.filter(parent = self.parentId)
			if not students:
				return None
			res = list(map(self.getStudentDetails, students))
			
			aggregationResult = [res['aggregation'] for res in res] 
			data = self.getUserSessionAggregationData(aggregationResult, res)
			data['level'] = self.parentLevel
			return data
		except Exception as e:
			traceback.print_exc()
			print (e)
			logger.error(e)

	def getStudentDetails(self, student):
		""" Used to fetch the stduent session details
		Args:
			studnt(obj): passed each student as args
			row(dict) : list of user session data
		"""

		try:
			total_usage = 0
			usersession_students = self.getLogData(student)
			for usersession_student in usersession_students:
				total_usage += usersession_student.total_usage
				
			if len(usersession_students) == 0:
				values = [0, 0]
				aggregation = [0, 0] 
				row = {'id': str(student.student_id), 'name': student.student_name, 'values': values, 'aggregation': aggregation,'startTimestamp':self.start,'endTimestamp':self.end,'flag':self.flag,'total':total_usage}
			else:
				m, s = divmod(total_usage, 60)
				h, m = divmod(m, 60)
				total_active_usage = "%d:%02d:%02d" % (h, m, s)
				values = [total_active_usage, total_active_usage]
				
				aggregation = [total_active_usage, total_active_usage]
				row = {'id': str(student.student_id), 'name': student.student_name, 'values': values, 'aggregation': aggregation, 'startTimestamp':self.start,'endTimestamp':self.end,'flag':self.flag,'total':total_usage}
			return row
		except Exception as e:
			traceback.print_exc()
			print (e)
			logger.error(e)

	def getUserSessionLogDetails(self, usersessionElement):
		""" Used to fetch user session details of any usersessionElement(i.e class, school and student)
		Args:
			usersessionElement(obj): fetched the school and class session details 
		Returns:
			row(dict) : It contains the usersession data of school or class
		"""
		try:
			aggregation = []
			rows = []
			values = []
			total_usage = 0
			
			objUsersessionData = self.getLogData(usersessionElement)
			print ("usersessionElement:", usersessionElement)

			for objUsersession in objUsersessionData:
				print ("Data:", objUsersession.total_usage)
				total_usage += int(objUsersession.total_usage)
			
			# Filter mastery level belongs to a certain class with certain topic id, and within certain time range
			total_students = usersessionElement.total_students
			if total_usage == 0:
				values = [0, 0]
				aggregation = [0, 0] 
				if self.parentLevel == 0:
					row = {'id': str(usersessionElement.school_id), 'name': usersessionElement.school_name, 'values': values, 'aggregation': aggregation,'startTimestamp':self.start,'endTimestamp':self.end,'flag':self.flag,'total':total_usage}
				else:
					row = {'id': str(usersessionElement.class_id), 'name': usersessionElement.class_name, 'values': values, 'aggregation': aggregation,'startTimestamp':self.start,'endTimestamp':self.end,'flag':self.flag,'total':total_usage}
			else:
				# Calculate the percentage of completed questions
				total_usersession_usage = float(total_usage) / total_students
	
				avg_total_active_usage = self.convert_time(total_usersession_usage)
				total_usage_data = self.convert_time(total_usage)
				
				values = [total_usage_data, avg_total_active_usage]
				aggregation = [total_usage_data, avg_total_active_usage]
				if self.parentLevel == 0:
					row = {'id': str(usersessionElement.school_id), 'name': usersessionElement.school_name, 'values': values, 'aggregation':aggregation,'startTimestamp':self.start,'endTimestamp':self.end,'flag':self.flag,'total':total_usage}	
				else:
					row = {'id': str(usersessionElement.class_id), 'name': usersessionElement.class_name, 'values': values, 'aggregation': aggregation,'startTimestamp':self.start,'endTimestamp':self.end,'flag':self.flag,'total':total_usage}
			print ("dddd")
			return row
		except Exception as e:
			traceback.print_exc()
			print (e)
			#logger.error(e)


	def getAggrigation(self, total_hoursList, avg_total_hours_list): 
		""" Used to calculate the aggregation for each usersessionElement based on metrics data
		Args:
			hoursList(list) :  List of total_usage(hours) of kolibri server

		Returns:
			aggregation[list] = returns average of metrics data in list
		"""
		try:
			aggregation = []
			avg_hours_usage = 0
			total_hours_usage = 0
			# avg_minutes_usage = 0
			# avg_seconds_usage = 0
		
			# Calculate the average for these four metrics
			length = len(total_hoursList)
			if length != 0:
			    for i in range(length):
			    	if avg_total_hours_list[i] == 0:
			    		continue
			    	p = avg_total_hours_list[i].split(':')
			    	k = total_hoursList[i].split(':')
			    	avg_hours_usage += int(p[0]) * 3600 + int(p[1])*60 + int(p[2])
			    	total_hours_usage += int(k[0]) * 3600 + int(k[1])*60 + int(k[2])

			    avg_hours_usage /= length
			    total_hours_usage /= length

			    avg_total_active_usage = self.convert_time(avg_hours_usage)
			    total_active_usage = self.convert_time(total_hours_usage)
			  
			    values = [total_active_usage, avg_total_active_usage] #, avg_percent_student_completed, 15] # Added for testing last parameter
			    average = {'name': 'Average', 'values': values}
			    aggregation.append(average)
			print ("ssssss")
			return aggregation
		except Exception as e:
			print (e)
			traceback.print_exc()
			logger.error(e)

	def getAggrigation_citywise(self, schools):
		try:
			school_aggr_city = []
			l = {'R':([], 'Rajsthan'), 'P':([],'Pune'), 'D':([],'Delhi'), 'M':([],'Mumbai')}

			for school in schools:
				if school['name'][0] in l.keys():
					l[school['name'][0]][0].append(school['total'])
			
			print ("L:", l)
			total_active_usage  = 0
			avg_active_usage = 0

			for k,v in l.items():
				p = {}
				total_active_usage  = 0
				avg_active_usage = 0
				total_active_usage_list = []
				if k in l.keys():
					if len(v[0]) > 0:
						print (v[0])
						print (v[1])
						result = sum(v[0])/len(v[0])
						avg_result = sum(v[0])/len(v[0])

						total_active_usage = self.convert_time(result)
						avg_active_usage = self.convert_time(avg_result)

						p['name'] = l[k][1]
						total_active_usage_list.append(total_active_usage)
						total_active_usage_list.append(avg_active_usage)
						#p['values'] = total_active_usage
					else:
						p['name'] = l[k][1]
						total_active_usage_list.append(total_active_usage)
						total_active_usage_list.append(avg_active_usage)

				p['values'] = total_active_usage_list
				school_aggr_city.append(p)
			return school_aggr_city
		except Exception as e:
			traceback.print_exc()
			print (e)
			logger.error(e)

	def convert_time(self, time):
		m, s = divmod(time, 60)
		h, m = divmod(m, 60)
		result = "%d:%02d:%02d" % (h, m, s)
		return result


	def getPageData(self):
		result = self.parentLevelMethods[self.parentLevel]()
		print ("Result:", result)
		# school_aggr_city = self.getAggrigation_citywise(result['rows'])
		# result['total'] = school_aggr_city
		return result





