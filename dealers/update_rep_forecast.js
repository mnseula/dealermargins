//rethink this if they aren't going to allow the dealers to save

console.log('Save Rep Forecast');
if (hasAnswer('TERMS', 'TERMS') || getValue('PROFILE', 'TYPE') === 'BEN' || getValue('PROFILE', 'TYPE') === 'SALESREP') {

    var mnth = ['AUG', 'SEP', 'OCT', 'NOV', 'DEC', 'JAN', 'FEB', 'MAR', 'APR',
        'MAY', 'JUN', 'JUL', 'TOT_REP'
    ];
    //var year = loadByListName('Current_Model_Year')[0].MODEL_YEAR;
    var year = '2024';
    if (getValue('PROFILE', 'ROLE') === 'SUPERUSER' || getValue('PROFILE', 'TYPE') === 'SALESREP' || getValue('PROFILE', 'ROLE') === 'INSIDESALESMGR' || getValue('PROFILE', 'ROLE') === 'SALESMGR') {
        console.log('Save Rep Forecast - Line 12');
        var dlrNo = getValue('CUSTSERV', 'FIND');
        var dlrName = getValue('CUSTSERV', 'DEALERNAME');
        dlrNoTrimmed = dlrNo.replace(/^(0+)/g, '');
        //console.log(dlrNo);
    }
    else {
        console.log('Save Rep Forecast - Line 19');
        var dlrNo = getValue('EOS', 'CUSTOMER_NO');
        var dlrName = getValue('EOS', 'COMPANY');
        //console.log(dlrNo);
    }

    var salesrep = loadByListName('dealers', "WHERE DlrNo= '" + pad(dlrNo, 8) + "'")[0].SalesPerson;
    console.log(salesrep);

    //Calculate New Total for Current Year Forecast field.

    updatevalues = []; //store them as you add them up for the update command.
    fcTot = 0;
    $.each($('input[name^="REP_TOOLS_' + year + '/"][name$="REP_FC"][name!="REP_TOOLS_' + year + '/TOT_REP_FC"]'), function (i, qa) {
        var code = $(qa).data('ref');
        var codeObj = code.split('/');
        var q = codeObj[0];
        var a = codeObj[1];
        var val = Number($(qa).val());
        console.log(q, a, val);
        if (val === 0) {
            setValue(q, a, val.toString());
        }
        updatevalues.push(val);
        fcTot += val;
    });
    console.log(updatevalues);
    setValue('REP_TOOLS_' + year, 'TOT_REP_FC', fcTot);

    //console.table(updatevalues);

    //Select forecast for this dealer and this year.  Check to see if there is one.
    //If so, update, if not insert.

    window.currentforecast = loadByListName('dealer_forecast_new', "WHERE DEALER_NO = '" + dlrNoTrimmed + "' AND FORECAST_MY= ' " + year + "'");

    //console.log(currentforecast);
    //end test for existence

    var locked = 0;
    if (hasAnswer('HIDE', 'REPLOCKED')) {
        locked = getValue('HIDE', 'REPLOCKED');
    }


    var data = [dlrNoTrimmed, year, updatevalues[0], updatevalues[1], updatevalues[2], updatevalues[3], updatevalues[4],
        updatevalues[5], updatevalues[6], updatevalues[7], updatevalues[8], updatevalues[9], updatevalues[10],
        updatevalues[11], fcTot, locked];


    if (currentforecast.length !== 0) {
        console.log("There is a current forecast to update");
        //console.log(data);
        sStatement('UPD_DLR_REP_FORECAST', data);

        alert('Update completed for ' + dlrName + '.');
        reset('BTN', 'SAVE');
    }
    else {
        console.log("There is no forecast to update, must insert.");

        var data = [salesrep, dlrNoTrimmed, dlrName, year, updatevalues[0], updatevalues[1], updatevalues[2], updatevalues[3],
            updatevalues[4], updatevalues[5], updatevalues[6], updatevalues[7], updatevalues[8], updatevalues[9],
            updatevalues[10], updatevalues[11], fcTot];
        console.log(data);
        sStatement('INS_DLR_REP_FORECAST', data);
        alert('Rep Forecast Update completed for ' + dlrName + '.');
    }


    reset('BTN', 'SAVE_REP_FC');

} else {

    console.log('Save Rep Forecast Fell into the abyss');
}
