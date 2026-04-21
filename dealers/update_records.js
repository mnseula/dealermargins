//rethink this if they aren't going to allow the dealers to save

//PROFILE / ROLE[= "INSIDESALESMGR"]#PROFILE / TYPE[= "SALESREP"]#PROFILE / GROUP[= "ADMIN"]#PROFILE / GROUP[= "MAINTENANCE"]#PROFILE / ROLE[= "OWNER"]#PROFILE / ROLE[= "ADMIN"]
console.log('Save Dealer Forecast');
var userRoleNow = getValue('PROFILE', 'ROLE');
var profileTypeNow = getValue('PROFILE', 'TYPE');

function isCanvasBlank(canvas) {
    return !canvas.getContext('2d')
        .getImageData(0, 0, canvas.width, canvas.height).data
        .some(channel => channel !== 0);
}

if (    (profileTypeNow === 'BEN' || profileTypeNow === 'SALESREP' || userRoleNow === 'ADMIN' || userRoleNow === 'OWNER')) {

    var mnth = ['AUG', 'SEP', 'OCT', 'NOV', 'DEC', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'TOT'];
    //var year = loadByListName('Current_Model_Year')[0].MODEL_YEAR;
    var year = '2025';

    //Sig save section;
    sigPanel = document.getElementById("sig_panel");
    var blankCanvas = isCanvasBlank(sigPanel);
    console.log('blankCanvas', blankCanvas);

    if (!blankCanvas) {
        var sig = sigPanel.toDataURL("image/png");
        setValue('HIDE', 'SIG_DATA', sig);
        var sigdata = [eosNoTrimmed, year, sig];
        // Remove existing record
        deleteByListName('Dealer_Planner_Sig_Data', 'LIST/DEALER_NO[="' + eosNoTrimmed + '"] & LIST/FORECAST_MY[="' + year + '"]');
        addByListName('Dealer_Planner_Sig_Data', sigdata);
    }
    //End of signature action


    //Give the dealer dropdown to users that should see it
    if (userRoleNow === 'SUPERUSER' || profileTypeNow === 'SALESREP' || userRoleNow === 'INSIDESALESMGR') {
        var dlrNo = getValue('CUSTSERV', 'FIND');
        var dlrName = getValue('CUSTSERV', 'DEALERNAME');
        dlrNoTrimmed = dlrNo.replace(/^(0+)/g, '');
        //console.log(dlrNo);
    }
    else {
        var dlrNo = getValue('EOS', 'CUSTOMER_NO');
        var dlrName = getValue('EOS', 'COMPANY');
        dlrNoTrimmed = dlrNo.replace(/^(0+)/g, '');
        //console.log(dlrNo);
    }
    //Load rep list
    var salesrep = loadByListName('dealers', "WHERE DlrNo= '" + pad(dlrNo, 8) + "'")[0].SalesPerson;
    //console.log(salesrep);

    //Calculate New Total for Current Year Forecast field.
    updatevalues = []; //store them as you add them up for the update command.
    fcTot = 0;
    $.each($('input[name^="FORM' + year + '/"][name$="_FC"][name!="FORM' + year + '/TOT_FC"]'), function (i, qa) {
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
    //console.log(updatevalues);
    setValue('FORM' + year, 'TOT_FC', fcTot);

    console.table(updatevalues);

    //Select forecast for this dealer and this year.  Check to see if there is one.
    //If so, update, if not insert.
    window.currentforecast = loadByListName('dealer_forecast_new', "WHERE DEALER_NO = '" + dlrNoTrimmed + "' AND FORECAST_MY= ' " + year + "'");
    //console.log(currentforecast);
    //end test for existence

    var signer = getValue('SIGNED_BY', 'SIGNED_BY');
    var dateSigned = getValue('SIGNED_BY', 'DATE_SIGNED');
    var ant_vol_disc = getValue('ADD_QUESTIONS', 'ANT_VOL_DISC'); if (ant_vol_disc === true) { ant_vol_disc = "" }
    var comments = getValue('ADD_QUESTIONS', 'COMMENTS'); if (comments === true) { comments = "" }
    //Set placeholder vars for the table update
    var terms = 0;
    var eu = 0;
    var privacy = 0;
    var locked = 0;
    if (hasAnswer('TERMS', 'TERMS')) { terms = 1; }
    if (hasAnswer('HIDE', 'REPLOCKED')) { locked = getValue('HIDE', 'REPLOCKED'); }

    var floorplan_source = getValue('ADD_QUESTIONS', 'FP_SOURCE'); if (floorplan_source === true) { floorplan_source = "" }

    if (signer.length === 0) { signer = ""; }
    if (dateSigned.length === 0) { dateSigned = ""; }

    console.log('Signed By: ', signer);

    var data = [dlrNoTrimmed, year, updatevalues[0], updatevalues[1], updatevalues[2], updatevalues[3], updatevalues[4],
        updatevalues[5], updatevalues[6], updatevalues[7], updatevalues[8], updatevalues[9], updatevalues[10],
        updatevalues[11], fcTot, signer, dateSigned, ant_vol_disc, comments, terms, floorplan_source, eu, privacy, locked];


    if (currentforecast.length !== 0) {
        console.log("There is a current forecast to update");
        sStatement('UPD_DLR_FORECAST', data);

        alert('Update completed for ' + dlrName + '.');
        reset('BTN', 'SAVE');
    }
    else {
        console.log("There is no forecast to update, must insert.");

        var data = [salesrep, dlrNoTrimmed, dlrName, year, updatevalues[0], updatevalues[1], updatevalues[2], updatevalues[3],
            updatevalues[4], updatevalues[5], updatevalues[6], updatevalues[7], updatevalues[8], updatevalues[9],
            updatevalues[10], updatevalues[11], fcTot, signer, dateSigned, ant_vol_disc, comments, terms, floorplan_source, eu, privacy];
        console.log(data);
        sStatement('INS_DLR_FORECAST', data);
        alert('Forecast Update completed for ' + dlrName + '.');
    }
    reset('BTN', 'SAVE');
}
//It needs to be completed first
else { eosPopup('Please agree to the the terms and enter the name and date signed.'); }

setValue('REP_TOOLS_' + year, 'AUG_FC', getValue('FORM' + year, 'AUG_FC'));
setValue('REP_TOOLS_' + year, 'SEP_FC', getValue('FORM' + year, 'SEP_FC'));
setValue('REP_TOOLS_' + year, 'OCT_FC', getValue('FORM' + year, 'OCT_FC'));
setValue('REP_TOOLS_' + year, 'NOV_FC', getValue('FORM' + year, 'NOV_FC'));
setValue('REP_TOOLS_' + year, 'DEC_FC', getValue('FORM' + year, 'DEC_FC'));
setValue('REP_TOOLS_' + year, 'JAN_FC', getValue('FORM' + year, 'JAN_FC'));
setValue('REP_TOOLS_' + year, 'FEB_FC', getValue('FORM' + year, 'FEB_FC'));
setValue('REP_TOOLS_' + year, 'MAR_FC', getValue('FORM' + year, 'MAR_FC'));
setValue('REP_TOOLS_' + year, 'APR_FC', getValue('FORM' + year, 'APR_FC'));
setValue('REP_TOOLS_' + year, 'MAY_FC', getValue('FORM' + year, 'MAY_FC'));
setValue('REP_TOOLS_' + year, 'JUN_FC', getValue('FORM' + year, 'JUN_FC'));
setValue('REP_TOOLS_' + year, 'JUL_FC', getValue('FORM' + year, 'JUL_FC'));
setValue('REP_TOOLS_' + year, 'TOT_FC', getValue('FORM' + year, 'TOT_FC'));
