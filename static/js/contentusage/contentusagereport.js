"use strict";

// globals
var table = null; // main data table
var aggregationTable = null; // aggregation table
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
    
    sendPOSTRequest('/contentusage/api/contentusage/get-page-meta', {
        startTimestamp: startTimestamp,
        endTimestamp: endTimestamp,
        contentId: contentID,
        channelId:channelID,
        filetrcontetusage: filetrcontetusage,
        parentLevel: parentLevel,
        previousContentID: objpreviouscontentlID,
        previousChannelID: objpreviouschannelID,
        // parentId: parentId
    }, function(response) {
        setBreadcrumb(response.data);
        setTableMeta(response.data);
        data1 = response.data;
        var currentdate = new Date(); 
        var current = currentdate.getTime()
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
		    data2 = response.data;
		    checkTableDataConsistancy(data1, data2);
            setTableData(response.data);
            // levelDict={};
            count1 = [];
            count2 = [];
	    });
    });
    dismissTrendChart();
};

// Used to check the consisatncy of masterymeta and masterydata result
var checkTableDataConsistancy = function(data1, data2) {
	if (!debug) {
		return;
	}
	if (!data1.rows) {
		console.error('Data Error: `get-page-meta` does not return valid rows data.');
		return;
	}
	if (!data1.metrics) {
		console.error('Data Error: `get-page-data` does not return valid metrics data.');
		return;
	}
	if (!data1.breadcrumb) {
		console.error('Data Error: `get-page-data` does not return valid breadcrumb data.');
		return;
	}
	if (!data2.rows) {
		console.error('Data Error: `get-page-data` does not return valid rows data.');
		return;
	}
	if (!data2.aggregation) {
		console.error('Data Error: `get-page-data` does not return valid aggregation data.');
		return;
	}
	if (data1.rows.length != data2.rows.length) {
		console.error('Data Inconsistency Error: `get-page-meta` returns ' + data1.rows.length + ' records while `get-page-data` returns ' + data2.rows.length + ' records.');
		return;
	}
	if (data2.rows.length > 0 && data1.metrics.length != data2.rows[0].values.length) {
		console.error('Data Inconsistency Error: `get-page-meta` returns ' + data1.metrics.length + ' metrics while `get-page-data` returns ' + data2.rows[0].values.length + ' values.');
		return;
	}
};

// Fetch topics by calling API and update the dropdown menu
// Called only once upon page initialization
var refreshSchoolsDropdown = function() {
    sendPOSTRequest('/contentusage/api/contentusage/schools', {
        startTimestamp: startTimestamp,
        endTimestamp: endTimestamp,
        parentLevel: parentLevel,
        parentId: parentId
    }, function(response) {
        buildSchoolsDropdown(response.data);
    });
};

// Get trend data with specific item id from server (via POST) and sanitize it 
// Used by `drawTrendChart`
var getTrendData = function(itemId,channelid, callback) {    
    sendPOSTRequest('/contentusage/api/contentusage/trend', {
        startTimestamp: startTimestamp,
        endTimestamp: endTimestamp,
        contentId: contentID,
        channelId: channelID,
        level: parentLevel ,
        itemId: itemId,
        itemChannelId : channelid,
        filetrcontetusage: filetrcontetusage,
        std:std,
    }, function(response) {
	    verifyTrendResponse(response);
        callback(processTrendData(response.data));
    });            
};

var verifyTrendResponse = function(response) {
	if (!debug) {
		return;
	}
	if (!response || !response.data) {
		console.error('Data Error: `get-trend` did not return valid data.');
		return;
	}
	var data = response.data;
	
	if (!data.series) {
		console.error('Data Error: `get-trend` did not return valid series data.');
		return;
	}
	if (!data.points) {
		console.error('Data Error: `get-trend` did not return valid points data.');
		return;
	}
	if (data.series.length == 0) {
		console.error('Data Error: `get-trend` returned 0 series.');
		return;
	}
	if (data.points.length == 0) {
		return;
	}
	if (!data.series[0].name) {
		console.error('Data Error: `get-trend` did not return valid name data for series.');
		return;
	}
	if (data.series[0].isPercentage) {
		console.error('Data Error: `get-trend` did not return valid isPercentage data for series.');
		return;
	}
	
	var nSeries = data.series.length;
	var pointSize = data.points[0].length;
	
	if (pointSize != nSeries + 1) {
		console.error('Data Inconsistency Error: There are ' + nSeries + ' series but ' + pointSize + 'values per point.');
		return;
	}	
};

// Instantiate date range picker
// Called only once upon page initialization
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
var buildSchoolsDropdown = function(data) {
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
        checkbox: true,
        selectMode: 3,
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
var setTableMeta = function(data) {
    tableMeta = data;
    
    // initialization run only once
    if (!metaSetOnce) {
        metaSetOnce = true;
        
        var sharedLengthMenu = [[30, 60, 90, 120], [30, 60, 90, 120]];

        // insert columns
        var idx;
        for (idx in data.metrics) {
            $('#data-table .trend-column').before('<th>' + data.metrics[idx].displayName + '</th>');
            $('#aggregation-table .trend-column').before('<th>' + data.metrics[idx].displayName + '</th>');
            $('#data-compare-table .dropdown-menu').append('<li><a href="#" onclick="setCompareMetricIndex(' + idx + ')">' + data.metrics[idx].displayName + '</a></li>');
            $('#data-performance-table .dropdown-menu-metric').append('<li><a href="#" onclick="setPerformanceMetricIndex(' + idx + ')">' + data.metrics[idx].displayName + '</a></li>');
        }
        
        // initialize tables


        table = $('#data-table').DataTable({
            columnDefs: [
                { orderable: false, targets: 3, "type": "html"}
            ],
            order: [[0, 'asc']],
            dom: 'Bfrtip',
            buttons: ['pageLength',
                {
                    extend: 'csv',           
                    exportOptions: {
                        columns: [0,1,2,3,4,5] // indexes of the columns that should be printed,
                    }                      // Exclude indexes that you don't want to print.
                },
                {
                    extend: 'excel',
                    exportOptions: {
                        columns: [0,1,2,3,4,5] 
                    }

                },
                {
                    extend: 'pdf',
                    exportOptions: {
                        columns: [0,1,2,3,4,5] 
                    }
                }
            ],  
            //buttons: ['pageLength'/*, 'copy'*/, 'csv', 'excel', 'pdf'/*, 'print'*/],
            lengthMenu: sharedLengthMenu
        });
        
        // Added for Testing Above code and commented below code
        // table = $('#data-table').DataTable({
        //     columnDefs: [
        //         { orderable: false, targets: 4 } // Added for Testing make 4 instead of 5
        //     ],
        //     order: [[0, 'asc']],
        //     dom: 'Bfrtip',
        //     buttons: ['pageLength'/*, 'copy'*/, 'csv', 'excel', 'pdf'/*, 'print'*/],
        //     lengthMenu: sharedLengthMenu
        // });
        
        aggregationTable = $('#aggregation-table').DataTable({
            paging: false,
            ordering: false,
            info: false,
            bFilter: false
        });
        
        compareTable = $('#data-compare-table').DataTable({
            columnDefs: [
                { orderable: false, targets: 2 }
            ],
            order: [[0, 'asc']],
            dom: 'Bfrtip',
            buttons: ['pageLength'],
            lengthMenu: sharedLengthMenu
        });
        
        performanceTable = $('#data-performance-table').DataTable({
            columnDefs: [
                { orderable: false, targets: 2 }
            ],
            order: [[0, 'asc']],
            dom: 'Bfrtip',
            buttons: ['pageLength'],
            lengthMenu: sharedLengthMenu
        });
    
        // manually toggle dropdown; stop event propagation to avoid unintentional table reorders
        $('thead .dropdown button').on('click', function(e){
            e.stopPropagation();  
            $('.dropdown-' + $(this).attr('id')).dropdown('toggle');
        });
    }
    
    // remove current rows
    
    table.clear();
    compareTable.clear();
    performanceTable.clear();
    aggregationTable.clear();
    
    // insert placeholder rows for data table
    var idx;
    for (idx in data.rows) {
        // data table
        
        var array = [drilldownColumnHTML(data.rows[idx].name, data.rows[idx].id, data.rows[idx].channelid, data.rows[idx].maxval)];
        var nItems = data.metrics.length;
        while (nItems--) {
            array.push('');
        }
        array.push(drawTrendButtonHTML(data.rows[idx].id, data.rows[idx].name, data.rows[idx].channelid));
        var rowNode = table.row.add(array).draw(false).node();
        var rowId = 'row-' + data.rows[idx].id;
        $(rowNode).attr('id', rowId);
        
        // compare table
        var compareArray = [drilldownColumnHTML(data.rows[idx].name, data.rows[idx].id, data.rows[idx].channelid, data.rows[idx].maxval)];
        compareArray.push('');
        compareArray.push('');
        var compareRowNode = compareTable.row.add(compareArray).draw(false).node();
        var compareRowId = 'row-' + data.rows[idx].id;
        $(compareRowNode).attr('id', rowId);
        
        // performance table
        var performanceArray = [drilldownColumnHTML(data.rows[idx].name, data.rows[idx].id, data.rows[idx].channelid, data.rows[idx].maxval)];
        performanceArray.push('');
        performanceArray.push('');
        var performanceRowNode = performanceTable.row.add(performanceArray).draw(false).node();
        var performanceRowId = 'row-' + data.rows[idx].id;
        $(performanceRowNode).attr('id', rowId);
    }
};

// Replace dummy data inserted in `setTableMeta` with real data
// Called every time the page needs update
var setTableData = function(data) {
    tableData = data;
    var idx;
    var tq;
    var te;
    
    // update data rows
    for (idx in data.rows) {
        var array = JSON.parse(JSON.stringify(data.rows[idx].values)); // deep copy an array
        array.unshift(drilldownColumnHTML(data.rows[idx].name, data.rows[idx].id, data.rows[idx].channelid, data.rows[idx].maxval));
        array.push(drawTrendButtonHTML(data.rows[idx].id, data.rows[idx].name, data.rows[idx].channelid));
        table.row('#row-' + data.rows[idx].id).data(array).draw(false);
        
        // compare table
        var compareArray = [drilldownColumnHTML(data.rows[idx].name, data.rows[idx].id, data.rows[idx].channelid, data.rows[idx].maxval), '', ''];
        compareTable.row('#row-' + data.rows[idx].id).data(compareArray).draw(false);
    }
    
    // add aggregation rows
    for (idx in data.aggregation) {
        var array = data.aggregation[idx].values;
        array.unshift(data.aggregation[idx].name);
        array.push('');
        aggregationTable.row.add(array).draw(false);
    }
    tq = data.rows[0]['total_questions']
    // te = data.rows[0]['total_subtopics']
    showTotalQuestions(tq);
    precalculate();
    setCompareMetricIndex(compareMetricIndex);
    setPerformanceMetricIndex(performanceMetricIndex);
};

var showTotalQuestions = function(qCount){
    var strQCount ;
    // var strExerciseCount;
    strQCount = qCount.toString();
    // strExerciseCount = eCount.toString();
    $('#totalQ').text(strQCount);
    // $('#totalExercise').text(strExerciseCount);
}
// Calculate statistical values
var precalculate = function() {
	compareMaxValues = [];
	performanceCompareToValues = [];
	
	var metricIndex;
	for (metricIndex in tableMeta.metrics) {
		// find max value
	    var maxVal = 0;
	    if ((tableData.rows.length > 0) && (typeof tableData.rows[0].values[metricIndex] === 'string')) {
	        maxVal = 100; // value type is percentage
	    } else {
		    var idx;
	        for (idx in tableData.rows) {
	            var rowValue = parseFloat(tableData.rows[idx].values[metricIndex]);
	            if (rowValue > maxVal) {
	                maxVal = rowValue;
	            }
	        }
	    }
	    compareMaxValues[metricIndex] = maxVal;
	}
	
	for (metricIndex in tableMeta.metrics) {
		// update compared-to values
		var isPercentage = (tableData.rows.length > 0) && (typeof tableData.rows[0].values[metricIndex] === 'string');
	    var values = [];
	    var idx;
	    for (idx in tableData.rows) {
	        values.push(parseFloat(tableData.rows[idx].values[metricIndex]));
	    }
	    
	    values.sort(function(a, b) { 
	        return a - b;
	    });
	    
	    var min = values[0];
	    var max = values[values.length - 1];
	    var sum = values.reduce(function(a, b) {
	        return a + b; 
	    }, 0);
	    var average = sum / values.length;
	    var half = Math.floor(values.length / 2);
	    var median = (values.length % 2) ? values[half] : ((values[half-1] + values[half]) / 2.0);
	    var suffix = isPercentage ? '%' : '';
	    
	    // set globals
	    
	    performanceCompareToValues[metricIndex] = {
	        min: min,
	        max: max,
	        average: average,
	        median: median,
	        suffix: suffix
	    };
	}
}

/** Pragma Mark - UIAction **/

// Set index of compare metric in the compare view
// UIAction
var setCompareMetricIndex = function(metricIndex) {
    compareMetricIndex = metricIndex;
    var metricName = tableMeta.metrics[metricIndex].displayName;
    $('#data-compare-table .current-metric').html(metricName);
    
    // find max value
    var maxValue = compareMaxValues[metricIndex];
    var idx;
    // update data rows
    for (idx in tableData.rows) {
        var rowValue = parseFloat(tableData.rows[idx].values[metricIndex]);
        var percentage = Math.round(maxValue == 0 ? 0 : (rowValue / maxValue * 100));
        var barHTML =   '<div class="progress">'+
                        '<div class="progress-bar" role="progressbar" aria-valuenow="' + percentage + 
                        '" aria-valuemin="0" aria-valuemax="100" style="width: ' + percentage + '%;">'+
                        '</div></div>';
        var compareArray = [
            drilldownColumnHTML(tableData.rows[idx].name, tableData.rows[idx].id, tableData.rows[idx].channelid, tableData.rows[idx].maxval), 
            tableData.rows[idx].values[metricIndex], 
            barHTML
        ];
        compareTable.row('#row-' + tableData.rows[idx].id).data(compareArray).draw(false);
    }
};

// Set index of compare metric in performance view
// UIAction
var setPerformanceMetricIndex = function(metricIndex) {
    performanceMetricIndex = metricIndex;
    var metricName = tableMeta.metrics[metricIndex].displayName;
    var isPercentage = (tableData.rows.length > 0) && (typeof tableData.rows[0].values[metricIndex] === 'string');
    $('#data-performance-table .current-metric').text(metricName);

	var vals = performanceCompareToValues[metricIndex];
    
    // update dropdown
    
    $('.compare-max a').text('Max: ' + vals.max + vals.suffix);
    $('.compare-min a').text('Min: ' + vals.min + vals.suffix);
    $('.compare-average a').text('Average: ' + (Math.round(vals.average * 10) / 10) + vals.suffix);
    $('.compare-median a').text('Median: ' + vals.median + vals.suffix);
    
    // update dropdown title and bars
    // updating compare metric will also affect the value of chosen compared values (different base values)
    updatePerformanceView();
};

// Set the compared value for performance view
// UIAction
var setPerformanceCompareToValue = function(valueName) {
    performanceCompareToValueName = valueName;
    updatePerformanceView();
};

// Get data remotely via `getTrendData` (async) and draw the chart (after removing previous chart -- if any)
// UIAction
var drawTrendChart = function(itemId, itemName, channelid) {
    dismissTrendChart();
    getTrendData(itemId, channelid, function(trendData) {
        var chartData = new google.visualization.DataTable();
        
        if (trendData.points.length == 0) {
            toastr.info('No trend data is available for the selected period.');
            return;
        }
        
        var earlyDate = trendData.points[0][0];
        var lateDate = trendData.points[trendData.points.length - 1][0];
        var options = {
            chart: {
                title: itemName + ' Content Usage Trend',
                subtitle: 'Data from ' + moment(earlyDate).format('MM/DD/YYYY') + ' to ' + moment(lateDate).format('MM/DD/YYYY')
            },
            legend: { position: 'bottom' },
            width: 900,
            height: 500,
            series: {
            },
            axes: {
                y: {
                    percentage: {label: 'Percentage'},
                    number: {label: 'Number'}
                }
            }
        };
        
        chartData.addColumn('date', 'Date');
        
        var seriesIndex = 0;
        var idx;
            
        for (idx in trendData.series) {
            var dict = trendData.series[idx];
            var type = dict.isPercentage ? 'percentage' : 'number';
            chartData.addColumn('number', dict.name);
            options.series[seriesIndex++] = {axis: type};
        }
        
        chartData.addRows(trendData.points);

        var chartContainer = document.getElementById('chart-wrapper');
        var chart = new google.charts.Line(chartContainer);
        

        chart.draw(chartData, options);
        setTrendChartVisible(true);
        

        // scroll to chart w/ animation
        $('html, body').animate({
            scrollTop: $('#chart-wrapper').offset().top
        }, 500);
    });
};

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

// Handle click event of a drilldown link
// UIAction
var performDrilldown = function(itemId, channelid) {
    objpreviouschannelID.push(channelid);
    objpreviouscontentlID.push(itemId);
    contentID = itemId;
    channelID = channelid;
    parentLevel++;
    updatePageContent();
};

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

// Dismiss trend diagram
// UIAction
var dismissTrendChart = function() {
    $('#chart-wrapper').html('');
    setTrendChartVisible(false);
};

/** Pragma Mark - Utilities **/

// Append a new breadcrumb item to the current list
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

// Returns the HTML code for draw trend button
var drawTrendButtonHTML = function(itemId, itemName, channelid) {
    return '<button class="btn btn-default draw-trend-button" onclick="drawTrendChart(\'' 
           + itemId + '\', \'' + itemName + '\', \''+ channelid +'\')"><i class="fa fa-line-chart" aria-hidden="true"></i> Show Trend</button>';
};
        
// HTML code of drilldown column in data table
var drilldownColumnHTML = function(name, id, channelid, maxval) {
    // alert(channelid);
    maxval = maxval;
    // alert(maxval);
    if (maxval) {
        return '<span>' + name + '</span>';
    } else {
        return '<a href="#" class="drilldown-link" onclick="performDrilldown(\'' + id + '\', \''+ channelid +'\')">' + name + '</a>';
    }
};

// Trend data preprocessing. Converts timestamp to date object.
var processTrendData = function(data) {
    // API issue: data.points and data.data are both used historically. 
    // We use data.points as the official one but accept data.data also as a compatibility patch.
    if (data.data !== null && data.points === null) {
        data.points = data.data;
    }

    var idx;
    for (idx in data.points) {
        var timestamp = data.points[idx][0];
        var dateObject = new Date(timestamp * 1000);
        data.points[idx][0] = dateObject;
    }
    
    return data;
};

// Sets whether the trend chart is visible.
var setTrendChartVisible = function(visible) {
    if (visible) {
        $('.trend-chart').removeClass('hidden');
    } else {
        $('.trend-chart').addClass('hidden');
    }
};

// Update the title of compared value and all actual table rows in performance view
var updatePerformanceView = function() {
    var vals = performanceCompareToValues[performanceMetricIndex];
    
    // dropdown title and pivot value
    
    var pivot;
    
    if (performanceCompareToValueName === 'max') {
        $('.current-compared-value').text('Max: ' + (vals.max) + vals.suffix);
        pivot = vals.max;
    }
    if (performanceCompareToValueName === 'min') {
        $('.current-compared-value').text('Min: ' + (vals.min) + vals.suffix);
        pivot = vals.min;
    }
    if (performanceCompareToValueName === 'average') {
        $('.current-compared-value').text('Average: ' + (Math.round(vals.average * 10) / 10) + vals.suffix);
        pivot = vals.average;
    }
    if (performanceCompareToValueName === 'median') {
        $('.current-compared-value').text('Median: ' + (vals.median) + vals.suffix);
        pivot = vals.median;
    }
    
    // table rows
    
    // some notes:
    // `raw value` is the original value of the data item; it can be any positive number
    // `pivot` is the value against which all `raw value`s are compared; it can be a max value, min value, average value or median value of all `raw value`s
    // `compare value` is the percentage of the `raw value` to the `pivot value`; it can be anything, positive or negative
    // `max` is the maximum `compare value`, but no less then 100
    // `min` is the minimum `compare value`, but no more then -100
    // `positive value` and `negative value` are `compare value`s scaled to a -100~100 range, when taking all `compare value`s into consideration. Only one will contain a non-zero number, dependending on the value's negativity.
    
    var max = 100;
    var min = -100;
    var idx;
    
    for (idx in tableData.rows) {
        var rawValue = parseFloat(tableData.rows[idx].values[performanceMetricIndex]);
        var compareValue = (rawValue - pivot) / pivot * 100;
        if (compareValue > max) {
            max = compareValue;
        }
        if (compareValue < min) {
            min = compareValue;
        }
    }
    
    for (idx in tableData.rows) {
        var rawValue = parseFloat(tableData.rows[idx].values[performanceMetricIndex]);
        var compareValue = (rawValue - pivot) / pivot * 100;
        var positiveValue = 0;
        var negativeValue = 0;
        
        var negativeLabel = '';
        var positiveLabel = '';
                
        if (compareValue > 0) {
            positiveValue = compareValue / max * 100;
            positiveLabel = '+' + (Math.round(compareValue * 10) / 10) + '%';
        } else if (compareValue < 0) {
            negativeValue = compareValue / min * 100; // the variable holds a positive number, but `represents` a negative value
            negativeLabel = (Math.round(compareValue * 10) / 10) + '%';
        }
        
        var barHTML =   '<div class="progress progress-negative">' +
                        '<div class="progress-bar progress-bar-danger" role="progressbar" aria-valuenow="' + negativeValue + 
                        '" aria-valuemin="0" aria-valuemax="100" style="width: ' + negativeValue + '%;">' + negativeLabel +
                        '</div></div>' +
                        '<div class="progress progress-positive">' +
                        '<div class="progress-bar progress-bar-success" role="progressbar" aria-valuenow="' + positiveValue + 
                        '" aria-valuemin="0" aria-valuemax="100" style="width: ' + positiveValue + '%;">' + positiveLabel +
                        '</div></div>';
                        
        var array = [drilldownColumnHTML(tableData.rows[idx].name, tableData.rows[idx].id, tableData.rows[idx].channelid, tableData.rows[idx].maxval), tableData.rows[idx].values[performanceMetricIndex], barHTML];
        
        performanceTable.row('#row-' + tableData.rows[idx].id).data(array).draw(false);
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
    refreshSchoolsDropdown();
    updatePageContent();
});
