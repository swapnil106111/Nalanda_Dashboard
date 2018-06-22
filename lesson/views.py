from django.shortcuts import render, HttpResponse
from .lessonmastery import LessonDetails
import json
# Create your views here.
from account.views import construct_response

def get_lessons(request):
	if request.method == 'POST':
		user = request.user
		body_unicode = request.body.decode('utf-8')
		data = json.loads(body_unicode)
		print ("Data:", data)
		parent_level = data.get('parentLevel', -2)
		objSchoolDetails = LessonDetails(user, parent_level)
		objSchoolData = objSchoolDetails.getPageData()
		print ("objSchoolData:", objSchoolData)
		response = construct_response(0, '', '', objSchoolData);
		response_text = json.dumps(response,ensure_ascii=False)
		return HttpResponse(response_text,content_type='application/json')
	else:
		response = construct_response(1111,'wrong request','wrong request','')
		response_text = json.dumps(response,ensure_ascii=False)
		return HttpResponse(response_text,content_type='application/json')


def get_lesson_mastery(request):
	if request.method == 'GET':
		# lesson_details = LessonDetails()
		return render(request,'lessonmasteryreport.html',{})
	else:
		return HttpResponse()