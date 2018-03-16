$(document).ready(function () {
    var csrf_token  = document.getElementById("csrfcode").value;
    var code = document.getElementById("code").value;
    var userdata = eval(document.getElementById("userData").value);
    if(code == 2001){
        otable = $('#usertable').DataTable({
        columns:[
          
                    // {"data": "userid"},
                    {"title": "UserName"},
                    {"title": "Email"},
                    {"title": "Role"},
                    {"title": "Institute Name"},
                    {"title": "Class Name"}
                ]
        });
    }
    else {

        // var userData = data.pendingUsers|safe ;
        otable = $('#usertable').DataTable({
            data : userdata,
            columns:[
                // {"data": "userid"},
                {"title": "UserName","data": "username"},
                {"title": "Email","data": "email"},
                {"title": "Role","data": "role"},
                {"title": "Institute Name","data": "instituteName"},
                {"title": "Class Name","data": "className"},
                {
                    "title": "SearchUser",
                    "visible": false,
                    "searchable":true,
                    "render": function(data, type,full, meta){
                        if (full.isActive){
                            return '#'
                        }
                        else{
                            return '$'
                        }
                    }
                },
                {
                    "title": "Active/Inactive",
                    "data" : "isActive",
                    'className': 'dt-body-center',
                    'searchable' : true,
                    "render": function (data, type, full, meta){
                        if (full.isActive){
                            return '<input type="checkbox" name="id[]" checked = "checked"value="' + $('<div/>').text(data).html() + '">';
                        }
                        else{
                            return '<input type="checkbox" name="id[]" value="' + $('<div/>').text(data).html() + '">';
                        }
                    }
                },
                {
                    "title":"Action",
                    'className': 'dt-body-center',
                    "render": function (data, type, full, meta){
                        return '<a class="remove-row" href="javascript: void(0)"><i class="glyphicon glyphicon-trash"></i></a>';
                    }
                },
            ],
        });
    }
    function parseTable(row, text,approveresult) {

        if (row.find('input[name="' + text + '"]').is(':checked') || row.find('input[name="' + text + '"]').not(':checked')) {
            var rowapprove = {};

            if (approveresult[row[0].children[0].innerHTML] != null) {
                if (row[0].children[4].id && row[0].children[4].id>0) {
                    approveresult[row[0].children[0].innerHTML].push(row[0].children[4].id);
                }
            }
            else {
                approveresult[row[0].children[0].innerHTML] = [];
                if (row[0].children[4].id && row[0].children[4].id>0) {
                    approveresult[row[0].children[0].innerHTML].push(row[0].children[4].id);
                }
            }
        }
        return approveresult;
    }

    function createRequestObject(approveresult) {
        var finalresult = [];
        for (obj in approveresult) {
            var result = {};
            result.username = obj;
            result.classes = approveresult[obj];
            finalresult.push(result);
        }
        var approveresultobj = {};
        approveresultobj.users = finalresult;
        return approveresultobj;
    }

    function createRequestObjectBlockedUsers(approveresult) {
        var finalresult = {};
        finalresult.usernames=[];
        for (obj in approveresult) {
            finalresult.usernames.push(obj);
        }
        return finalresult;
    }


    function ajaxrequest(url, dataObject, successcallback) {
        $.ajax({
            type: 'POST',
            url: url,
            data: JSON.stringify(dataObject),
            headers: {'X-CSRFToken': csrf_token },
            success: successcallback,
            error: function (jqXHR, textStatus, errorThrown) {
            },
            dataType: 'json'
        });
    };

    $(':checkbox').click(function () {
        var currentRow = this.parentNode.parentNode;

        if($(this).attr('name')=="appchk" && $(this).is(':checked'))
        {
            $(currentRow).find('input[name=disappchk]').prop('checked', false);
        }
        else if($(this).attr('name')=="disappchk" && $(this).is(':checked'))
        {
            $(currentRow).find('input[name=appchk]').prop('checked', false);
        }
    });

    $("input:checkbox").on("click", function(){
        approveresult = {}
        disapproveresult = {}
        if ($(this).is(":checked")){
            WRN_PROFILE_DELETE = "Are you sure you want to Active this user?"; 
            var check = confirm(WRN_PROFILE_DELETE);
            if(check == true){ 
                var row = $(this).closest('tr')
                approveresult = parseTable(row, 'appchk', approveresult);
                var approveresultobj = createRequestObject(approveresult);
                ajaxrequest('./api/user/approve', approveresultobj);
            }

        }
        else
        {
            WRN_PROFILE_DELETE = "Are you sure you want to Inactive this user?"; 
            // alert ("Are you sure to InActive the ")
            var check = confirm(WRN_PROFILE_DELETE);  
            if(check == true){
                var row = $(this).closest('tr')
                disapproveresult = parseTable(row, 'appchk', disapproveresult);
                var disapproveresultobj = createRequestObject(disapproveresult);
                ajaxrequest('./api/user/disapprove', disapproveresultobj);    
            } 
        }
        setTimeout(function(){window.location = window.location}, 3000);
    });

    $(".remove-row").on('click', function() {
        deleteuserresult = {};
        WRN_PROFILE_DELETE = "Are you sure you want to delete this user?";  
        var check = confirm(WRN_PROFILE_DELETE);  
        if(check == true){
            var row = $(this).closest('tr')
            deleteuserresult = parseTable(row, 'appchk', deleteuserresult);
            var deleteuserobj = createRequestObject(deleteuserresult);
            ajaxrequest('./api/user/delete', deleteuserobj);
            otable.row(row).remove().draw( false );
           }
        });

    $("#radActive").change(function(){
        otable.column(5).search("#").draw()
    });

    $("#radInActive").change(function(){
        otable.column(5).search("$").draw()
    });

    $("#radAll").change(function(){
        otable.column(5).search("").draw()
    });
});

