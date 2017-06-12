window.onload = function(){
    var d = new Date();
    var month_name = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Augosto','Setembro','Outubro','Novembro','Dezembro'];
    var month = d.getMonth();   //0-11
    var year = d.getFullYear(); //2017
    var first_date = month_name[month] + " " + 1 + " " + year;
    //Março 3 2017
    var tmp = new Date(first_date).toDateString();
    //Qui Mar 30 2017 ...
    var first_day = tmp.substring(0, 3);    //Qui
    var day_name = ['Dom','Seg','Ter','Qua','Qui','Sex','Sab'];
    var day_no = day_name.indexOf(first_day);   //1
    var days = new Date(year, month+1, 0).getDate();    //30
    //Qui Mar 30 2017 ...
    var calendar = get_calendar(day_no, days);
    document.getElementById("calendar-month-year").innerHTML = month_name[month]+" "+year;
    document.getElementById("calendar-dates").appendChild(calendar);
}

function get_calendar(day_no, days){
    var table = document.createElement('table');
    var tr = document.createElement('tr');
    
    //row for the day letters
    for(var c=0; c<=6; c++){
        var td = document.createElement('td');
        td.innerHTML = "DSTQQSS"[c];
        tr.appendChild(td);
    }
    table.appendChild(tr);
    
    //create 2nd row
    tr = document.createElement('tr');
    var c;
    for(c=0; c<=6; c++){
        if(c == day_no){
            break;
        }
        var td = document.createElement('td');
        td.innerHTML = "";
        tr.appendChild(td);
    }
    
    var count = 1;
    for(; c<=6; c++){
        var td = document.createElement('td');
        td.innerHTML = count;
        count++;
        tr.appendChild(td);
    }
    table.appendChild(tr);
    
    //rest of the date rows
    for(var r=3; r<=7; r++){
        tr = document.createElement('tr');
        for(var c=0; c<=6; c++){
            if(count > days){
                table.appendChild(tr);
                return table;
            }
            var td = document.createElement('td');
            td.innerHTML = count;
            count++;
            tr.appendChild(td);
        }
        table.appendChild(tr);
    }
    return table;
}