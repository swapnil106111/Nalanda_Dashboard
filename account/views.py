from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.template import Context, loader
from django.core.exceptions import ObjectDoesNotExist
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

from .usermastery import UserMasteryMeta, UserMasteryData

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
            response = redirect(reverse('get_report_mastery'))
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
    data = get_school_and_classes()
    # If GET request is received, render the register page, return the school and class info
    if request.method == 'GET':
    	response_str = {}
    	form = UserProfileForm(None, request.POST)
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
        classes = request.POST.getlist('classes')
        form = UserProfileForm(request.POST)
        response = {}
        if form.is_valid():
            institutes =  form.cleaned_data['institutes']
            if not institutes:
                institutes = None
            if form.cleaned_data['role'].id == 3 and len(classes) == 0:
                response = construct_response(1002,"","User need to select atleast one class",data)
                form = UserProfileForm()
                response['form'] = form
                return render(request,'register.html', response)
            user = form.save()
            if classes:
                for curClass in classes:
                    try:
                        userInfoClass = UserInfoClass.objects.get(pk = int(curClass))
                    except UserInfoClass.DoesNotExist:
                        userInfoClass = None
                    up = UserRoleCollectionMapping.objects.create(class_id=userInfoClass, institute_id=form.cleaned_data['institutes'], user_id=user)
                    up.save()
            else:
                userInfoClass = None
                up = UserRoleCollectionMapping.objects.create(class_id=userInfoClass, institute_id=institutes, user_id=user)
                up.save()

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
        pendingUser = True
        blockedUsers = {}
        pendings = User.objects.filter(is_active = False)
        blocked =  AccessAttempt.objects.filter(failures_since_start__gte=3)
        pendingUsers = list(map(lambda p: getPendingUserDetails(p, pendingUser), pendings))
        pendingUsers = sum(pendingUsers, [])
        blockedUsers = list(map(lambda p: getPendingUserDetails(p, False), blocked))
        blockedUsers = sum(blockedUsers, [])
        data = {'pendingUsers': pendingUsers, 'blockedUsers': blockedUsers}
        response_object = construct_response(0, "", "", data)
        if not pendingUsers and not blockedUsers:
            response_object = construct_response(2001, "user list empty", "All users are approved by admin and doesn't have ublocked users", {})
        return render(request, 'admin-users.html', response_object)
    else:
        return HttpResponse()

def getPendingUserDetails(user, pendingUser):
    instituteName = ''
    instituteID = -1
    classID = -1
    className = ''
    pending_users = []

    if pendingUser:
        role = user.groups.values()[0]['name']
        roleID = user.groups.values()[0]['id']
    else:
        user =  User.objects.get(username = user.username)
        role = user.groups.values()[0]['name']
        roleID = user.groups.values()[0]['id']

    if roleID != 1:
        objUserMapping = UserRoleCollectionMapping.objects.filter(user_id = user)
        print ("")
        if objUserMapping:
            for usermapped in objUserMapping:
                print ("usermapped:", type(usermapped))
                instituteName = usermapped.institute_id.school_name
                instituteID = usermapped.institute_id.school_id
                if roleID == 3:
                    classID = usermapped.class_id.class_id
                    className = usermapped.class_id.class_name
                pending_user = {'username': user.username, 'email': user.email, 'role': role, 'instituteId': instituteID, 'instituteName': instituteName, 'classId': classID, 'className': className}
                pending_users.append(pending_user)
        else:
            raise Exception("User is not belongs to any class")
    else:
        pending_user = {'username': user.username, 'email': user.email, 'role': role, 'instituteId': instituteID, 'instituteName': instituteName, 'classId': classID, 'className': className}
        pending_users.append(pending_user)
    print ("Users:", pending_users)
    return pending_users

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
            return response
        except:
            code = 2021
            title = 'Sorry, error occurred at the server'
            message = 'Sorry, error occurred at the server'
            data = {}
            response_object = construct_response(code, title, message, data)
            response_text = json.dumps(response_object,ensure_ascii=False)
            return render(request, 'login.html', response_object)
    else:
        return HttpResponse()

# This function implements the request receiving and response sending for admin approve users
@csrf_exempt
def admin_approve_pending_users_view(request):
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        users = data.get('users',[])
        response_object = admin_approve_pending_users_post(users)

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
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        usernames = data.get('usernames',[])
        response_object = admin_unblock_users_post(usernames)
        # print(response_object)
        response_text = json.dumps(response_object,ensure_ascii=False)
        return HttpResponse(response_text)
    else:
        return HttpResponse()

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

# This function implements the request receiving and response sending for get page data
@csrf_exempt
def get_page_data_view(request):
    user = request.user
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    startTimestamp = data.get('startTimestamp', 0)
    endTimestamp = data.get('endTimestamp', 0)
    topicID = data.get('contentId', '').strip()
    parentLevel = data.get('parentLevel', -1)
    parentID = int(data.get('parentId', '').strip())
    channelID = data.get('channelId', '').strip()
    objUserMastery = UserMasteryData(user, parentID, parentLevel, topicID, channelID, startTimestamp, endTimestamp)
    objUserMasteryData = objUserMastery.getPageData()
    response_object = construct_response(0, "", "", objUserMasteryData)
    response_text = json.dumps(response_object,ensure_ascii=False)
    return HttpResponse(response_text, content_type='application/json')

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

@csrf_exempt
def get_trend(request):
    print ("Method:", request.method)
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
        print ("start_timestamp:", start)
        print ("end_timestamp:", end)
        print ("topicID:", topic_id)
        print ("channelId:", channel_id)
        print ("level:", level)
        print ("item_id", item_id)
        data = None
        content = None
        if topic_id == "-1":
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
    if request.method == 'GET': 
        return render(request,'report-mastery.html')
    else:
        return HttpResponse()

