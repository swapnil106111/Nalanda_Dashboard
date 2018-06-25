"use strict";

// globals
var table = null; // main data table
var aggregationTable = null; // aggregation rows table
var compareTable = null; // // datatables object
var performanceTable = null; // datatables object
var tableData; // see API specs
var tableMeta; // see API specs
var startTimestamp = 1496948693; // default: from server
var endTimestamp = 1596948693; // default: from server
var contentId = ['-1']; // default: everything
var channelId = ['-1']; // default: everything
var filetrcontetusage = []
var parentLevel = 0; // default: parent-of-root-level
var parentId = '-1'; // default: none (at root level already, no parent)
var compareMetricIndex = 0; // current metric index of the compare table
var performanceMetricIndex = 0; // current metric index of the performance table
var performanceCompareToValueName = 'average'; // name of the type of currently used compared values
var performanceCompareToValues = []; // compared values, for all types, of the performance table
var compareMaxValues = [];
var pendingRequests = 0; // number of requests that are sent but not received yet
var maxItemLevel = false; // students (read-only)
var debug = true; // whether to print debug outputs to console
var selfServe = false;
var count = 0;
var std = false;
// var maxval = false;
var setParenrtLevel = false;
var contentID = '-1';// Defined for content usage metrics
var channelID = '-1';
var objpreviouscontentlID= ['-1'];
var objpreviouschannelID = ['-1'];
var test = []; 
var level = 0;
var levelDict = {};
var count1 = [];
var count2 = [];

/** Pragma Mark - Starting Points **/

// Update page (incl. new breadcrumb and all table/diagrams)
// Uses global variables `startTimestamp`, `endTimestamp`, `contentId`, `channelId`, `parentLevel`, and `parentId`
// Called every time the page needs update
var updatePageContent = function() {
    
    // Making sure `setTableData` happens AFTER `setTableMeta` 
    
    var data1 = null;
    var data2 = null;
    
    sendPOSTRequest('/contentusage/api/contentusage/get-page-data', {
        startTimestamp: startTimestamp,
        endTimestamp: endTimestamp,
        contentId: contentID,
        channelId: channelID,
        filetrcontetusage:filetrcontetusage,
        std:std,
        parentLevel: parentLevel,
        parentId: parentId,
        current:current,
        level : level,
        levelDict : levelDict
    }, function(response) {
	    // data2 = response.data;
	    // checkTableDataConsistancy(data1, data2);
        // setTableData(response.data);
        // levelDict={};
        console.log("Data:"+ response.data)
        count1 = [];
        count2 = [];
    });
    dismissTrendChart();
};

// Fetch topics by calling API and update the dropdown menu
// Called only once upon page initialization
var refreshLessonsDropdown = function() {
    sendPOSTRequest('/lesson/api/lesson/lessons', {
        startTimestamp: startTimestamp,
        endTimestamp: endTimestamp,
        parentLevel: parentLevel,
        parentId: parentId
    }, function(response) {
        buildLessonsDropdown(response.data);
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

// Clears current breadcrumb and sets it to a new one according to given data.
// Uses `appendBreadcrumbItem`
// Called every time the page needs update
var setBreadcrumb = function(data) {
    $('.report-breadcrumb').html('');
    var len = data.breadcrumb.length;
    if (len == 1){
        parentLevel = data.breadcrumb[0].parentLevel 
    }

    // alert(parentLevel)
    var idx;
    for (idx in data.breadcrumb) {
        var o = data.breadcrumb[idx];
        var lastItem = idx == len - 1;
        appendBreadcrumbItem(o.parentName, o.parentLevel, o.parentId, o.channelId, lastItem);
        // contentID = o.parentId // Defined for content usage metrics
        // channelID = o.channelId
    }
};

// Initializes the schools dropdown according to given data
// Calls `_setSchools` recursively
// Called only once upon page initialization
var buildLessonsDropdown = function(data) {
    var content = [];
    _setSchools(content, data.schools);

    // wrap "everything"
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
    
    $('#topics-tree').html('');
    $('#topics-tree').fancytree({
        // checkbox: true,
        // selectMode: 3,
        extensions: ['filter'],
        quicksearch: true,
        source: content,
        filter: opts
    });
    
    // filter field
    $('#topic-filter-field').keyup(function(e) {
        var n; // number of results
        var tree = $.ui.fancytree.getTree();
        var filterFunc = tree.filterBranches;
        var match = $(this).val();

        if (e && e.which === $.ui.keyCode.ESCAPE || $.trim(match) === ''){
            // reset search
            $('#topic-filter-field').val('');
            var tree = $.ui.fancytree.getTree();
            tree.clearFilter();
            return;
        }

        n = filterFunc.call(tree, match, opts);
    });
    
    // automatic reset
    $('#reset-search').click(function(e){
        $('#topic-filter-field').val('');
        var tree = $.ui.fancytree.getTree();
        tree.clearFilter();
    });
    
    // click background to dismiss
    $('html').click(function() {
        closeTopicDropdown();
    });
    
    $('#topic-dropdown-container').click(function(e) {
        e.stopPropagation();
    });
    
    $('.topic .toggle-button').click(function(e) {
        toggleTopicDropdown();
        e.stopPropagation();
    });
};

// Instantiate both tables, insert rows with data partially populated
// Called every time the page needs update
var metaSetOnce = false;
var setDummyData = function() {
  var data = [
    ['Sagar','Exercise Mastered',  10, 15],
    ['Sagar','Questions  Attempts', 50, 90],
    ['Sagar', 'Questions Correct', 30, 70],
    ['Mahesh', 'Exercise Mastered', 20, 80],
    ['Mahesh', 'Questions  Attempts', 50, 70],
    ['Mahesh', 'Questions Correct', 40, 40],
  ];
  var table = $('#data-table').DataTable({
    columns: [
        {
            name: 'first',
            title: 'Student Name',
        },
        {
            name: 'second',
            title: 'Metrics',
        },
        {
            title: 'Addition',
        }, 
        {
            title: 'Substraction',
        },
    ],
    data: data,
    rowsGroup: [
      'first:name',
      'second:name'
    ],
    // pageLength: '20',
    });
}


var showTotalQuestions = function(qCount){
    var strQCount ;
    // var strExerciseCount;
    strQCount = qCount.toString();
    // strExerciseCount = eCount.toString();
    $('#totalQ').text(strQCount);
    // $('#totalExercise').text(strExerciseCount);
}




/** Pragma Mark - UIActions **/

// UIAction
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
var toggleTopicDropdown = function() {
    $('#topic-dropdown-container').toggleClass('shown');
};

// UIAction
var closeTopicDropdown = function() {
    $('#topic-dropdown-container').removeClass('shown');
};

// UIAction
var toggleTopicDropdownExpandAll = function() {
    var $button = $('#topic-dropdown-container .expand-button');
    if ($button.data('expand')) {
        $button.data('expand', false);
        $button.html('Collapse All');
        $('#topics-tree').fancytree('getTree').visit(function(node) {
            node.setExpanded();
        });
    } else {
        $button.data('expand', true);
        $button.html('Expand All');
        $('#topics-tree').fancytree('getTree').visit(function(node) {
            if (node.title !== 'Everything') {
                node.setExpanded(false); // collapse all except the root node (which there will be only 1)
            }
        });
    }
};

// Apply currently selected topic, dismiss the dropdown, and update the page (async)
// UIAction
var applyAndDismissTopicDropdown = function() {
    // var node = $('#topics-tree').fancytree('getTree').getActiveNode();
    var nodes = $('#topics-tree').fancytree('getTree').getSelectedNodes();
    filetrcontetusage = []
    test = []
    var count = 0
    var role = document.getElementById("userid").value;
    if (role != ""){
        role = parseInt(document.getElementById("userid").value);
    }
    // alert(role);
    // contentId =[];
    var node = 0;
    if (nodes.length != 0) {
        for(node in nodes){
            if(nodes[node].children == null && nodes[node].getLevel() == 4 && role != 3){
                var selectionIdentifiers = nodes[node].key; // update global state
                filetrcontetusage.push(selectionIdentifiers);
                std = true;
                level = nodes[0].getLevel()
            }
            else if (nodes[node].children == null && nodes[node].getLevel() == 3 && role == 3) {
                level = nodes[0].getLevel()
                std = true;
            }
            else if (nodes[node].children == null && nodes[node].getLevel() == 2 && role == 3) {
                level = nodes[0].getLevel()
                std = true;
            }
            else if(nodes[node].children.length > 0 && nodes[node].getLevel() == 3 && role != 3){
                level = nodes[0].getLevel()
            }
            else if(nodes[node].children.length > 0 && nodes[node].getLevel() == 2 && role != 3){
                level = nodes[0].getLevel()
            }
            
            getTotalCount(nodes[node]);
            if (nodes.length == 1){
                $('.topic-dropdown-text').html(nodes[node].title); 
            }
            else{
                $('.topic-dropdown-text').html("MULTISELECT"); 
            }
            
        } 
        // if(channelId.length == 0 && contentId.length == 0){
        //     channelId = ['-1'];
        //     contentId = ['-1'];
        // }
        updatePageContent();
        toggleTopicDropdown();
    }

    else
    {
        toastr.warning('You must select a topic to apply the filter.');
    }
};

var getTotalCount = function(node){
    if (node.getLevel() == 3){
        count1.push(node.key);
        levelDict[node.getLevel()] = count1
    }
    else if (node.getLevel() == 2){
        count2.push(node.key);
        levelDict[node.getLevel()] = count2
    } 
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
            if (response.code) {
                toastr.error(response.info.message, response.info.title);
            } else if (!response.data) {
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
    // updateLoadingInfo();
    setupDateRangePicker();
    setupDateRangePickerEndDate();
    refreshLessonsDropdown();
    setDummyData();
    // updatePageContent();
});
