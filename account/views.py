from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.template import Context, loader
from django.core.exceptions import ObjectDoesNotExist
# from nalanda.models import Users,UserInfoSchool, UserInfoClass, UserRoleCollectionMapping, UserInfoStudent
# from nalanda.models import Content, MasteryLevelStudent, MasteryLevelClass, MasteryLevelSchool, 
from account.models import LatestFetchDate, UserInfoClass, UserInfoSchool, UserRoleCollectionMapping, Content,  MasteryLevelStudent, MasteryLevelClass, MasteryLevelSchool, UserInfoStudent
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.utils import timezone
from django.core.urlresolvers import reverse
import json
import datetime
import time
from django.db.utils import DatabaseError, Error, OperationalError
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login
from axes.decorators import watch_login
from axes.utils import reset
from django.contrib.auth.forms import AuthenticationForm
from django.views.generic import UpdateView
from .forms import UserProfileForm
from axes.models import AccessAttempt

from .usermastery import UserMasteryMeta

# This function contructs the dict for every response
# code = 0 represents that the processing is sucessful
def construct_response(code, title, message, data):
    response_object = {}
    response_object["code"] = code
    response_object["info"] = {"title": title,"message": message}
    response_object["data"] = data
    return response_object

# This function implements the request receiving and response sending for login
# @csrf_exempt
@watch_login
def login_view(request):
    # If GET request is received, render the login page
    response_object ={}
    form = AuthenticationForm(None, request.POST)
    if request.method == 'POST':
    	if form.is_valid():
            login(request, form.get_user())
            response = redirect(reverse('report'))
            return response
    	else:
            data = form.errors.as_json()
            error_data = json.loads(data)
            for msg in error_data:
                message = error_data[msg][0]['message']
                response_object = construct_response(1001, "",message, {})
    response_object['form']=form
    return render(request, 'login.html', response_object)

# This function implements the request receiving and response sending for rending report homepage
@csrf_exempt
def report_homepage_view(request):
    if request.method == 'GET':
        code = 0
        title = ''
        message = ''
        try:
            latest_date = LatestFetchDate.objects.filter()
            if latest_date:
                data = {'dateUpdated': latest_date[0].latest_date}
            else:
                data = {}
            response_object = construct_response(code, title, message, data)
            return render(request, 'index.html', response_object)
        # If exception occurred, construct corresponding error info to the user
        except DatabaseError:
            code = 2001
            title = 'Sorry, error occurred in database operations'
            message = 'Sorry, error occurred in database operations'
            data = {}
            response_object = construct_response(code, title, message, data)
            return render(request, 'index.html', response_object)
        except OperationalError:
            code = 2011
            title = 'Sorry, operational error occurred'
            message = 'Sorry, operational error occurred'
            data = {}
            response_object = construct_response(code, title, message, data)
            return render(request, 'index.html', response_object)
        except:
            code = 2021
            title = 'Sorry, error occurred at the server'
            message = 'Sorry, error occurred at the server'
            data = {}
            response_object = construct_response(code, title, message, data)
            return render(request, 'index.html', response_object)
    else:
        return HttpResponse()

# This function implements the request receiving and response sending for register
@csrf_exempt
def register_view(request):
    # If GET request is received, render the register page, return the school and class info
    if request.method == 'GET':
    	response_str = {}
    	form = UserProfileForm(None, request.POST)
    	institutes = get_school_and_classes()
    	data = institutes
    	code = 0
    	title = ''
    	message = ''
    	response_object = construct_response(code, title, message, data)
    	response_text = json.dumps(response_object,ensure_ascii=False)
    	response_str = json.loads(response_text)
    	response_str['form'] = form
    	return render(request, 'register.html', response_str)
    # If POST request is received, process the request and return JSON object
    elif request.method == 'POST':
    	form = UserProfileForm(request.POST)
    	response = {}
    	if form.is_valid():
            form.save()
            response = construct_response(1006,"","User Registered successfully! Wait for admin approve the request ",{})
            form = UserProfileForm()
            response['form'] = form
            return render(request,'register.html', response)
    	else:
            data = form.errors.as_json()
            error_data = json.loads(data)
            for msg in error_data:
                message = error_data[msg][0]['message']
                message= str(msg)+" "+ message[4:] 
            response_text ={}
            response_text = construct_response(1007,"",message,{})
            form = UserProfileForm()
            response_text['form'] = form
            return render(request, 'register.html', response_text)

# This function gets all schools and classes in the database
def get_school_and_classes():
    
    school_info = {}
    school_id = ''
    school_name = ''
    schools = UserInfoSchool.objects.all()
    def convert_to_string(data):
            data['class_id'] = str(data['class_id'])
            return data
    # Get all the schools, if schools exist
    for school in schools:
        classes_in_school = list(UserInfoClass.objects.filter(parent=school.school_id).values('class_id','class_name'))   
        school_info[str(school.school_id)] = list(map(convert_to_string, classes_in_school))
    return school_info

# This function implements the request receiving and response sending for admin get pending and blocked users
def admin_get_view(request):
    if request.method == 'GET':
        role = request.user.is_superuser
        # If user is not an admin
        if not role: 
            code = 2031
            title = 'Sorry, you have to be admin to perform this action'
            message = 'Sorry, you have to be admin to perform this action'
            data = {}
            response_object = construct_response(code, title, message, data)
         # If user is an admin, render the admin-users page
        else:
            response_object = admin_get_post()
        return render(request, 'admin-users.html', response_object)
    else:
        return HttpResponse()

# This function implements the logic for admin get pending and blocked users
def admin_get_post():
    try:
        code = 0
        title = ''
        message = ''
        pending_users = []
        blocked_users = []
        # Get users that has not been approved
        pendings = User.objects.filter(is_active = False)
        print ("Pendings user:", pendings.values())
        if pendings:
            for pending in pendings:
                # Find the user according to user_id
                user = pending
                if not user:
                    continue
                userRoleClass = UserRoleCollectionMapping.objects.get(user_id=user)
                curr_class = userRoleClass.class_id
                institute = userRoleClass.institute_id
                instituteId = -1
                classId = -1
                instituteName = ''
                className = ''

                username = user.username
                email = user.email
                user_role = User.objects.get(id= user.id)
                user_group = Group.objects.get(user=user_role)
                role_name = user_group.name

                # Find corresponding class and school
                if curr_class:
                    className = curr_class.class_name
                    classId = curr_class.class_id
                if institute:
                    instituteId = institute.school_id
                    instituteName = institute.school_name
                pending_user = {'username': username, 'email': email, 'role': role_name, 'instituteId': instituteId, 'instituteName': instituteName, 'classId': classId, 'className': className}
                pending_users.append(pending_user)
        # Get users that has not been blocked
        blockeds = AccessAttempt.objects.filter(failures_since_start__gte=3)
        print ("blockeds:", blockeds)
        # blockeds = AccessAttempt.objects.filter(is_active = False)
        if blockeds:
            for blocked in blockeds:
                try:
                    user = User.objects.get(username=blocked.username)
                except user.DoesNotExist:
                    user = None
                    continue

                username = blocked.username
                email = user.email

                user_role = User.objects.get(id = user.id)
                user_group = Group.objects.get(user=user_role)
                role_name = user_group.name
                # Find the mapping according to user_id
                mappings = UserRoleCollectionMapping.objects.filter(user_id = user)
                # If corresponding mapping exists
                if mappings:
                    for mapping in mappings:
                        instituteId = -1
                        classId = -1
                        instituteName = ''
                        className = ''

                        institute = mapping.institute_id
                        # Find the schools and classes
                        if institute:
                            instituteId = institute.school_id
                            instituteName = institute.school_name
                        curr_class = mapping.class_id
                        if curr_class:
                            className = curr_class.class_name
                            classId = curr_class.class_id
                        blocked_user = {'username': username, 'email': email, 'role': role_name, 'instituteId': instituteId, 'instituteName': instituteName, 'classId': classId, 'className': className}
                        blocked_users.append(blocked_user)
                # If corresponding mapping doesn't exist, put instituteId and classId as -1
                else:
                    blocked_user = {'username': username, 'email': email, 'role': role_name, 'instituteId': -1, 'instituteName': '', 'classId': -1, 'className': ''}
                    blocked_users.append(blocked_user)
        data = {'pendingUsers': pending_users, 'blockedUsers': blocked_users}
        response_object = construct_response(code, title, message, data)
        return response_object
    # If exception occurred, construct corresponding error info to the user
    except Exception as e:
        print (e)
    # except DatabaseError:
    #     code = 2001
    #     title = 'Sorry, error occurred in database operations'
    #     message = 'Sorry, error occurred in database operations'
    #     data = {}
    #     response_object = construct_response(code, title, message, data)
    #     return response_object
    # except OperationalError:
    #     code = 2011
    #     title = 'Sorry, operational error occurred'
    #     message = 'Sorry, operational error occurred'
    #     data = {}
    #     response_object = construct_response(code, title, message, data)
    #     return response_object
    # except:
    #     code = 2021
    #     title = 'Sorry, error occurred at the server'
    #     message = 'Sorry, error occurred at the server'
    #     data = {}
    #     response_object = construct_response(code, title, message, data)
    #     return response_object

# This function implements the request receiving and response sending for logout
@csrf_exempt
def logout_view(request):
    # If GET request is received, render the index page
    if request.method == 'GET':
        try:
            logout(request)
            code = 0
            title = ""
            message = ""
            data = {}
            response_object = construct_response(code, title, message, data)
            response = render(request, 'login.html', response_object)
            # Clear the cookie
            response.delete_cookie('role')
            return response
        except:
            code = 2021
            title = 'Sorry, error occurred at the server'
            message = 'Sorry, error occurred at the server'
            data = {}
            response_object = construct_response(code, title, message, data)
            response_text = json.dumps(response_object,ensure_ascii=False)
            return render(request, 'login.html', response_object)
            #return HttpResponse(response_text,content_type='application/json')
    else:
        return HttpResponse()

# This function implements the request receiving and response sending for admin approve users
@csrf_exempt
def admin_approve_pending_users_view(request):
    if request.method == 'POST':
        role = request.user.is_superuser
        # If the user is not an admin
        if not role:
            code = 2031
            title = 'Sorry, you have to be admin to perform this action'
            message = 'Sorry, you have to be admin to perform this action'
            data = {}
            response_object = construct_response(code, title, message, data)
            print(response_object)
        # If the user is an admin, process the request
        else:
            body_unicode = request.body.decode('utf-8')
            data = json.loads(body_unicode)
            users = data.get('users',[])
            print ("Users:",users)
            response_object = admin_approve_pending_users_post(users)
            print(response_object)

        response_text = json.dumps(response_object,ensure_ascii=False)
        return HttpResponse(response_text)
    else:
        return HttpResponse()

# This function implements the logic for admin approve users
def admin_approve_pending_users_post(users):
    try:
        code = 0
        title = ''
        message = ''
        data = {}
        # If the users to be approved is not empty
        if len(users) != 0:
            for i in range(len(users)):
                username = users[i]["username"]
                result = User.objects.filter(username=username)
                if result:
                    # Mark the user as active
                    result[0].is_active = True
                    result[0].update_date = timezone.now()
                    result[0].save()
                    # If the user is a board memeber or leader, only one mapping exists
                    # if result[0].role_id == 1 or result[0].role_id == 2:
                    #     mapping = UserRoleCollectionMapping.objects.filter(user_id=result[0])
                    #     if mapping:
                    #         mapping[0].is_approved = True

                    #         mapping[0].save()
                    # # If the user is a teacher, multiple mappings to the classrooms exist
                    # elif result[0].role_id == 3:
                    #     classes = users[i]["classes"]
                    #     for j in range(len(classes)):
                    #         approve_class = UserInfoClass.objects.filter(class_id = classes[j])
                    #         if approve_class:
                    #             mapping = UserRoleCollectionMapping.objects.filter(user_id=result[0]).filter(class_id=approve_class[0])
                    #             if mapping:
                    #                 mapping[0].is_approved = True

                    #                 mapping[0].save()
        response_object = construct_response(code, title, message, data)

        return response_object
    # If exception occurred, construct corresponding error info to the user
    except DatabaseError:
        code = 2001
        title = 'Sorry, error occurred in database operations'
        message = 'Sorry, error occurred in database operations'
        data = {}
        response_object = construct_response(code, title, message, data)
        return response_object
    except OperationalError:
        code = 2011
        title = 'Sorry, operational error occurred'
        message = 'Sorry, operational error occurred'
        data = {}
        response_object = construct_response(code, title, message, data)
        return response_object
    except:
        code = 2021
        title = 'Sorry, error occurred at the server'
        message = 'Sorry, error occurred at the server'
        data = {}
        response_object = construct_response(code, title, message, data)
        return response_object

# This function implements the logic for admin disapprove users
def admin_disapprove_pending_users_post(users):
    code = 0
    title = ''
    message = ''
    data = {}
    try:
        if users:
            # If the users to be disapproved is not empty
            for i in range(len(users)):
                username = users[i]['username']
                result = User.objects.filter(username=username)
                if result:
                    result[0].delete()
        response_object = construct_response(code, title, message, data)
        return response_object
    # except Exception as e:
    #     print(e)
    except DatabaseError:
        code = 2001
        title = 'Sorry, error occurred in database operations'
        message = 'Sorry, error occurred in database operations'
        data = {}
        response_object = construct_response(code, title, message, data)
        return response_object
    except OperationalError:
        code = 2011
        title = 'Sorry, operational error occurred'
        message = 'Sorry, operational error occurred'
        data = {}
        response_object = construct_response(code, title, message, data)
        return response_object
    except:
        code = 2021
        title = 'Sorry, error occurred at the server'
        message = 'Sorry, error occurred at the server'
        data = {}
        response_object = construct_response(code, title, message, data)
        return response_object

# This function implements the request receiving and response sending for admin approve users
@csrf_exempt
def admin_disapprove_pending_users_view(request):
    if request.method == 'POST':
        role = request.user.is_superuser
        # If the user is not an admin
        if not role:
            code = 2031
            title = 'Sorry, you have to be admin to perform this action'
            message = 'Sorry, you have to be admin to perform this action'
            data = {}
            response_object = construct_response(code, title, message, data)
            print(response_object)
        # If the user is an admin, process the request
        else:
            body_unicode = request.body.decode('utf-8')
            data = json.loads(body_unicode)
            users = data.get('users',[])
            print("users = ", users)
            response_object = admin_disapprove_pending_users_post(users)
            print(response_object)
        response_text = json.dumps(response_object,ensure_ascii=False)

        return HttpResponse(response_text)
    else:
        return HttpResponse()

# This function implements the logic for admin unblock users
def admin_unblock_users_post(usernames):
    code = 0
    title = ''
    message = ''
    data = {}
    try:
        if usernames:
            for i in range(len(usernames)):
                # Check if the username exists
                username = usernames[i]
                acess_atempts = AccessAttempt.objects.get(username = username)
                result = User.objects.get(username=username)
                # If exists, change is_active to True, and clear the number_of_failed_attempts
                if result and acess_atempts:
                    result.is_active = True;
                    # result[0].number_of_failed_attempts = 0;
                    acess_atempts.failures_since_start = 0
                    result.update_date = timezone.now()
                    result.save()
                    acess_atempts.save()
        response_object = construct_response(code, title, message, data)
        return response_object
    # If exception occurred, construct corresponding error info to the user
    except DatabaseError:
        code = 2001
        title = 'Sorry, error occurred in database operations'
        message = 'Sorry, error occurred in database operations'
        data = {}
        response_object = construct_response(code, title, message, data)
        return response_object
    except OperationalError:
        code = 2011
        title = 'Sorry, operational error occurred'
        message = 'Sorry, operational error occurred'
        data = {}
        response_object = construct_response(code, title, message, data)
        return response_object
    except:
        code = 2021
        title = 'Sorry, error occurred at the server'
        message = 'Sorry, error occurred at the server'
        data = {}
        response_object = construct_response(code, title, message, data)
        return response_object

# This function implements the request receiving and response sending for admin unblock users
@login_required(login_url='/account/login/')
@user_passes_test(lambda u: u.is_superuser)
def admin_unblock_users_view(request):
    if request.method == 'POST':
        # role = request.user.is_superuser
        # # If the user is not an admin
        # if not role:
        #     code = 2031
        #     title = 'Sorry, you have to be admin to perform this action'
        #     message = 'Sorry, you have to be admin to perform this action'
        #     data = {}
        #     response_object = construct_response(code, title, message, data)

        # # If the user is an admin, process the request
        # else:
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        usernames = data.get('usernames',[])
        response_object = admin_unblock_users_post(usernames)
        # print(response_object)
        response_text = json.dumps(response_object,ensure_ascii=False)
        return HttpResponse(response_text)
    else:
        return HttpResponse()

# This function implements the logic for get page meta
def get_page_meta(parent_id, parent_level, user_id, role):
    try:
        parent_level = int(parent_level)
        print ("Parent_id:"+str(parent_id)+" "+"Parent_level:"+str(parent_level))
        code = 0
        title = ''
        message = ''
        # If the parent_level and parent_id info is not complete
        if parent_level == -1 or parent_id == -2:
            code = 2031
            title = 'Parent level or parent id is missing'
            message = 'Parent level or parent id is missing'
            data = {}
         # If the parent_level and parent_id info is complete
        else:

            metrics = construct_metrics()
            breadcrumb = []
            rows = []
            if role != 3:
                root = construct_breadcrumb("Institutues", 0, 0)
                # For all possbile levels, root should be present
                breadcrumb.append(root)
            #If the partent level is root
            if parent_level == 0:
                # Return all the schools
                schools = UserInfoSchool.objects.filter()
                if schools:
                    for school in schools:
                        temp = {
                            "id": str(school.school_id),
                            "name": school.school_name
                        }
                        rows.append(temp)
            # If the parent level is school
            elif parent_level == 1:
                # Add current level school to the breadcrumb
                school = UserInfoSchool.objects.filter(school_id = parent_id)
                if school:
                    school_name = school[0].school_name
                    if int(role) == 3:
                        breadcrumb.append(construct_breadcrumb("Classes", 1, parent_id))
                    else:
                        breadcrumb.append(construct_breadcrumb(school_name, 1, parent_id))

                # Return all the classrooms inside a school

                    classes = UserInfoClass.objects.filter(parent = parent_id)
                    if classes:
                        for curr_class in classes:
                            user_role_class = UserRoleCollectionMapping.objects.get(user_id_id = user_id)
                            if user_role_class.class_id_id == curr_class.class_id:
                                temp = {
                                    "id": str(curr_class.class_id),
                                    "name": curr_class.class_name
                                }
                                rows.append(temp)
            # If the parent level is class
            elif parent_level == 2:
                #Add current level class to the breadcrumb
                curr_class = UserInfoClass.objects.filter(class_id = parent_id)
                if curr_class:
                    class_name = curr_class[0].class_name

                #Add higher level school to the breadcrumb
                    school = UserInfoSchool.objects.filter(school_id = curr_class[0].parent).first()
                    if school:
                        school_id = str(school.school_id)
                        school_name = school.school_name
                        breadcrumb.append(construct_breadcrumb(school_name, 1, school_id))
                        breadcrumb.append(construct_breadcrumb(class_name, 2, parent_id))
                    # Return all students inside a classroom
                students = UserInfoStudent.objects.filter(parent = parent_id)
                # Return all students inside a classroom
                #students = UserInfoStudent.objects.filter(parent = curr_class[0])
                if students:
                    for student in students:
                        temp = {
                            'id': str(student.student_id),
                            'name': student.student_name
                        }
                        rows.append(temp)
            data = {'breadcrumb': breadcrumb, 'metrics': metrics, 'rows': rows}
        response_object = construct_response(code, title, message, data)
        return response_object
    # If exception occurred, construct corresponding error info to the user
    except Exception as e:
        print (e)
    # except DatabaseError:
    #     code = 2001
    #     title = 'Sorry, error occurred in database operations'
    #     message = 'Sorry, error occurred in database operations'
    #     data = {}
    #     response_object = construct_response(code, title, message, data)
    #     return response_object
    # except OperationalError:
    #     code = 2011
    #     title = 'Sorry, operational error occurred'
    #     message = 'Sorry, operational error occurred'
    #     data = {}
    #     response_object = construct_response(code, title, message, data)
    #     return response_object
    # except:
    #     code = 2021
    #     title = 'Sorry, error occurred at the server'
    #     message = 'Sorry, error occurred at the server'
    #     data = {}
    #     response_object = construct_response(code, title, message, data)
    #     return response_object


# This function implements the request receiving and response sending for get page meta
@csrf_exempt
def get_page_meta_view(request):   
    user = request.user
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    parent_level = data.get('parentLevel', -2)
    parent_id = int(data.get('parentId', '').strip())
    objUserMastery = UserMasteryMeta(user, parent_id, parent_level)
    objUserData = objUserMastery.getPageMeta()
    response_text = json.dumps(objUserData,ensure_ascii=False)
    return HttpResponse(response_text,content_type='application/json')

# This function implements the logic for get page data
def get_page_data(parent_id, parent_level, topic_id, end_timestamp, start_timestamp, channel_id, user, role):
    try:
        # print (str(parent_id) + " : "+ str(parent_level)+ " : "+str(topic_id)+ " : "+str(end_timestamp)+ " : "+str(start_timestamp)+ " : "+str(channel_id))
        parent_level = int(parent_level)
        code = 0
        title = ''
        message = ''
        data = {}
        # If the input data is not complete
        if parent_level == -1 or parent_id == -2 or topic_id == '' or (not start_timestamp) or (not end_timestamp) or channel_id == '':
            code = 2031
            title = 'Argument is missing'
            message = 'Argument is missing'
            data = {}
        # If the input data is complete
        else:
            # print ("Inside else get_page_data")
            rows = []
            aggregation = []
            percent_complete_array = []
            percent_correct_array = []
            number_of_attempts_array = []
            percent_student_completed_array = []

            values = []
            total_questions = 0
            # Since in django select range function, the end_date is not included, hence increase the date by one day
            end_timestamp = str(int(end_timestamp) + 86400)
            # Convert from Unix timestamp to datetime
            start_timestamp = datetime.date.fromtimestamp(int(start_timestamp)).strftime('%Y-%m-%d')
            end_timestamp = datetime.date.fromtimestamp(int(end_timestamp)).strftime('%Y-%m-%d')
            # If the user wants to view everything
            if topic_id == '-1' and channel_id == '-1':
                topic = Content.objects.filter(topic_id = "").first()
            # If the user has specified content_id and channel_id
            else:
                topic = Content.objects.filter(topic_id=topic_id).filter(channel_id = channel_id).first()

            if topic:
                total_questions = topic.total_questions

            # print ("Total questions:", total_questions)


            # If the current level is root
            if parent_level == 0:
                # Return all the schools
                schools = UserInfoSchool.objects.all()
                # For each school, calculate
                if schools:
                    for school in schools:
                        # Get school id and name
                        school_id = str(school.school_id)
                        school_name = school.school_name
                        completed_questions = 0
                        correct_questions = 0
                        number_of_attempts = 0
                        students_completed = 0
                        total_students = 0


                        # Filter all mastery level logs belong to a certain school within certain time range
                        if topic_id == '-1':
                            mastery_schools = MasteryLevelSchool.objects.filter(school_id=school).filter(content_id="").filter(date__range=(start_timestamp, end_timestamp))
                        else:
                             mastery_schools = MasteryLevelSchool.objects.filter(school_id=school).filter(channel_id=channel_id).filter(content_id=topic_id).filter(date__range=(start_timestamp, end_timestamp))
                        if mastery_schools:

                            for mastery_school in mastery_schools:
                                completed_questions += mastery_school.completed_questions
                                correct_questions += mastery_school.correct_questions
                                number_of_attempts += mastery_school.attempt_questions
                                students_completed += mastery_school.students_completed





                        total_students = school.total_students
                        if total_questions == 0 or total_students == 0:
                            values = ["0.00%", "0.00%", 0, "0.00%"]
                            row = {'id': school_id, 'name': school_name, 'values': values}
                            rows.append(row)
                            continue


                        # Calculate the percentage of completed questions
                        percent_complete_float = float(completed_questions) / (total_questions * total_students)
                        percent_complete = "{0:.2%}".format(percent_complete_float)
                        percent_complete_array.append(percent_complete_float)

                        # Calculate the percentage of correct questions

                        percent_correct_float = float(correct_questions) / (total_questions * total_students)
                        percent_correct = "{0:.2%}".format(percent_correct_float)
                        percent_correct_array.append(percent_correct_float)

                        # Get the number of attempted questions

                        number_of_attempts_array.append(number_of_attempts)

                        # Calculate the percentage of students completed the topic

                        percent_student_completed_float = float(students_completed) / (total_students * total_questions)
                        percent_student_completed = "{0:.2%}".format(percent_student_completed_float)
                        percent_student_completed_array.append(percent_student_completed_float)

                        values = [percent_complete, percent_correct, number_of_attempts, percent_student_completed]
                        row = {'id': school_id, 'name': school_name, 'values': values}
                        rows.append(row)

            # If the parent level is school
            elif parent_level == 1:
                # Find the current school
                school = UserInfoSchool.objects.filter(school_id = parent_id)

                # Return all the classrooms inside a school
                if school:
                    classes = UserInfoClass.objects.filter(parent = parent_id)
                    if classes:
                        if int(role) == 3:
                            user_class_institute = UserRoleCollectionMapping.objects.get(user_id_id = user) 
                        for curr_class in classes:
                            # Get class id and name
                            if user_class_institute.class_id_id == curr_class.class_id:
                                class_id = str(curr_class.class_id)
                                class_name = curr_class.class_name
                                completed_questions = 0
                                correct_questions = 0
                                number_of_attempts = 0
                                students_completed = 0
                                total_students = 0


                                # Filter all mastery level logs belongs to a certain class within certain time range
                                if topic_id == '-1':
                                    mastery_classes = MasteryLevelClass.objects.filter(class_id=curr_class).filter(content_id="").filter(date__range=(start_timestamp, end_timestamp))
                                else:
                                     mastery_classes = MasteryLevelClass.objects.filter(class_id=curr_class).filter(channel_id=channel_id).filter(content_id=topic_id).filter(date__range=(start_timestamp, end_timestamp))

                                if mastery_classes:
                                    for mastery_class in mastery_classes:
                                        completed_questions += mastery_class.completed_questions
                                        correct_questions += mastery_class.correct_questions
                                        number_of_attempts += mastery_class.attempt_questions
                                        students_completed += mastery_class.students_completed

                                # Filter mastery level belongs to a certain class with certain topic id, and within certain time range


                                total_students = curr_class.total_students
                                if total_questions == 0 or total_students == 0:
                                    values = ["0.00%", "0.00%", 0, "0.00%"]
                                    row = {'id': class_id, 'name': class_name, 'values': values}
                                    rows.append(row)
                                    continue

                                # Calculate the percentage of completed questions
                                percent_complete_float = float(completed_questions) / (total_questions * total_students)
                                percent_complete = "{0:.2%}".format(percent_complete_float)
                                percent_complete_array.append(percent_complete_float)

                                # Calculate the percentage of correct questions

                                percent_correct_float = float(correct_questions) / (total_questions * total_students)
                                percent_correct = "{0:.2%}".format(percent_correct_float)
                                percent_correct_array.append(percent_correct_float)

                                # Get the number of attempted questions

                                number_of_attempts_array.append(number_of_attempts)

                                # Calculate the percentage of students completed the topic

                                percent_student_completed_float = float(students_completed) / (total_students * total_questions)
                                percent_student_completed = "{0:.2%}".format(percent_student_completed_float)
                                percent_student_completed_array.append(percent_student_completed_float)

                                values = [percent_complete, percent_correct, number_of_attempts, percent_student_completed]
                                row = {'id': class_id, 'name': class_name, 'values': values}
                                rows.append(row)


            # If the parent level is class
            elif parent_level == 2:
                curr_class = UserInfoClass.objects.filter(class_id = parent_id)
                # Return all the students inside a class
                if curr_class:
                    students = UserInfoStudent.objects.filter(parent = parent_id)
                    if students:
                        for student in students:
                            # Get class id and name
                            student_id = str(student.student_id)
                            # Get student id and name

                            student_name = student.student_name
                            completed_questions = 0
                            correct_questions = 0
                            number_of_attempts = 0
                            number_of_content = 0
                            completed = True




                            # Filter mastery level belongs to a certain student within certain time range
                            if topic_id == '-1':
                                mastery_students = MasteryLevelStudent.objects.filter(student_id=student).filter(content_id="").filter(date__range=(start_timestamp, end_timestamp))
                            else:
                                mastery_students = MasteryLevelStudent.objects.filter(student_id=student).filter(channel_id=channel_id).filter(content_id=topic_id).filter(date__range=(start_timestamp, end_timestamp))


                            # Filter mastery level belongs to a certain student with certain topic id, and within certain time range

                            if mastery_students:
                                for mastery_student in mastery_students:
                                    completed_questions += mastery_student.completed_questions
                                    correct_questions += mastery_student.correct_questions
                                    number_of_attempts += mastery_student.attempt_questions
                                    if completed:
                                        completed = mastery_student.completed and completed


                            if len(mastery_students) == 0:
                                values = ["0.00%", "0.00%", 0, "0.00%"]
                                row = {'id': student_id, 'name': student_name, 'values': values}
                                rows.append(row)
                                continue

                            # Calculate the percentage of completed questions
                            percent_complete_float = float(completed_questions) / total_questions
                            percent_complete = "{0:.2%}".format(percent_complete_float)
                            percent_complete_array.append(percent_complete_float)

                            # Calculate the percentage of correct questions

                            percent_correct_float = float(correct_questions) / total_questions
                            percent_correct = "{0:.2%}".format(percent_correct_float)
                            percent_correct_array.append(percent_correct_float)

                            # Get the number of attempted questions

                            number_of_attempts_array.append(number_of_attempts)

                            # Calculate the percentage of students completed the topic

                            if completed:
                                completed = "100.00%"
                                percent_student_completed_array.append("100%")
                            else:
                                completed = "0.00%"
                                percent_student_completed_array.append("0%")

                            values = [percent_complete, percent_correct, number_of_attempts, completed]
                            row = {'id': student_id, 'name': student_name, 'values': values}
                            rows.append(row)
            avg_percent_complete = 0
            avg_percent_correct = 0
            avg_number_of_attempts = 0
            avg_percent_student_completed = 0


            # Calculate the average for these four metrics
            length = len(percent_complete_array)
            if length != 0:
                for i in range(length):
                    avg_percent_complete +=  percent_complete_array[i]
                    avg_percent_correct += percent_correct_array[i]
                    avg_number_of_attempts += number_of_attempts_array[i]
                    if parent_level != 2:
                        avg_percent_student_completed += percent_student_completed_array[i]
                avg_percent_complete /= length
                avg_percent_correct /= length
                avg_number_of_attempts /= length
                if parent_level == 2:
                    avg_percent_student_completed = ""
                else:
                     avg_percent_student_completed /= length
                     avg_percent_student_completed = "{0:.2%}".format(avg_percent_student_completed)
                values = ["{0:.2%}".format(avg_percent_complete), "{0:.2%}".format(avg_percent_correct), str(int(avg_number_of_attempts)), avg_percent_student_completed]
                average = {'name': 'Average', 'values': values}
                aggregation.append(average)
            data = {'rows': rows, 'aggregation': aggregation}
        # print ("data:", data)    
        response_object = construct_response(code, title, message, data)

        return response_object
    except Exception as e:
        print (e) 
    # If exception occurred, construct corresponding error info to the user
'''
    except DatabaseError:
        code = 2001
        title = 'Sorry, error occurred in database operations'
        message = 'Sorry, error occurred in database operations'
        data = {}
        response_object = construct_response(code, title, message, data)
        return response_object
    except OperationalError:
        code = 2011
        title = 'Sorry, operational error occurred'
        message = 'Sorry, operational error occurred'
        data = {}
        response_object = construct_response(code, title, message, data)
        return response_object
    except:
        code = 2021
        title = 'Sorry, error occurred at the server'
        message = 'Sorry, error occurred at the server'
        data = {}
        response_object = construct_response(code, title, message, data)
        return response_object
'''




# This function implements the request receiving and response sending for get page data
@csrf_exempt
def get_page_data_view(request):
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    if request.method == 'POST':
        role = request.user.is_superuser
        if not role:
            user_role = User.objects.get(id= request.user.id)
            user_group = Group.objects.get(user=user_role)
            role_id = user_group.id
        else:
            role_id = 0
        # If the user has not logged in
        if not role and not role_id:
            code = 2031
            title = 'Sorry, you have to login to perform this action'
            message = 'Sorry, you have to login to perform this action'
            data = {}
            response_object = construct_response(code, title, message, data)
            response_text = json.dumps(response_object,ensure_ascii=False)
            return HttpResponse(response_text,content_type='application/json')
        # If the user has logged in, process the request
        else:
            body_unicode = request.body.decode('utf-8')
            data = json.loads(body_unicode)
            start_timestamp = data.get('startTimestamp', 0)
            end_timestamp = data.get('endTimestamp', 0)
            topic_id = data.get('contentId', '').strip()
            parent_level = data.get('parentLevel', -1)
            parent_id = int(data.get('parentId', '').strip())
            channel_id = data.get('channelId', '').strip()
            # response_object= get_page_data(parent_id, parent_level, topic_id, end_timestamp, start_timestamp, channel_id, request.user.id, role_id)
            # 
            # print(response_text)
            response_object = construct_response(0, "", "", {})
            response_text = json.dumps(response_object,ensure_ascii=False)
            return HttpResponse(response_text, content_type='application/json')

    else:
        return HttpResponse()

#@login_required
@csrf_exempt
def get_topics(request):
    # print(str(request.get_full_path()))
    if request.method == 'POST':
        topics = Content.objects.filter(topic_id='').first()
        obj = json.loads(topics.sub_topics)
        response = construct_response(0, '', '', obj);
        response_text = json.dumps(response,ensure_ascii=False)
        return HttpResponse(response_text,content_type='application/json')
    else:
        response = construct_response(1111,'wrong request','wrong request','')
        response_text = json.dumps(response,ensure_ascii=False)
        return HttpResponse(response_text,content_type='application/json')

#@login_required
@csrf_exempt
def get_trend(request):
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        params = json.loads(body_unicode)
        start_timestamp = params.get('startTimestamp','')
        start = datetime.datetime.fromtimestamp(start_timestamp)
        end_timestamp = params.get('endTimestamp', '')
        end = datetime.datetime.fromtimestamp(end_timestamp)
        topic_id = params.get('contentId')
        channel_id = params.get('channelId')
        level =params.get('level')
        item_id = params.get('itemId')
        data = None
        content = None
        if topic_id=="-1":
            content = Content.objects.filter(topic_id='').first()
        else:
            content = Content.objects.filter(topic_id=topic_id,channel_id=channel_id).first()
        total_questions = content.total_questions
        # print(total_questions)
        total_students = 1.0
        if level == -1 or level == 0:
            pass
        elif level == 1:
            school = UserInfoSchool.objects.filter(school_id=item_id).first()
            total_students = school.total_students
            if topic_id == "-1":
                '''data = MasteryLevelSchool.objects.filter(school_id=item_id).filter(date__gt=start).filter(date__lt=end).values('channel_id')\
                .annotate(Sum('completed_questions'),Sum('correct_questions'),Sum('attempt_questions'),Sum('students_completed')).order_by('date')
                print(data)'''
                data = MasteryLevelSchool.objects.filter(school_id=item_id,content_id="",date__gte=start,date__lte=end).order_by('date')
            else:
                data = MasteryLevelSchool.objects.filter(school_id=item_id,content_id=topic_id, channel_id=channel_id,\
                    date__gte=start,date__lte=end).order_by('date')
                # print(data)
        elif level == 2:
            classroom = UserInfoClass.objects.filter(class_id=item_id).first()
            total_students = classroom.total_students
            if topic_id == "-1":
                data = MasteryLevelClass.objects.filter(class_id=item_id,content_id="",date__gte=start,date__lte=end).order_by('date')
            else:
                data = MasteryLevelClass.objects.filter(class_id=item_id, content_id=topic_id, channel_id=channel_id,\
                    date__gte=start,date__lte=end).order_by('date')
        elif level == 3:
            if topic_id == "-1":
                data = MasteryLevelStudent.objects.filter(student_id=item_id,content_id="",date__gte=start,date__lte=end).order_by('date')
            else:
                data = MasteryLevelStudent.objects.filter(student_id=item_id, content_id=topic_id, channel_id=channel_id,\
                    date__gte=start,date__lte=end).order_by('date')
        res = {}
        series = []
        series.append({'name':'% exercise completed','isPercentage':True})
        series.append({'name':'% exercise correct','isPercentage':True})
        series.append({'name':'# attempts','isPercentage':False})
        series.append({'name':'% students completed topic','isPercentage':True})
        points = []
        completed_questions_sum = 0
        correct_questions_sum = 0
        attempt_questions_sum = 0
        completed_sum = 0
        for ele in data:
            temp = []
            '''if topic_id=="-1":
                completed_questions_sum += ele['completed_questions__sum']
                correct_questions_sum += ele['correct_questions__sum']
                attempt_questions_sum += ele['attempt_questions__sum']
                temp.append(time.mktime(ele['date'].timetuple()))
                temp.append(100.0*completed_questions_sum/(total_students*total_questions))
                temp.append(100.0*correct_questions_sum/(total_students*total_questions))
                temp.append(attempt_questions_sum)
                if level == 3:
                    completed_sum += ele['completed__sum']
                else:
                    completed_sum += ele['students_completed__sum']
                temp.append(100.0*completed_sum/total_students)
            else:'''
            completed_questions_sum += ele.completed_questions
            correct_questions_sum += ele.correct_questions
            attempt_questions_sum += ele.attempt_questions
            temp.append(time.mktime(ele.date.timetuple()))
            temp.append(100.0*completed_questions_sum/(total_students*total_questions))
            temp.append(100.0*correct_questions_sum/(total_students*total_questions))
            temp.append(attempt_questions_sum)
            if level == 3:
                completed_sum += ele.completed
                temp.append(completed_sum)
            else:
                completed_sum += ele.students_completed
                temp.append(completed_sum)
            points.append(temp)
        res['series'] = series
        res['points'] = points
        #data_str = serializers.serialize('json', data)
        response = construct_response(0,'','',res)
        response_text = json.dumps(response,ensure_ascii=False)
        return HttpResponse(response_text,content_type='application/json')
    else:
        response = construct_response(1111,'wrong request','wrong request','')
        response_text = json.dumps(response,ensure_ascii=False)
        return HttpResponse(response_text,content_type='application/json')

@csrf_exempt
def get_report_mastery(request):
    userinfo = {}
    if request.method == 'GET': 
        # role = request.user.is_superuser
        # if not role:
        #     user_role = User.objects.get(id= request.user.id)
        #     user_group = Group.objects.get(user=user_role)
        #     role_id = user_group.id
        # else:
        #     role_id = 0
        # if role_id == 3:
        #     user_class_institute = UserRoleCollectionMapping.objects.get(user_id_id = request.user.id)
        #     parent_id = user_class_institute.institute_id_id
        #     userinfo['parent_id'] = str(parent_id)
        #     userinfo['parent_level'] = "1"
        # else:
        #     userinfo['parent_id'] = "-1"
        #     userinfo['parent_level'] = "0"
        # data = json.dumps(userinfo)
        return render(request,'report-mastery.html')
    else:
        return HttpResponse()

