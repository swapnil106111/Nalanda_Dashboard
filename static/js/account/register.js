$(document).ready(function () {
    var institutedata = document.getElementById('schooldata').value;
    institutedata = eval(institutedata);
    // alert(institutedata);
    // institutedata = JSON.toString(institutedata);
    // on page load follloiwng actions should be taken
    // 1. hide institutes drop down and classes drop down
    $("#InstitutesSelecDiv").hide();
    $("#ClassesSelectDiv").hide();

    // This function is performed when role is changed
    // It shows institutes or classes based on role sleected
    $("#id_username" ).keyup(function() {
        var re = /^\w+$/;
        var username = document.getElementById('id_username').value;
        if (username == '' ){
            return true;
        }
        var res = re.exec(username);
        if (res == null) {
            var errorname = document.getElementById('errorname')
            errorname.innerText = 'Username must contain only letters, numbers and underscores!';
            // alert("Error: Username must contain only letters, numbers and underscores!");
            return false;
        }
        else{
            var errorname = document.getElementById('errorname')
            errorname.innerText = '';
        }
    });
    $("#id_role").change(function () {
        var e = document.getElementById("id_role");
        var strUserRole = e.options[e.selectedIndex].value;
        $("#InstitutesSelecDivforBM").hide();
        $("#InstitutesSelecDiv").hide();
        $("#ClassesSelectDiv").hide();
        if (strUserRole != "" && strUserRole != 1) {
            $("#InstitutesSelecDiv").show();
            $("#id_institutes").val("");
        }
        else if (strUserRole == 1){
            select  = document.getElementById('id_institutes');
            var option = ""
            var institutesforbm = ""
            $.each(select, function(k,v)
            {
                if (v.value!=""){
                    option += '<input type="checkbox" name="institutesforbm"  value="' + v.value + '"/> ' + v.text + '<br />'
                }
            });
            institutesforbm = option
            $("#checkBoxesOuterdivforBM div").html(institutesforbm);
            if (institutesforbm!=""){
                $("#InstitutesSelecDivforBM").show();
            }
        }
        else
        {
            $("#InstitutesSelecDiv").hide();
            $("#id_institutes").val("");
        }
    }).change();

    // This function is performed when institute is changed or selected
    // It shows classes based on role selected
    $('#id_institutes').change(function () {
        $("#ClassesSelectDiv").hide();
        var valueSelected = $(this).val();
        idselected = $('#id_role').val();
        var classes = '';        
        if (idselected == 3 && valueSelected !='') {
            var option = ""
            // var option = "<option value>---------</option>";
            $.each(institutedata[valueSelected], function(k,v){
                option += '<input type="checkbox" name="classes"  value="' + v.class_id + '"/> ' + v.class_name + '<br />'
            });
            classes = option 
        }
        
        $("#checkBoxesOuterdiv div").html(classes);
        if (classes!="")
            $("#ClassesSelectDiv").show();
    }).change();
});

