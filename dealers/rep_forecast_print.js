console.log('Printing!');
var year = 2024;
console.log('Year', year);
var repTotal = 0;
var forecastTotal = 0;
var dealerName = getValue('REP_TOOLS_'+ year, 'DEALERNAME');



var augrepfc = getValue('REP_TOOLS_'+ year, 'AUG_REP_FC'); if(augrepfc === false){augrepfc = ""; } else{ repTotal += parseInt(augrepfc); }
var seprepfc = getValue('REP_TOOLS_'+ year, 'SEP_REP_FC'); if(seprepfc === false){seprepfc = ""; }else{ repTotal += parseInt(seprepfc); }
var octrepfc = getValue('REP_TOOLS_'+ year, 'OCT_REP_FC'); if(octrepfc === false){octrepfc = ""; }else{ repTotal += parseInt(octrepfc); }
var novrepfc = getValue('REP_TOOLS_'+ year, 'NOV_REP_FC'); if(novrepfc === false){novrepfc = ""; }else{ repTotal += parseInt(novrepfc); }
var decrepfc = getValue('REP_TOOLS_'+ year, 'DEC_REP_FC'); if(decrepfc === false){decrepfc = ""; }else{ repTotal += parseInt(decrepfc); }
var janrepfc = getValue('REP_TOOLS_'+ year, 'JAN_REP_FC'); if(janrepfc === false){janrepfc = ""; }else{ repTotal += parseInt(janrepfc); }
var febrepfc = getValue('REP_TOOLS_'+ year, 'FEB_REP_FC'); if(febrepfc === false){febrepfc = ""; }else{ repTotal += parseInt(febrepfc); }
var marrepfc = getValue('REP_TOOLS_'+ year, 'MAR_REP_FC'); if(marrepfc === false){marrepfc = ""; }else{ repTotal += parseInt(marrepfc); }
var aprrepfc = getValue('REP_TOOLS_'+ year, 'APR_REP_FC'); if(aprrepfc === false){aprrepfc = ""; }else{ repTotal += parseInt(aprrepfc); }
var mayrepfc = getValue('REP_TOOLS_'+ year, 'MAY_REP_FC'); if(mayrepfc === false){mayrepfc = ""; }else{ repTotal += parseInt(mayrepfc); }
var junrepfc = getValue('REP_TOOLS_'+ year, 'JUN_REP_FC'); if(junrepfc === false){junrepfc = ""; }else{ repTotal += parseInt(junrepfc); }
var julrepfc = getValue('REP_TOOLS_'+ year, 'JUL_REP_FC'); if(julrepfc === false){julrepfc = ""; }else{ repTotal += parseInt(julrepfc); }

var augfc = getValue('REP_TOOLS_'+ year, 'AUG_FC'); if(augfc === false){augfc = ""; }else{ forecastTotal += parseInt(augfc); }
var sepfc = getValue('REP_TOOLS_'+ year, 'SEP_FC'); if(sepfc === false){sepfc = ""; }else{ forecastTotal += parseInt(sepfc); }
var octfc = getValue('REP_TOOLS_'+ year, 'OCT_FC'); if(octfc === false){octfc = ""; }else{ forecastTotal += parseInt(octfc); }
var novfc = getValue('REP_TOOLS_'+ year, 'NOV_FC'); if(novfc === false){novfc = ""; }else{ forecastTotal += parseInt(novfc); }
var decfc = getValue('REP_TOOLS_'+ year, 'DEC_FC'); if(decfc === false){decfc = ""; }else{ forecastTotal += parseInt(decfc); }
var janfc = getValue('REP_TOOLS_'+ year, 'JAN_FC'); if(janfc === false){janfc = ""; }else{ forecastTotal += parseInt(janfc); }
var febfc = getValue('REP_TOOLS_'+ year, 'FEB_FC'); if(febfc === false){febfc = ""; }else{ forecastTotal += parseInt(febfc); }
var marfc = getValue('REP_TOOLS_'+ year, 'MAR_FC'); if(marfc === false){marfc = ""; }else{ forecastTotal += parseInt(marfc); }
var aprfc = getValue('REP_TOOLS_'+ year, 'APR_FC'); if(aprfc === false){aprfc = ""; }else{ forecastTotal += parseInt(aprfc); }
var mayfc = getValue('REP_TOOLS_'+ year, 'MAY_FC'); if(mayfc === false){mayfc = ""; }else{ forecastTotal += parseInt(mayfc); }
var junfc = getValue('REP_TOOLS_'+ year, 'JUN_FC'); if(junfc === false){junfc = ""; }else{ forecastTotal += parseInt(junfc); }
var julfc = getValue('REP_TOOLS_'+ year, 'JUL_FC'); if(julfc === false){julfc = ""; }else{ forecastTotal += parseInt(julfc); }


console.log('aprfc',aprfc);


PrintElem();

function PrintElem()
{
    var mywindow = window.open('', 'PRINT', 'height=400,width=600');

    mywindow.document.write('<html><head><title></title>');
    mywindow.document.write('</head><body >');

    mywindow.document.write('<h1>' + year  + ' Forecast - '+dealerName+'</h1>');
    mywindow.document.write('<table width=100%><tr><td><h3>Month</h3></td><td><h3>Forecast</h3></td><td><h3>Rep Forecast</h3></td></tr>');

    mywindow.document.write('<tr><td><h3>August</h3> </td><td><h3>' + augfc  + '</h3></td><td><h3>' + augrepfc  + '</h3></td></tr>');
    mywindow.document.write('<tr><td><h3>September</h3> </td><td><h3>' + sepfc  + '</h3></td><td><h3>' + seprepfc  + '</h3></td></tr>');
    mywindow.document.write('<tr><td><h3>October</h3> </td><td><h3>' + octfc  + '</h3></td><td><h3>' + octrepfc  + '</h3></td></tr>');
    mywindow.document.write('<tr><td><h3>November</h3> </td><td><h3>' + novfc  + '</h3></td><td><h3>' + novrepfc  + '</h3></td></tr>');
    mywindow.document.write('<tr><td><h3>December</h3> </td><td><h3>' + decfc  + '</h3></td><td><h3>' + decrepfc  + '</h3></td></tr>');
    mywindow.document.write('<tr><td><h3>January</h3> </td><td><h3>' + janfc  + '</h3></td><td><h3>' + janrepfc  + '</h3></td></tr>');
    mywindow.document.write('<tr><td><h3>February</h3> </td><td><h3>' + febfc  + '</h3></td><td><h3>' + febrepfc  + '</h3></td></tr>');
    mywindow.document.write('<tr><td><h3>March</h3> </td><td><h3>' + marfc  + '</h3></td><td><h3>' + marrepfc  + '</h3></td></tr>');
    mywindow.document.write('<tr><td><h3>April</h3> </td><td><h3>' + aprfc  + '</h3></td><td><h3>' + aprrepfc  + '</h3></td></tr>');
    mywindow.document.write('<tr><td><h3>May</h3> </td><td><h3>' + mayfc  + '</h3></td><td><h3>' + mayrepfc  + '</h3></td></tr>');
    mywindow.document.write('<tr><td><h3>June</h3> </td><td><h3>' + junfc  + '</h3></td><td><h3>' + junrepfc  + '</h3></td></tr>');
    mywindow.document.write('<tr><td><h3>July</h3> </td><td><h3>' + julfc  + '</h3></td><td><h3>' + julrepfc  + '</h3></td></tr>');
    mywindow.document.write('<tr><td><h3>TOTAL</h3> </td><td><h3>'+forecastTotal+'</h3></td><td><h3>'+repTotal+'</h3></td></tr>');

    mywindow.document.write('</table>');


    //mywindow.document.write(document.getElementById(elem).innerHTML);
    mywindow.document.write('</body></html>');

    mywindow.document.close(); // necessary for IE >= 10
    mywindow.focus(); // necessary for IE >= 10*/

    mywindow.print();
    mywindow.close();

    return true;
}

    reset('BTN','REPPRINT');
