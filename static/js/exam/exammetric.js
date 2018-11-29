"use strict";

// globals

var startTimestamp = 1496948693; // default: from server
var endTimestamp = 1596948693; // default: from server
var parentLevel = 0; // default: parent-of-root-level
var parentId = '-1'; // default: none (at root level already, no parent)
var pendingRequests = 0; // number of requests that are sent but not received yet
var debug = true; // whether to print debug outputs to console
var selfServe = false;
var userID = '' // User ID
var dataTable = null;
var aggregationTable = null;
/** Pragma Mark - Starting Points **/
var length_exam = [[30,60,90,120],[30,60,90,120]]
// Update page (incl. new breadcrumb and all table/diagrams)
// Uses global variables `startTimestamp`, `endTimestamp`, `contentId`, `channelId`, `parentLevel`, and `parentId`
// Called every time the page needs update
var updatePageContent = function() {

    // Making sure `setTableData` happens AFTER `setTableMeta`
   $(document).ready(function() {

        $('.totalquestions-breadcrumb').addClass('hidden');
        $('#t_button').addClass('hidden')
        $('.report-breadcrumb').removeClass('hidden');
    });
    var data1 = null;
    var data2 = null;
    sendPOSTRequest('/exam/api/exam/get-page-data', {
        startTimestamp: startTimestamp,
        endTimestamp: endTimestamp,
        userID : userID
    }, function(response) {
     setTableData(response.data,response.code);
    }
    );
};

// Fetch topics by calling API and update the dropdown menu
// Called only once upon page initialization
var refreshSchoolsDropdown = function() {
    sendPOSTRequest('/exam/exams/', {
        startTimestamp: startTimestamp,
        endTimestamp: endTimestamp,
        parentLevel: parentLevel,
        parentId: parentId
    }, function(response) {
        buildSchoolDropdown(response.data);
    });
};

var setupDateRangePicker = function() {
    $('.daterangepicker').daterangepicker({
        singleDatePicker: true,
        showDropdowns: true,
        startDate: new Date(startTimestamp * 1000),
        // endDate: new Date(endTimestamp * 1000)
    }, function(start, end, label) {
    startTimestamp = new Date(start.format('YYYY-MM-DD')).getTime() / 1000;
    // endTimestamp = new Date(end.format('YYYY-MM-DD')).getTime() / 1000;
    updatePageContent();
    });
};

var setupDateRangePickerEndDate = function() {
    $('.daterangepickerenddate').daterangepicker({
        singleDatePicker: true,
        showDropdowns: true,
        startDate: new Date(endTimestamp * 1000)
    },function(start, end, label) {
    endTimestamp = new Date(end.format('YYYY-MM-DD')).getTime() / 1000;
    updatePageContent();
    });
};

// Update loading info (on top of screen) according to current system status. Calling this method will either show it, change it, or hide it.
var updateLoadingInfo = function() {
    if (pendingRequests > 0) {
        setLoadingInfo('Crunching data, hang tight…');
        $('.prevents-interaction').removeClass('hidden');
    } else {
        setLoadingInfo(null);
        $('.prevents-interaction').addClass('hidden');
    }
};

/** Pragma Mark - Page Manipulation **/

// Set a specific loading message.
var setLoadingInfo = function(message) {
    if (message === null) {
        $('.loading-info-container').addClass('hidden');
        return;
    }

    $('.loading-info').html(message);
    $('.loading-info-container').removeClass('hidden');
};




// Initializes the schools dropdown according to given data
// Calls `_setSchools` recursively
// Called only once upon page initialization
var buildSchoolDropdown = function(data) {
    var content = [];
    _setSchools(content, data.schools);

    //wrap "everything"
    content = [{
        title: 'Everything',
        key: '-1,-1',
        folder: true,
        children: content,
        expanded: true
    }];

    var opts = {
        autoApply: true,            // Re-apply last filter if lazy data is loaded
        autoExpand: true,           // Expand all branches that contain matches while filtered
        counter: false,             // Show a badge with number of matching child nodes near parent icons
        fuzzy: false,               // Match single characters in order, e.g. 'fb' will match 'FooBar'
        hideExpandedCounter: true,  // Hide counter badge if parent is expanded
        hideExpanders: false,       // Hide expanders if all child nodes are hidden by filter
        highlight: true,            // Highlight matches by wrapping inside <mark> tags
        leavesOnly: false,          // Match end nodes only
        nodata: false,              // Display a 'no data' status node if result is empty
        mode: 'hide'                // Grayout unmatched nodes (pass "hide" to remove unmatched node instead)
    };

    $('#schools-tree').html('');
    $('#schools-tree').fancytree({
        // checkbox: true,
        // selectMode: 3,
        extensions: ['filter'],
        quicksearch: true,
        source: content,
        filter: opts
    });

    // filter field
    $('#school-filter-field').keyup(function(e) {
        var n; // number of results
        var tree = $.ui.fancytree.getTree();
        var filterFunc = tree.filterBranches;
        var match = $(this).val();

        if (e && e.which === $.ui.keyCode.ESCAPE || $.trim(match) === ''){
            // reset search
            $('#school-filter-field').val('');
            var tree = $.ui.fancytree.getTree();
            tree.clearFilter();
            return;
        }

        n = filterFunc.call(tree, match, opts);
    });

    // automatic reset
    $('#reset-search').click(function(e){
        $('#school-filter-field').val('');
        var tree = $.ui.fancytree.getTree();
        tree.clearFilter();
    });

    // click background to dismiss
    $('html').click(function() {
        closeSchoolDropdown();
    });

    $('#school-dropdown-container').click(function(e) {
        e.stopPropagation();
    });

    $('.school .toggle-button').click(function(e) {
        toggleSchoolDropdown();
        e.stopPropagation();
    });
};

var switchView = function(viewId) {
    $('.switch-view-button').removeClass('btn-primary current');
    $('.switch-view-button').addClass('btn-default');
    $('.switch-view-button-' + viewId).removeClass('btn-default');
    $('.switch-view-button-' + viewId).addClass('btn-primary current');

    $('.report-view').addClass('hidden');
    $('.report-view-' + viewId).removeClass('hidden');
};

// Toggle topics dropdown menu
// UIAction
var toggleSchoolDropdown = function() {
    $('#school-dropdown-container').toggleClass('shown');
};

// UIAction
var closeSchoolDropdown = function() {
    $('#school-dropdown-container').removeClass('shown');
};

// UIAction
var toggleSchoolDropdownExpandAll = function() {
    var $button = $('#school-dropdown-container .expand-button');
    if ($button.data('expand')) {
        $button.data('expand', false);
        $button.html('Collapse All');
        $('#schools-tree').fancytree('getTree').visit(function(node) {
            node.setExpanded();
        });
    } else {
        $button.data('expand', true);
        $button.html('Expand All');
        $('#schools-tree').fancytree('getTree').visit(function(node) {
            if (node.title !== 'Everything') {
                node.setExpanded(false); // collapse all except the root node (which there will be only 1)
            }
        });
    }
};
// Apply currently selected topic, dismiss the dropdown, and update the page (async)
// UIAction
var applyAndDismissSchoolDropdown = function() {

    var node = $('#schools-tree').fancytree('getTree').getActiveNode();
    if (node !== null && node.children == null) {
        var userId = node.key;// update global state
        userID = userId;
        $('.school-dropdown-text').html(node.title);
        updatePageContent();
    } else {
        // a node is not selected
        toastr.warning('You must select a student to apply the filter. Here filter is only student not the class/or schools');
    }
    toggleSchoolDropdown();
};

// Instantiate both tables, insert rows with data partially populated
// Called every time the page needs update
var metaSetOnce = false;
var setTableData = function(examData, code) {
    if (code == 2001){
        if (dataTable != null){
            dataTable.destroy();
            $('#data-table').html('');
        }
        dataTable = $('#data-table').DataTable({
            // "pageLength":30;
            columns: [
            {
                'name': 'first',
                'title': 'Student Name',
            },
            {
                'name':'second',
                'title':'Correct Questions'
            },
            {
                'name':'third',
                'title':'% Correct Questions'
            },
            ],
            lengthMenu:length_exam,
        });
    }
    else{
        try{

            var data = examData['rows']
            var column = examData['columns']

            if (dataTable != null){
                dataTable.destroy();
                $('#data-table').html('');
            }
            dataTable = $('#data-table').DataTable({
            lengthMenu:length_exam,
            columns: column,
            data: data,
            });
            headerData(examData);
            aggregation_table(examData)
        }
        catch(err){
            console.log(err.stack);
        }
    }
}

var aggregation_table= function(data){
if (aggregationTable != null){
    aggregationTable.destroy();
    
}
aggregationTable = $('#aggregation-table').DataTable({
            paging: false,
            bFilter: false
    });
aggregationTable.clear();
var idx
for (idx in data.average) {
        var array = data.average[idx].values;
        array.unshift(data.average[idx].name);
        array.push('');
        aggregationTable.row.add(array).draw(false);
    }
}

var headerData = function(data){
        var headers = data['header']
        var te = headers['question_count']
        var topic_data = data['topic']
        var topic_detail = data['details']
        $('#t_button').removeClass('hidden');
        showexamcount(te);
        showtopic(topic_data,topic_detail)

};
var showexamcount = function(eCount,tc){
    if (eCount != null)
    {
    $('.totalquestions-breadcrumb').removeClass('hidden')
    $('.report-breadcrumb').addClass('hidden')
    $('#totalExams').text( eCount.toString());
   
    } else {

         $('.totalquestions-breadcrumb').addClass('hidden')
         $('.report-breadcrumb').removeClass('hidden')
     }
};
var showtopic = function(data,detail){
   
   $('#t_button').click( function fun() { 
    $(".modal-body").html("");
    var len = data.length
    for (var i=0; i < len; i++)
    {
        var tooltip = $("<div data-toggle='tooltip'  title='"+detail[i]+"'>"+(i+1)+")"+data[i]+"</div>")
        $('#topic').append(tooltip);
        $(document).on('mousemove', function(e) {
            $('.tooltip').css({
             left: e.pageX + 30,
             top: e.pageY - 10,
            });
            });
        }
    });
    $('#close').click( function fun() {
        for(var i =0; i<data.length; i++){
        $('#topic').children("div").remove();
        }
    });

}

// Handle click event of a breadcrumb link
// UIAction
var clickBreadcrumbLink = function(level, id, channelid) {
    contentID = id;
    channelID = channelid;
    parentLevel = level;
    objpreviouscontentlID.length = level + 1;
    objpreviouschannelID.length = level + 1;
    // parentLevel--;
    updatePageContent();
};

var appendBreadcrumbItem = function(name, level, id, channelid, isLast) {
    var html;
    if (isLast) {
        html = '<span class="breadcrumb-text">' + name + '</span>';
    } else {
        html = '<a class="breadcrumb-link" href="#" onclick="clickBreadcrumbLink(' + level + ', \'' + id + '\', \'' +channelid+ '\')">' + name + '</a>';
        if (!isLast) {
            html += ' > ';
        }
    }

    $('.report-breadcrumb').append(html);
};
// Recursively build the topics structure. See `buildTopicsDropdown`.
var _setSchools = function(toArray, dataArray) {
    var idx;
    var flag = false;
    for (idx in dataArray) {
        var dict = dataArray[idx];
        if (dict.children){
            flag = true;
            var newDict = {
                title: dict.name,
                key: dict.id,
                folder: flag
            };
        }
        else{
            var newDict = {
                title: dict.name,
                key: dict.id,
                folder: flag
            };
        }
        if (dict.children !== null) {
            newDict['children'] = [];
            _setSchools(newDict['children'], dict.children);
        }
        toArray.push(newDict);
    }
};

var sendPOSTRequest = function(url, dataObject, callback) {
    if (selfServe) {
        sendPOSTRequest_test(url, dataObject, callback);
    } else {
        sendPOSTRequest_real(url, dataObject, callback);
    }
};

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
    }
// Sends a POST request. Both request and return data are JSON object (non-stringified!!1!)
// `callback` called when a response is received, with the actual response as the parameter.
var sendPOSTRequest_real = function(url, dataObject, callback) {
    pendingRequests++;
    updateLoadingInfo();

    if (debug) {
        console.log('POST request sent to: ' + JSON.stringify(url) + '. POST data: ' + JSON.stringify(dataObject));
    }

    var csrftoken = getCookie('csrftoken');
    $.ajax({
        type: 'POST',
        url: url,
        data: JSON.stringify(dataObject),
        headers: {'X-CSRFToken': csrftoken },
        dataType: 'json',
        success: function(response, textStatus, jqXHR) {
            if (debug) {
                console.log('Response (From `' + url + '`): ' + JSON.stringify(response));
            }
            if (!response.data) {
                toastr.error('There is an error communicating with the server. Please try again later.');
                console.error('Invalid response: A valid `data` field is not found.');
            } else {
                callback(response);
            }
            pendingRequests--;
            updateLoadingInfo();
        },
        error: function(jqXHR, textStatus, errorThrown) {
            if (!textStatus) {
                textStatus = 'error';
            }
            if (!errorThrown) {
                errorThrown = 'Unknown error';
            }
            if (debug) {
                console.log('Request (from `' + url + '`) failed with status: ' + textStatus + '. Error Thrown: ' + errorThrown);
            }
            toastr.error('Request (from `' + url + '`) failed: ' + textStatus + ': ' + errorThrown, 'Connection Error');
            pendingRequests--;
            updateLoadingInfo();
        }
    });
};

$(function() {
    google.charts.load('current', {'packages':['line', 'corechart']});
    setupDateRangePicker();
    setupDateRangePickerEndDate();
    refreshSchoolsDropdown();
    updatePageContent();
});
