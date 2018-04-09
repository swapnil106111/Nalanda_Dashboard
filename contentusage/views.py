from django.shortcuts import render, HttpResponse
from account.views import construct_response
from account.models import UserInfoClass, UserInfoSchool, UserInfoStudent
import json 
from .contentusagereport import ContentUsageMeta, ContentUsageData, SchoolDetails, TrendDetails
from contentusage.constants import *

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
		user = request.user
		body_unicode = request.body.decode('utf-8')
		data = json.loads(body_unicode)
		parent_level = data.get('parentLevel', -2)
		objSchoolDetails = SchoolDetails(user, parent_level)
		objSchoolData = objSchoolDetails.getPageData()
		response = construct_response(0, '', '', objSchoolData);
		response_text = json.dumps(response,ensure_ascii=False)
		return HttpResponse(response_text,content_type='application/json')
	else:
		response = construct_response(1111,'wrong request','wrong request','')
		response_text = json.dumps(response,ensure_ascii=False)
		return HttpResponse(response_text,content_type='application/json')

def get_contentusage_page_meta(request):
	user = request.user
	body_unicode = request.body.decode('utf-8')
	data = json.loads(body_unicode)
	parent_level = data.get('parentLevel', -2)
	content_id = data.get('contentId','')
	channel_id = data.get('channelId','')
	previouscontent_id = data.get('previousContentID','')
	previouschannel_id = data.get('previousChannelID','')
	objContentUsage= ContentUsageMeta(user, parent_level, content_id, channel_id, previouscontent_id, previouschannel_id)
	objContentUsageData = objContentUsage.pageMeta(METRICS)
	response_text = json.dumps(objContentUsageData,ensure_ascii=False)
	return HttpResponse(response_text,content_type='application/json')

def get_contentusage_page_data(request):
	user = request.user
	body_unicode = request.body.decode('utf-8')
	data = json.loads(body_unicode)
	startTimestamp = data.get('startTimestamp', 0)
	endTimestamp = data.get('endTimestamp', 0)
	topicID = data.get('contentId', '')
	parentLevel = data.get('parentLevel', '')
	parentID = int(data.get('parentId', '').strip())
	channelID = data.get('channelId', '')
	filtercriteriaflag = data.get('std', '')
	filetrcontetusage = data.get('filetrcontetusage','')
	current_time = data.get('current','')
	objContentUsage = ContentUsageData(user, parentLevel, topicID, channelID, startTimestamp, endTimestamp, filtercriteriaflag, filetrcontetusage, current_time)
	objContentUsageData = objContentUsage.pageData()
	response_object = construct_response(0, "", "", objContentUsageData)
	response_text = json.dumps(response_object,ensure_ascii=False)
	return HttpResponse(response_text, content_type='application/json')

def get_trend_data(request):
	if request.method == 'POST':
		user = request.user
		body_unicode = request.body.decode('utf-8')
		params = json.loads(body_unicode)
		# print ("Data:", params)
		start_timestamp = params.get('startTimestamp','')
		# start = datetime.datetime.fromtimestamp(start_timestamp)
		end_timestamp = params.get('endTimestamp', '')
		# end = datetime.datetime.fromtimestamp(end_timestamp)
		topic_id = params.get('contentId')
		channel_id = params.get('channelId')
		level = params.get('level')
		item_id = params.get('itemId')
		item_channel_id = params.get('itemChannelId')
		std = params.get('std')
		filetr_contetusage = params.get('filetrcontetusage')
		objTrendDetails = TrendDetails(user, start_timestamp, end_timestamp,level,item_id,item_channel_id, std, topic_id, channel_id, filetr_contetusage)
		res = objTrendDetails.get_trend()
		response = construct_response(0,'','',res)
		response_text = json.dumps(response,ensure_ascii=False)
	else:
		response = construct_response(1111,'wrong request','wrong request','')
		response_text = json.dumps(response,ensure_ascii=False)
	return HttpResponse(response_text,content_type='application/json')

def get_contentusage(request):
    if request.method == 'GET':
        return render(request,'contentusagereport.html', {})
    else:
    	return HttpResponse()