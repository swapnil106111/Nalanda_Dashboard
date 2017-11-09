from django.shortcuts import render, HttpResponse, redirect, get_object_or_404, render_to_response
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
from itertools import groupby
from operator import itemgetter
import collections
from account.forms import Forget_Password

from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login
from axes.decorators import watch_login
from axes.utils import reset
from django.contrib.auth.forms import AuthenticationForm
from django.views.generic import UpdateView
from .forms import UserProfileForm
from axes.models import AccessAttempt
from .usermastery import UserMasteryMeta, UserMasteryData
from account.constants import MESSAGE, SUBJECT, REGISTEREMAIl, USERACTIVEMAIL
from django.conf import settings
from django.template import Context
from django.template.loader import render_to_string, get_template
from django.core.mail import EmailMessage

from django.core.validators import validate_email

# This function contructs the dict for every response
# code = 0 represents that the processing is sucessful
def construct_response(code, title, message, data):
    response_object = {}
    response_object["code"] = code
    response_object["info"] = {"title": title,"message": message}
    response_object["data"] = data
    return response_object

@watch_login
def login_view(request):
    """ 
    This function implements the request receiving and response sending for login
    """
    response_object ={}
    form = AuthenticationForm(None, request.POST)
    #If POST request is received, render the mastery page
    if request.method == 'POST':
    	if form.is_valid():
            # user = User.objects.get(is_superuser = True)
            # if user == form.get_user():
            if form.get_user().is_superuser:
                return redirect('/account/admin-users')
            else:
                login(request, form.get_user())
                response = redirect(reverse('get_report_mastery'))
                return response
    	else:
            data = form.errors.as_json()
            error_data = json.loads(data)
            for msg in error_data:
                message = error_data[msg][0]['message']
                response_object = construct_response(1001, "",message, {})
    #If GET request is received, render the login page
    response_object['form']=form
    return render(request, 'login.html', response_object)


def register_view(request):
    """
        This function implements the request receiving and response sending for register  
    """
    domain = request.get_host()
    # print ("Domain:", domain)
    # print ("Fullpath:",request.META['HTTP_REFERER'])
    data = get_school_and_classes()
    # If GET request is received, render the register page, return the school and class info
    if request.method == 'GET':
    	response_str = {}
    	form = UserProfileForm(None, request.POST)
    	code = 1000
    	title = ''
    	message = ''
    	response_object = construct_response(code, title, message, data)
    	response_text = json.dumps(response_object,ensure_ascii=False)
    	response_str = json.loads(response_text)
    	response_str['form'] = form
    	return render(request, 'register.html', response_str)

    # If POST request is received, process the request and return JSON object
    elif request.method == 'POST':
        try:
            validate_email(request.POST.get("email"))
        except:
            response = construct_response(0,"","Enter a valid e-mail address.", data)
            form = UserProfileForm()
            response['form'] = form
            return render(request,'register.html', response)
        # print ("Email:", )
        classes = request.POST.getlist('classes')
        form = UserProfileForm(request.POST)
        response = {}
        if form.is_valid():
            institutes =  form.cleaned_data['institutes']

            if not institutes and form.cleaned_data['role'].id == 2:
                institutes = None
                response = construct_response(0,"","User need to select atleast one institute", data)
                form = UserProfileForm()
                response['form'] = form
                return render(request,'register.html', response)

            if form.cleaned_data['role'].id == 3 and len(classes) == 0:
                response = construct_response(0,"","User need to select atleast one class",data)
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
  
            sendEmail(user, REGISTEREMAIl, SUBJECT[1], domain)
            response = construct_response(1006,"User Save","You are succesfully registered to Nalanda's Dashboard. Please check your email account.", data)
            form = UserProfileForm()
            response['form'] = form
            return render(request,'register.html', response)
        #If POST request is receieved and get an any error. Erroer will display on the registration page
        else:
            errorDetails = form.errors.as_json()
            errorData = json.loads(errorDetails)
            for k,v in errorData.items():
                message = errorData[k][0]['message']
                # message= str(msg)+" "+ message[4:] 
                response_text ={}
                response_text = construct_response(0,"",message,data)
                form = UserProfileForm()
                response_text['form'] = form
                return render(request, 'register.html', response_text)

def sendEmail(user, template, subject, domain):
    try:
        ctx = {
                "user":user,
                "url":"http://"+domain+"/account/login/"
            }
        message = get_template(template).render(ctx)

        msg = EmailMessage(subject, message, to=[user.email], from_email=settings.EMAIL_HOST_USER)
        msg.content_subtype = 'html'
        msg.send()
    except Exception as e:
        print (e)

def get_school_and_classes():
    """
        This function gets all schools and classes in the database
    Args:
        None
    Returns:
        school_info(dict) = It contains schoolinfo and it's associated classes information
    """
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

# @login_required(login_url='/account/login/')
# @user_passes_test(lambda u: u.is_superuser)
def admin_get_view(request):
    """
        This function implements the request receiving and response sending for admin get the users
    """

    if request.method == 'GET':
        # pendingUser = True
        blockedUsers = {}
        pendings = User.objects.filter(is_superuser = False).order_by('-id')
        # blocked =  AccessAttempt.objects.filter(failures_since_start__gte=3)
        pendingUsers = list(map(lambda p: getPendingUserDetails(p), pendings))
        # print ("Users:", pendingUsers)
        pendingUsers = sum(pendingUsers, [])
        # print ("Users:", pendingUsers)

        for user in pendingUsers:
            if user['isActive']:
                user['isActive'] = 1
            else:
                user['isActive'] = 0
        # blockedUsers = list(map(lambda p: getPendingUserDetails(p, False), blocked))
        # blockedUsers = sum(blockedUsers, [])
        objPendingUsers = getMultipleClassCombine(pendingUsers)
       
        data = {'pendingUsers': objPendingUsers }
        response_object = construct_response(0, "", "", data)
        if len(objPendingUsers) == 0:
            response_object = construct_response(2001, "user list empty", "All users are approved by admin and doesn't have ublocked users", {})
        return render(request, 'admin-users.html', response_object)

def getMultipleClassCombine(userList):
    """
        This function is used to combine the multiple classes of user combined as comma seprated string 
    Args:
        userList(List): It contains the user list
    Returns:
        result(List): updared user teacher classes combined as comma separated string 
    """
    result = []
    key_data=itemgetter('userid')
    sorted_data=sorted(userList, key= key_data)

    for key, grp in groupby(sorted_data , key_data):
        temp_dict={}
        cl_st=""
        for data in grp:
            for k,v in data.items():
                if str(k)=='className':
                    cl_st += ', ' + v
                else:
                    temp_dict[k]=v
            temp_dict['className']=cl_st[1:]
        result.append(temp_dict)
    return result

def getPendingUserDetails(user):
    """
        This function is used to get the user details
    Args:
        user(object): passed individual user as input
    Returns:
        pending_users(List): It returns the user details
    """
    instituteName = ''
    instituteID = -1
    classID = -1
    className = ''
    pending_users = []

    role = user.groups.values()[0]['name']
    roleID = user.groups.values()[0]['id']
    
    if roleID != 1:
        objUserMapping = UserRoleCollectionMapping.objects.filter(user_id = user)

        if objUserMapping:
            for usermapped in objUserMapping:
                # print ("usermapped:", type(usermapped))
                instituteName = usermapped.institute_id.school_name
                instituteID = usermapped.institute_id.school_id
                if roleID == 3:
                    classID = usermapped.class_id.class_id
                    className = usermapped.class_id.class_name
                pending_user = collections.OrderedDict()
                pending_user = {'userid':user.id, 'username': user.username, 'email': user.email, 'role': role, 'instituteName': instituteName, 'className': className, 'isActive':user.is_active}
                pending_users.append(pending_user)
        else:
            raise Exception("User is not belongs to any class")
    else:
        pending_user = collections.OrderedDict()
        pending_user = {'userid':user.id, 'username': user.username, 'email': user.email, 'role': role, 'instituteName': instituteName, 'className': className, 'isActive':user.is_active}
        pending_users.append(pending_user)
    return pending_users
 
@login_required(login_url='/account/login/')
def logout_view(request):
    """
        This function implements the request receiving and response sending for logout
    """
    # If GET request is received, render the index page
    if request.method == 'GET':
        try:
            logout(request)
            return redirect('/account/login/')
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

# @login_required(login_url='/account/login/')
# @user_passes_test(lambda u: u.is_superuser)
def admin_approve_pending_users_view(request):
    """
        This function implements the request receiving and response sending for admin approve users
    """
    domain = request.get_host()
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        users = data.get('users',[])
        response_object = admin_approve_pending_users_post(users, domain)

        response_text = json.dumps(response_object,ensure_ascii=False)
        return HttpResponse(response_text)
    else:
        return HttpResponse()

def admin_approve_pending_users_post(users, domain):
    """
        This function implements the logic for admin active the users
    """
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
                    sendEmail(result[0], USERACTIVEMAIL, SUBJECT[2], domain)
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

def admin_disapprove_pending_users_post(users):
    """
       This function implements the logic for admin inactive users 
    """
    code = 0
    title = ''
    message = ''
    data = {}
    try:
        if users:
            # If the users to be disapproved is not empty
            for i in range(len(users)):
                username = users[i]['username']
                result = User.objects.get(username=username)
                if result:
                    result.is_active = False
                    result.save()
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

# @login_required(login_url='/account/login/')
# @user_passes_test(lambda u: u.is_superuser)
def admin_disapprove_pending_users_view(request):
    """
        This function implements the request receiving and response sending for admin inactive users
    """
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        users = data.get('users',[])
        response_object = admin_disapprove_pending_users_post(users)
        response_text = json.dumps(response_object,ensure_ascii=False)
        return HttpResponse(response_text)

    # @login_required(login_url='/account/login/')
    # @user_passes_test(lambda u: u.is_superuser)
def deleteUser(request):
    """ 
        This function is used to delete the the user
    """
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        users = data.get('users',[])
        deleteSuccess = True
        try:
            if users:
                for i in range(len(users)):
                    username = users[i]['username']
                    result = User.objects.get(username=username)
                    if result:
                        result.delete()

            response_object = construct_response("3001", "User Delete", "User Deleted successfully", {})
            response_text = json.dumps(response_object, ensure_ascii=False)
            return HttpResponse(response_text)
        except Exception as e:
            print (e)

@login_required(login_url='/account/login/')
def get_page_meta_view(request):
    """
    This function implements the request receiving and response sending for get page meta details
    """   
    user = request.user
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    parent_level = data.get('parentLevel', -2)
    parent_id = int(data.get('parentId', '').strip())
    objUserMastery = UserMasteryMeta(user, parent_id, parent_level)
    objUserData = objUserMastery.getPageMeta()
    response_text = json.dumps(objUserData,ensure_ascii=False)
    return HttpResponse(response_text,content_type='application/json')

@login_required(login_url='/account/login/')
def get_page_data_view(request):
    """
    This function implements the request receiving and response sending for get page data

    """
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

@login_required(login_url='/account/login/')
def get_topics(request):
    """
        This function is used to get the channel details 
    """
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

@login_required(login_url='/account/login/')
def get_trend(request):
    """
    This function is used to show the mastery data in a graphical format
    """
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

@login_required(login_url='/account/login/')
def get_report_mastery(request):
    if request.method == 'GET': 
        return render(request,'report-mastery.html')
    else:
        return HttpResponse()

