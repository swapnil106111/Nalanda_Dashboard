from account.models import * 
from django.contrib.auth.models import User, Group
from .constants import *


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
		parentLevelMethods = {2:self.schoolLeader, 3:self.teacher}	
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

			if parentID == -1: # Here set the parent id for teacher. when showing data of teacher we don't have the parent inforamtion for teacher user
				parentID = schools[0]

			if parentLevel in level: # Checked particular user have the access of schools or class
				if not parentID in level[parentLevel]:
					raise Exception("1. Not authorized to access the data")
				else:
					self.institutes = UserInfoSchool.objects.filter(school_id = schools[0])
					self.classes = UserInfoClass.objects.filter(class_id__in = classes)
			else:
				raise Exception("2. Not authorized to access the data")

		# For user admin and board member we have fetched all the institues data
		else:
			self.institutes = UserInfoSchool.objects.all()
			self.classes = None
		self.parentLevel = parentLevel
		self.parentId = parentID


	def teacher(self):
		userMapping = UserRoleCollectionMapping.objects.filter(user_id= self.user)
		schools = list(userMapping.values_list('institute_id_id', flat=True))
		classes = list(userMapping.values_list('class_id_id', flat=True))
		return schools, classes

	def schoolLeader(self):
		userMapping = UserRoleCollectionMapping.objects.filter(user_id= self.user)
		schools = list(userMapping.values_list('institute_id_id', flat=True))
		classes = list(UserInfoClass.objects.filter(parent = schools[0]).values_list('class_id', flat=True))
		return schools, classes



class UserMasteryMeta(BaseRoleAccess):

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
			objBreadcrumb.append(self.construct_breadcrumb("Institutes", "0", "-1"))

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
			objBreadcrumb.append(self.construct_breadcrumb("Institutes", "0", "-1"))

		if school:
			school_id = str(school.school_id)
			school_name = school.school_name
			objBreadcrumb.append(self.construct_breadcrumb(school_name, self.parentLevels['school'], school_id))
			objBreadcrumb.append(self.construct_breadcrumb(class_name, self.parentLevels['class'], self.parentId))

		objStudentData = UserInfoStudent.objects.filter(parent = self.parentId)

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
		objBreadcrumb.append(self.construct_breadcrumb("Institutes", "0", "-1"))	
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



