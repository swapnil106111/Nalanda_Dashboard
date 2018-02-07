from account.models import * 
from django.contrib.auth.models import User, Group
from .constants import *
import datetime

class BaseRoleAccess(object):
	def __init__(self, user, parentID, parentLevel):
		""" Used to set meta data of mastery 
		attributes:
			user(object) = login user
			parentID(int) = Used to maintain hierarchy of claas, school and student data
							i) it could be school_id or class_id if user wants to see the class and student data 
							ii) default it should be "-1" 
			parentLevel(int) = Used to maintain hierarchy of claas, school and student data
							   i) exculding user as teacher parentLevel is set to 0 to view the visualizer
							   ii) Selction on class, school parent level changed for each user(1=schools, 2=class etc)
		"""
		parentLevelMethods = {1:self.boardMember, 2:self.schoolLeader, 3:self.teacher}	
		self.user = user
		self.role = 0

		# Check if user is superuser i.e admin. admin doesn't belongs to any group
		if not user.is_superuser:
			self.role = user.groups.values()[0]['id']

		if self.role == 3: # Set parentLevel = 1 for teacher. He/she dosen't have the permission of institutes. for first we have set it to 1
			parentLevel = 1 if parentLevel <= 0 else parentLevel

		if self.role in parentLevelMethods: # based on the role of user call the respective methods (only for School leader and teacher)
			schools, classes = parentLevelMethods[self.role]()
			level = {0: schools, 1:schools , 2: classes}

			print ("Schools:", schools)
			print ("classes:", classes)

			if parentID == -1: # Here set the parent id for teacher. when showing data of teacher we don't have the parent inforamtion for teacher user
				parentID = schools[0]

			if parentLevel in level and classes is not None: # Checked particular user have the access of schools or class
				if not parentID in level[parentLevel] and classes is not None:
					raise Exception("1. Not authorized to access the data")
				else:
					self.institutes = UserInfoSchool.objects.filter(school_id = schools[0])
					self.classes = UserInfoClass.objects.filter(class_id__in = classes)
			#1.Added here to BM who has access the certain set of school data if he/she selected schools while registration so we add funcationality for the BM. 
			#2.Default BM has access all the schools data."""
			elif self.role == 1 and classes is None:
				if (len(schools) > 0):
					self.institutes = UserInfoSchool.objects.filter(school_id__in = schools)
				else:
					self.institutes = UserInfoSchool.objects.filter(school_id = schools[0])
				print ("Institutes:", self.institutes)
				self.classes = None
			else:
				self.institutes = UserInfoSchool.objects.filter(school_id = schools[0])
				# raise Exception("2. Not authorized to access the data")

		# For user admin and board member we have fetched all the institues data
		# Only for admin user view all the schools data as per provide functionality to board Member who can view specific Schools data --Discussed with Harish
		elif self.role == 0:
			userMapping = UserRoleCollectionMapping.objects.filter(user_id= self.user)
			schools = list(userMapping.values_list('institute_id_id', flat=True))
			self.institutes = UserInfoSchool.objects.all()
			self.classes = None
		self.parentLevel = int(parentLevel)
		self.parentId = parentID


	def teacher(self):
		"""
		This function is used to fetch the mapping of classes and schools based on the user role 
		"""
		userMapping = UserRoleCollectionMapping.objects.filter(user_id = self.user)
		schools = list(userMapping.values_list('institute_id_id', flat = True))
		classes = list(userMapping.values_list('class_id_id', flat = True))
		return schools, classes

	def schoolLeader(self):
		"""
		This function is used to fetch the mapping of classes and schools based on the user role 
		"""
		userMapping = UserRoleCollectionMapping.objects.filter(user_id= self.user)
		schools = list(userMapping.values_list('institute_id_id', flat=True))
		classes = list(UserInfoClass.objects.filter(parent = schools[0]).values_list('class_id', flat = True))
		return schools, classes

	def boardMember(self):
		userMapping = UserRoleCollectionMapping.objects.filter(user_id= self.user)
		schools = list(userMapping.values_list('institute_id_id', flat=True))
		classes = None
		return schools, classes

	# AccessList = [2, 3]
	# def hasAccessSchool(self, parentID):
	# 	if self.role in AccessList:
	# 		userMapping = UserRoleCollectionMapping.objects.filter(user_id = self.user)
	# 		schools = list(userMapping.filter(institute_id_id = parentID).values_list('institute_id_id', flat = True))
	# 	else:
	# 		schools = UserInfoSchool.objects.all()

	# def hasAccessClass(self, parentID):
	# 	if self.role == 3:
	# 		userMapping = UserRoleCollectionMapping.objects.filter(user_id = self.user)
	# 		classes = list(userMapping.filter(class_id_id = parentID).values_list('class_id_id', flat = True))
	# 	else:
	# 		classes = None

class UserMasteryMeta(BaseRoleAccess):
	"""
	This is used to retrive the user meta information based on the role.

	"""

	def __init__(self, user,parentID, parentLevel):
		super(self.__class__, self).__init__(user, parentID, parentLevel)
		self.parentLevelMethods = [self.getInstituteMeta, self.getClassMeta, self.getStudentMeta]
		self.parentLevels = { 'institutes':0, 'school':1, 'class':2, 'students': 3 }

	# Construct the metrics format
	def construct_metrics(self):
		return metrics
    
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

	def getClassMeta(self, objBreadcrumb, rows):
		""" Used to fetch the class meta information
		Args:
			parentid(int): Used to retrive respective classes based on school_id(parentid)
			objBreadcrumb(list): used to set metadata(parentId, parentLevel, parentName)of class
			rows(list) = []
			role(int) = Role of the user i.e 1 = board member, 2 = school leader and 3 = teacher
		Returns:
			rows(list) = It returns classes meta information i.e class_id and class_name 
			objBreadcrumb(list) = It fetch the hierarchy level of class 

		"""
		if self.role != 3:
			objBreadcrumb.append(self.construct_breadcrumb("Institutes", 0, "-1"))

		school = self.institutes.filter(school_id = self.parentId)
		school_name = ""
		if school:
			school_name = school[0].school_name

		root = self.construct_breadcrumb(school_name, self.parentLevel , self.parentId)
		objBreadcrumb.append(root)

		objClasses = self.classes
		if self.classes == None:
			objClasses = UserInfoClass.objects.filter(parent = school[0].pk)

		for objclass in objClasses:
			class_info = {
				"id": str(objclass.class_id),
				"name": objclass.class_name
			}
			rows.append(class_info)

		return rows, objBreadcrumb

	def getStudentMeta(self, objBreadcrumb, rows):
		""" Used to fetch the stident meta inforamtion	
		Args:
			role_id(int) = role of a user_id
			parentId(int) =  used to retrive student information based on class_id(parentId)
			objBreadcrumb(list) = used to set metadata(parentId, parentLevel, parentName) of class and school
			rows(list) = []
		Returns:
			rows(list) = it reurns student inforamtion respective class
			objBreadcrumb(list) = it returns metadata(parentId, parentLevel, parentName) of class and school
		"""
		if self.classes:
			curr_class = self.classes.filter(class_id = self.parentId)
		else:
			curr_class = UserInfoClass.objects.filter(class_id = self.parentId)
		class_name = curr_class[0].class_name

		school = self.institutes.filter(school_id = curr_class[0].parent).first()

		if self.role != 3:
			objBreadcrumb.append(self.construct_breadcrumb("Institutes", 0, "-1"))

		if school:
			school_id = str(school.school_id)
			school_name = school.school_name
			objBreadcrumb.append(self.construct_breadcrumb(school_name, self.parentLevels['school'], school_id))
			objBreadcrumb.append(self.construct_breadcrumb(class_name, self.parentLevels['class'], self.parentId))

		objStudentData = UserInfoStudent.objects.filter(parent = self.parentId)
		if not objStudentData:
			return rows, objBreadcrumb
		for student in objStudentData:
			studentInfo = {
			'id': str(student.student_id),
			'name': student.student_name
			}
			rows.append(studentInfo)
		return rows, objBreadcrumb

	def getInstituteMeta(self, objBreadcrumb, rows):
		""" Used to fetch the institute meta information
		Args:
			objBreadcrumb(list) = used to set metadata(parentId, parentLevel, parentName) of institutes
			rows(list) = []
		Returns:
			objBreadcrumb(list) = it returns metadata(parentId, parentLevel, parentName) of institutes
			rows(list) = it returns institutes information
		"""
		objBreadcrumb.append(self.construct_breadcrumb("Institutes", 0, "-1"))	
		# print ("Institutes:", self.institutes)
		for institute in self.institutes:
			school_info = {
			    "id": str(institute.school_id),
			    "name": institute.school_name
			}
			rows.append(school_info)
		return rows, objBreadcrumb

	def getPageMeta(self):
		"""" Used to fetch mastery meta inforamtion
		Args:
			None
		Returns:
			response_object(dict) = it returns the code , title , message and meta data 
		"""
		code = 0
		title = ""
		message = ""
		rows = []
		objBreadcrumb = []
		objMetrics = self.construct_metrics()
		rows, objBreadcrumb = self.parentLevelMethods[self.parentLevel](objBreadcrumb, rows)
		
		data = { 'breadcrumb': objBreadcrumb, 'metrics': objMetrics, 'rows': rows }
		response_object = self.construct_response(code, title, message, data)
		return response_object 

class UserMasteryData(BaseRoleAccess):
	"""
	This function is used to fetch the mastery data of the user
	"""
	def __init__(self, user, parentID, parentLevel, topicID, channelID, startTimestamp, endTimestamp):
		super(self.__class__, self).__init__(user, parentID, parentLevel)
		self.topicID = topicID if topicID != '-1' else ''
		self.channelID = channelID
		endTimestamp = str(int(endTimestamp) + 86400)
		self.startTimestamp = datetime.date.fromtimestamp(int(startTimestamp)).strftime('%Y-%m-%d')
		self.endTimestamp = datetime.date.fromtimestamp(int(endTimestamp)).strftime('%Y-%m-%d')
		self.parentLevelMethods = [self.getInstitutesData, self.getClassData, self.getStudentData]
		self.parentLevels = { 'institutes':0, 'school':1, 'class':2, 'students': 3 }

	def getTopicsData(self):
		""" Used to calculate the total_questions based on the selected topicID and channelID
		Args:
			None
		Returns:
			total_questions(int) : Count of total_questions
		"""
		total_questions = 0
		filterTopics = {'topic_id':self.topicID}
		if self.topicID:
			filterTopics['channel_id']=self.channelID

		topic = Content.objects.filter(**filterTopics).first()
		total_questions = topic.total_questions
		return total_questions

	def getSubTopicsData(self):
		""" Used to calculate the total_subtopics based on the selected topicID and channelID
		Args:
			None
		Returns:
			total_questions(int) : Count of total_subtopics
		"""
		total_questions = 0
		filterTopics = {'topic_id':self.topicID}
		if self.topicID:
			filterTopics['channel_id']=self.channelID

		topic = Content.objects.filter(**filterTopics).first()
		total_subtopics = topic.sub_topics_total
		return total_subtopics

	def getLogData(self, masteryElement):
		""" Used to fetch the log data of each masteryElement(class, school, student)
		Args:
			masteryElement(obj): It could be class, school and student
		Returns:
			masteryData(Queryset): It contains mastry logs of each masteryElement
		"""

		filterTopics = {'content_id':self.topicID}
		filterTopics['date__range'] = (self.startTimestamp, self.endTimestamp)

		if self.topicID:
			filterTopics['channel_id']=self.channelID

		if self.parentLevel == 0:
			filterTopics['school_id'] = masteryElement
			masteryData = MasteryLevelSchool.objects.filter(**filterTopics)
		elif self.parentLevel == 1:
			filterTopics['class_id'] = masteryElement
			# print ("**filterTopics**:", **filterTopics)
			masteryData = MasteryLevelClass.objects.filter(**filterTopics)
		elif self.parentLevel == 2:
			filterTopics['student_id'] = masteryElement
			masteryData = MasteryLevelStudent.objects.filter(**filterTopics)
		return masteryData

	def getInstitutesData(self):
		""" Used to fetch the institutes mastery details
		Args:
			None
		Returns:
			data(dict): It contains rows of mastry data and it's aggregation
		"""
		res = list(map(self.getMastryLogDetails, self.institutes))
		aggregationResult = [res['aggregation'] for res in res]

		data = self.getMasteryAggregationData(aggregationResult, res)
		return data

	def getMasteryAggregationData(self, aggregationResult, masteryData):
		""" Used to Calculate the aggregation of each masteryElements
		Args:
			aggregationResult(list) : list of percentage vaue of four metrics
			masteryData(dict) = mastry data of masteryElements
		Returns:
			data(dict) = it contains aggregation result and mastery data of class, school
		"""
		data = {}	
		percent_complete_array = []
		percent_correct_array = []
		number_of_attempts_array = []
		percent_student_completed_array = []
		sample_metrix = []
		mastered_topics = []
		percent_mastered_topics = []
		for row in aggregationResult:
			mastered_topics.append(row[0])
			percent_mastered_topics.append(row[1])
			percent_complete_array.append(row[2])
			percent_correct_array.append(row[3])
			#percent_student_completed_array.append(row[2]) # Added for Testing
			number_of_attempts_array.append(row[4])
			sample_metrix.append(row[5]) # New matrix

		
		# Removed unwanted data of aggregation
		for row in masteryData:
			row.pop('aggregation', None)

		aggregation = self.getAggrigation(mastered_topics, percent_mastered_topics,percent_complete_array, percent_correct_array, number_of_attempts_array, sample_metrix)  # New matrix
		# aggregation = self.getAggrigation(percent_complete_array, percent_correct_array, number_of_attempts_array)#( percent_student_completed_array, 15) # Added for testing last paramter
		data['rows'] = masteryData
		data['aggregation'] = aggregation
		return data

	def getClassData(self):	
		""" Used to fetch mastery class data
		Args:
			None
		Returns:
			data(dict): It contains rows of mastry data and it's aggregation
		"""
		school = self.institutes.filter(school_id = self.parentId)
		objClasses = self.classes
		if self.classes == None:
			objClasses = UserInfoClass.objects.filter(parent = school[0].pk)

		res = list(map(self.getMastryLogDetails, objClasses))
		aggregationResult = [res['aggregation'] for res in res]
		data = self.getMasteryAggregationData(aggregationResult, res)
		return data

	def getStudentData(self):
		""" Used to fetch mastery student data
		Args:
			None
		Returns:
			data(dict): It contains rows of mastry data and it's aggregation
		"""
		students = UserInfoStudent.objects.filter(parent = self.parentId)
		if not students:
			return None
		res = list(map(self.getStudentDetails, students))
		
		aggregationResult = [res['aggregation'] for res in res] 
		data = self.getMasteryAggregationData(aggregationResult, res)
		return data

	def getStudentDetails(self, student):
		""" Used to fetch the stduent mastery details
		Args:
			studnt(obj): passed each student as args
			row(dict) : list of mastery data
		"""
		completed_questions = 0
		correct_questions = 0
		number_of_attempts = 0
		number_of_content = 0
		completed = True
		sample_metrix = 0 # New matrix
		mastered_topics = 0
		percent_mastered_topics = 0
		total_questions = self.getTopicsData() 
		mastery_students = self.getLogData(student)
		for mastery_student in mastery_students:
			mastered_topics += mastery_student.attempt_questions # future change 

			# Future change for percent_mastered_topics -- START
			percent_mastered_topics = mastery_student.completed_questions # future change
			# Future change for percent_mastered_topics -- END

			completed_questions += mastery_student.completed_questions
			correct_questions += mastery_student.correct_questions
			number_of_attempts += mastery_student.attempt_questions
			sample_metrix = 5 # New matrix
			# if completed: # Added for Testing
			# 	completed = mastery_student.completed and completed # Added for testing

		if len(mastery_students) == 0:
			completed = "0.00%"
			values = [0,"0.00%","0.00%", "0.00%", 0,"0.00%"]#, completed] # Added for Testing # New matrix
			# aggregation = [0.00, 0.00, completed, 0] # Added for Testing
			aggregation = [0, 0.00, 0.00, 0.00, 0, 0.00] # New matrix

			row = {'id': str(student.student_id), 'name': student.student_name, 'values': values, 'aggregation': aggregation}
		else:
			percent_complete_float = float(completed_questions) / total_questions
			percent_complete = "{0:.2%}".format(percent_complete_float)

			# Calculate the percentage of correct questions
			percent_correct_float = float(correct_questions) / total_questions
			percent_correct = "{0:.2%}".format(percent_correct_float)

			percent_sample_metrix = "{0:.2%}".format(0.05)


			
			# Future change for percent_mastered_topics -- START
			percent_mastered_topics_float = float(completed_questions) / total_questions 
			percent_mastered_topics = "{0:.2%}".format(percent_mastered_topics_float)
			# Future change for percent_mastered_topics -- END

			# Calculate the percentage of students completed the topic
			# if completed: # Added for Testing 
			# 	completed = "100.00%" # Added for Testing 
			# else: # Added for Testing 
			# 	completed = "0.00%" # Added for Testing 
			#values = [percent_complete, percent_correct, number_of_attempts, completed] # Added for testing
			values = [mastered_topics, percent_mastered_topics, percent_complete, percent_correct, number_of_attempts, percent_sample_metrix]
			#aggregation = [percent_complete_float, percent_correct_float, completed, number_of_attempts] # Added for Testing
			aggregation = [mastered_topics, percent_mastered_topics,percent_complete_float, percent_correct_float, number_of_attempts, percent_sample_metrix]

			row = {'id': str(student.student_id), 'name': student.student_name, 'values': values, 'aggregation': aggregation}
		return row

	def getMastryLogDetails(self, masteryElement):
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
		percent_mastered_topics = 0
		total_questions = self.getTopicsData() 
		objMasteryData = self.getLogData(masteryElement)

		for objMastery in objMasteryData:
			# print ("objMastery:", objMastery.attempt_questions)
			mastered_topics += objMastery.attempt_questions

			# Future change for percent_mastered_topics -- START
			percent_mastered_topics += objMastery.completed_questions 
			# Future change for percent_mastered_topics -- END

			completed_questions += objMastery.completed_questions
			correct_questions += objMastery.correct_questions
			number_of_attempts += objMastery.attempt_questions
			sample_metrix = 5
			# students_completed += objMastery.students_completed # Added for Testing
		
		# Filter mastery level belongs to a certain class with certain topic id, and within certain time range
		total_students = masteryElement.total_students
		if total_questions == 0 or total_students == 0:
			values = [0, "0.00%","0.00%", "0.00%", 0, "0.00%"]#, "0.00%", "0.00%"] # Added For Testing last "0.00%"
			aggregation = [0, "0.00%","0.00", "0.00", 0, "0.00%"] #, "0.00", "0.00%"] # Added For Testing last "0.00%"
			if self.parentLevel == 0:
				row = {'id': str(masteryElement.school_id), 'name': masteryElement.school_name, 'values': values, 'aggregation': aggregation}
			else:
				row = {'id': str(masteryElement.class_id), 'name': masteryElement.class_name, 'values': values, 'aggregation': aggregation}
		else:
			# Calculate the percentage of completed questions
			percent_complete_float = float(completed_questions) / (total_questions * total_students)
			percent_complete = "{0:.2%}".format(percent_complete_float)

			# Calculate the percentage of correct questions
			percent_correct_float = float(correct_questions) / (total_questions * total_students)
			percent_correct = "{0:.2%}".format(percent_correct_float)



			### Calculation for your matrix
			percent_sample_metrix = "{0:.2%}".format(0.05)


			# Future change for percent_mastered_topics -- START
			percent_mastered_topics_float = float(completed_questions) / (total_questions * total_students)
			percent_mastered_topics = "{0:.2%}".format(percent_mastered_topics_float)
			# Future change for percent_mastered_topics -- END
		
			# Calculate the percentage of students completed the topic
			# percent_student_completed_float = float(students_completed) / (total_students * total_questions) # Added for testing
			# percent_student_completed = "{0:.2%}".format(percent_student_completed_float) # Added for testing

			values = [mastered_topics, percent_mastered_topics, percent_complete, percent_correct, number_of_attempts, percent_sample_metrix]#, percent_student_completed, 15] # Added For Testing last parameter
			aggregation = [mastered_topics, percent_mastered_topics, percent_complete_float, percent_correct_float, number_of_attempts, percent_sample_metrix]#,  percent_student_completed_float, 15] # Added For Testing last parameter

			if self.parentLevel == 0:
				row = {'id': str(masteryElement.school_id), 'name': masteryElement.school_name, 'values': values, 'aggregation':aggregation}	
			else:
				row = {'id': str(masteryElement.class_id), 'name': masteryElement.class_name, 'values': values, 'aggregation': aggregation}
		return row


	def getAggrigation(self, mastered_topics, percent_mastered_topics, percentCompleteList, percentCorrectList, numberOfAttemptsList, fourthArgument_which_not_used_in_method): #, percentStudentCompletedList): # Added for testing
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
		avg_percent_complete = 0
		avg_percent_correct = 0
		avg_number_of_attempts = 0
		avg_percent_student_completed = 0
		avg_mastered_topics = 0
		avg_percent_mastered_topics = 0
		# Calculate the average for these four metrics
		length = len(percentCompleteList)
		if length != 0:
		    for i in range(length):
		    	avg_mastered_topics += numberOfAttemptsList[i]

		    	# Future change for percent_mastered_topics -- START
		    	avg_percent_mastered_topics += percentCompleteList[i]
		    	# Future change for percent_mastered_topics -- END

		    	avg_percent_complete +=  percentCompleteList[i]
		    	avg_percent_correct += percentCorrectList[i]
		    	avg_number_of_attempts += numberOfAttemptsList[i]
		        # if self.parentLevel != 2:  # Added for testing
		        #     avg_percent_student_completed += percentStudentCompletedList[i] # Added for Testing
		    avg_mastered_topics /= length
		    avg_percent_mastered_topics /= length
		    avg_percent_complete /= length
		    avg_percent_correct /= length
		    avg_number_of_attempts /= length
		    # if self.parentLevel == 2: # Added for Testing
		    #     avg_percent_student_completed = "" # Added for Testing
		    # else: # Added for Testing
		    #      avg_percent_student_completed /= length # Added for Testing
		    #      avg_percent_student_completed = "{0:.2%}".format(avg_percent_student_completed) # Added for Testing
		    values = [str(int(avg_mastered_topics)), "{0:.2%}".format(avg_percent_mastered_topics), "{0:.2%}".format(avg_percent_complete), "{0:.2%}".format(avg_percent_correct), str(int(avg_number_of_attempts)), "{0:.2%}".format(0.05)] #, avg_percent_student_completed, 15] # Added for testing last parameter

		    average = {'name': 'Average', 'values': values}
		    aggregation.append(average)
		print(aggregation)
		return aggregation
	
	def getPageData(self):
		result = self.parentLevelMethods[self.parentLevel]()
		return result




