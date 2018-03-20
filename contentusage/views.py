from django.shortcuts import render, HttpResponse
from account.views import construct_response
from account.models import UserInfoClass, UserInfoSchool, UserInfoStudent
import json 
# Create your views here.

def get_schools(request):
    """
    This function gets all schools and classes in the database
    Args:
        None
    Returns:
        school_info(dict) = It contains schoolinfo and it's associated classes and student info
    """
    if request.method == 'POST':
        totalschools = {}
        school_list = []
        schools = UserInfoSchool.objects.all()
        def convert_to_string(data):
            data['id'] = str(data['id'])
            return data
        # Get all the schools, if schools exist
        for school in schools:
            school_info = {}
            classes_in_school = list(UserInfoClass.objects.filter(parent=school.school_id).extra(select={'id':'class_id','name':'class_name'}).values('id','name'))
            for classid in classes_in_school:
                students_in_class = list(UserInfoStudent.objects.filter(parent=classid['id']).extra(select={'id':'student_id','name':'student_name'}).values('id','name'))
                classid['children'] = students_in_class
            school_info['id'] = str(school.school_id)
            school_info['name'] = school.school_name
            school_info['children'] = list(map(convert_to_string, classes_in_school))
            school_list.append(school_info)
        totalschools["schools"] = school_list
        response = construct_response(0, '', '', totalschools);
        response_text = json.dumps(response,ensure_ascii=False)
        return HttpResponse(response_text,content_type='application/json')
    else:
        response = construct_response(1111,'wrong request','wrong request','')
        response_text = json.dumps(response,ensure_ascii=False)
        return HttpResponse(response_text,content_type='application/json')

def get_contentusage(request):
    if request.method == 'GET':
        return render(request,'contentusagereport.html', {})
    else:
    	return HttpResponse()