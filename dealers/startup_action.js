hidePrice();
hideQuantity();
// Set read-only fields and load dealer data.
var mnth = ['AUG', 'SEP', 'OCT', 'NOV', 'DEC', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'TOT'];
var roFld = ['_LY', '_TY', '_FC'];
//var year = (new Date).getFullYear();
//get the current model year bc in 8/15 the model year is 16, not 15.
//var year = loadByListName('Current_Model_Year')[0].MODEL_YEAR;
window.year = '2025';

//reset the form fields so that admins can change dealers without the
//totals continuing to add up. Also clears previous dealers
//forecasts when the next dealer doesn't have forecast data for that year.

reset('FORM' + year);
reset('FORM' + (year - 1));
reset('FORM' + (year - 2));
reset('FORM' + (year - 3));
reset('REP_TOOLS_' + (year));
reset('ADD_QUESTIONS');
reset('SIG');
reset('TERMS');
reset('SIGNED_BY');
$('div[data-ref="SIGNED_BY/SIGIMG"]').empty();

window.eosNo = "";

// Clear signature box
clearCanvas();

//if (getValue('PROFILE', 'ROLE') !== 'SUPERUSER' && getValue('PROFILE', 'TYPE') !== 'SALESREP' && getValue('PROFILE','ROLE') !== 'INSIDESALESMGR') {
if (getValue('PROFILE', 'TYPE') === 'DEALER') {
    console.log('User is not an Admin, RSM or Inside Sales.');
    eosNo = getValue('EOS', 'CUSTOMER_NO');
    setValue('CUSTSERV', 'FIND', eosNo);
    var eosCustName = getValue('EOS', 'COMPANY');
    window.eosNoTrimmed = eosNo.replace(/^(0+)/g, '');

    var dealerInfo = loadByListName('dealers', "WHERE  DlrNo = '" + pad(eosNoTrimmed, 8) + "'");
    if (dealerInfo.length) {
        var dealership = dealerInfo[0].DealerDBA;
        setValue('DLR_INFO', 'DLR_DBA', dealership);
        setValue('DLR_INFO', 'CONT_NAME', dealerInfo[0].Contact);
        setValue('DLR_INFO', 'ADD1', dealerInfo[0].Add1);
        setValue('DLR_INFO', 'CITY', dealerInfo[0].City);
        setValue('DLR_INFO', 'STATE', dealerInfo[0].State);
        setValue('DLR_INFO', 'ZIP', dealerInfo[0].Zip);
        setValue('DLR_INFO', 'PHONE', dealerInfo[0].PhoneNo);
        setValue('DLR_INFO', 'WEB', dealerInfo[0].Web_URL);
    }
    setValue('FORM' + year, 'DEALERNAME', eosCustName);
    setValue('REP_TOOLS_' + year, 'DEALERNAME', eosCustName);
    signatureRec = [];
    signatureRec = loadByListName('Dealer_Planner_Sig_Data', 'LIST/DEALER_NO[="' + eosNoTrimmed + '"] & LIST/FORECAST_MY[= "' + year + '"]');
    reset('HIDE', 'SIG_DATA');
    if (signatureRec.length > 0) {
        signature = signatureRec[0].SIG_DATA;
        setValue('HIDE', 'SIG_DATA', signature);
        //loadCanvas(signature);

        $('#sigimg').remove();  //keep the images from duplicating
        url = signature;
        path = '<img src="' + url + '" style="padding: 0px; border: 0px; box-shadow: 0px" class="thumbnail" crossorigin="anonymous">';
        output = '<div id=sigimg>' + path + '</div>';
        $('div[data-ref="SIGNED_BY/SIGIMG"]').append(output);

    }
} else {
    console.log('User is an Admin, RSM or Inside Sales Mgr');
    eosNo = getValue('CUSTSERV', 'FIND').toString();
    eosNoTrimmed = eosNo.replace(/^(0+)/g, '');

    var dealerInfo = loadByListName('dealers', "WHERE  DlrNo = '" + pad(eosNoTrimmed, 8) + "'");

    if (dealerInfo.length) {
        var dealership = dealerInfo[0].DealerDBA;
        setValue('DLR_INFO', 'DLR_DBA', dealership);
        setValue('DLR_INFO', 'CONT_NAME', dealerInfo[0].Contact);
        setValue('DLR_INFO', 'ADD1', dealerInfo[0].Add1);
        setValue('DLR_INFO', 'CITY', dealerInfo[0].City);
        setValue('DLR_INFO', 'STATE', dealerInfo[0].State);
        setValue('DLR_INFO', 'ZIP', dealerInfo[0].Zip);
        setValue('DLR_INFO', 'PHONE', dealerInfo[0].PhoneNo);
        setValue('DLR_INFO', 'WEB', dealerInfo[0].Web_URL);
    }

    if (eosNo !== 'false') {
        var eosCustName = (loadByListName('dealers', "WHERE DlrNo = '" + eosNo + "'")[0] || {}).DealerName;
        setValue('FORM' + year, 'DEALERNAME', eosCustName);
        setValue('REP_TOOLS_' + year, 'DEALERNAME', eosCustName);
        signatureRec = loadByListName('Dealer_Planner_Sig_Data', 'LIST/DEALER_NO[="' + eosNoTrimmed + '"] & LIST/FORECAST_MY[= "' + year + '"]');
        console.log(signatureRec);
        reset('HIDE', 'SIG_DATA');
        if (signatureRec.length > 0) {
            signature = signatureRec[0].SIG_DATA;
            setValue('HIDE', 'SIG_DATA', signature);
            //loadCanvas(signature); //had a problem with this because the signature disappears on mouseover

            $('#sigimg').remove();  //keep the images from duplicating
            if (signature.length > 0) {
                url = signature;
                path = '<img src="' + url + '" style="padding: 0px; border: 0px; box-shadow: 0px" class="thumbnail" crossorigin="anonymous">';
                output = '<div id=sigimg>' + path + '</div>';
                $('div[data-ref="SIGNED_BY/SIGIMG"]').append(output);
            }
        }
    }
}

eosNopadded = pad(eosNo, 12);
//dealer planner boat units
console.log('eosNopadded', eosNopadded);

actualboatunits = sStatement('SEL_ACTUAL_UNITS', ([eosNopadded]));
opOrd = sStatement('SEL_OPEN_ORDERS', ([eosNoTrimmed]));
forecast = sStatement('SEL_FORECAST', ([eosNoTrimmed]));

//Grep the full table results down to only the years you want.
forecast_TY = $.grep(forecast, function (forecastExtract) { return ((forecastExtract.FORECAST_MY == year)); });
forecast_LY = $.grep(forecast, function (forecastExtract) { return ((forecastExtract.FORECAST_MY == year - 1)); });
forecast_back2years = $.grep(forecast, function (forecastExtract) { return ((forecastExtract.FORECAST_MY == year - 2)); });
forecast_back3years = $.grep(forecast, function (forecastExtract) { return ((forecastExtract.FORECAST_MY == year - 3)); });
actualboatunits_TY = $.grep(actualboatunits, function (actualboatunitsExtract) { return ((actualboatunitsExtract.model_year == year)); });
actualboatunits_LY = $.grep(actualboatunits, function (actualboatunitsExtract) { return ((actualboatunitsExtract.model_year == year - 1)); });
actualboatunits_back2years = $.grep(actualboatunits, function (actualboatunitsExtract) { return ((actualboatunitsExtract.model_year == year - 2)); });
actualboatunits_back3years = $.grep(actualboatunits, function (actualboatunitsExtract) { return ((actualboatunitsExtract.model_year == year - 3)); });

//console.log('actualboatunits');
//console.table(actualboatunits);
//console.log('forecast_TY');
//console.table(forecast_TY);
//console.log('forecast_LY');
//console.table(forecast_LY);
//console.table(forecast_back2years);
//console.log('actual_TY');
//console.table(actualboatunits_TY);
//console.log('actual_LY');
//console.table(actualboatunits_LY);
//console.table(actualboatunits_back2years);

// Load existing planner settings.

if (opOrd.length > 0) {
    setValue('FORM' + year, 'OPEN', opOrd[0].Boat_Qty);
    setValue('REP_TOOLS_' + year, 'OPEN', opOrd[0].Boat_Qty);
}

if (eosNo !== 'false' && forecast.length === 0) {
    eosPopup('No existing forecast records exist for this dealership.');
}

// Load data to read only fields.
$.each(mnth, function (monI, mCode) {
    console.log("monI", monI + 1);
    console.log(mCode);
    if (forecast_TY.length > 0) {
        //current year forecast population.
        setValue('FORM' + year, mCode + '_FC', forecast_TY[0]['period_' + (monI + 1) + '_fc']);
        setValue('REP_TOOLS_' + year, mCode + '_FC', forecast_TY[0]['period_' + (monI + 1) + '_fc']);
        setValue('REP_TOOLS_' + year, mCode + '_REP_FC', forecast_TY[0]['period_' + (monI + 1) + '_rep_fc']);

        if (forecast_TY[0].SIGNED_BY !== '1') { setValue('SIGNED_BY', 'SIGNED_BY', forecast_TY[0].SIGNED_BY); }
        if (forecast_TY[0].DATE_SIGNED !== '1') { setValue('SIGNED_BY', 'DATE_SIGNED', forecast_TY[0].DATE_SIGNED); }
        setValue('ADD_QUESTIONS', 'ANT_VOL_DISC', forecast_TY[0].ant_vol_disc);
        setValue('ADD_QUESTIONS', 'COMMENTS', forecast_TY[0].comments);

        //console.log('Keri', forecast_TY[0].terms);
        if (forecast_TY[0].terms === '1') { setAnswer('TERMS', 'TERMS'); }

        setValue('HIDE', 'REPLOCKED', forecast_TY[0].locked);
        //Lock out the save button if they shouldn't have access to it
        if (forecast_TY[0].locked === '1') {
            $('button[data-ref="BTN/DEALERLOCK"]').hide();
            if (getValue('PROFILE', 'ROLE') !== 'SUPERUSER' && getValue('PROFILE', 'TYPE') !== 'SALESREP') {
                //This is where we need to disable teh save button
                $('button[data-ref="BTN/SAVE"]').hide();
                //Set the fields as read only
                //'FORM' + year
                $('input[data-ref="FORM_' + year + '/AUG_FC"]').attr('readonly', 'true');
                $('input[data-ref="FORM_' + year + '/SEP_FC"]').attr('readonly', 'true');
                $('input[data-ref="FORM_' + year + '/OCT_FC"]').attr('readonly', 'true');
                $('input[data-ref="FORM_' + year + '/NOV_FC"]').attr('readonly', 'true');
                $('input[data-ref="FORM_' + year + '/DEC_FC"]').attr('readonly', 'true');
                $('input[data-ref="FORM_' + year + '/JAN_FC"]').attr('readonly', 'true');
                $('input[data-ref="FORM_' + year + '/FEB_FC"]').attr('readonly', 'true');
                $('input[data-ref="FORM_' + year + '/MAR_FC"]').attr('readonly', 'true');
                $('input[data-ref="FORM_' + year + '/APR_FC"]').attr('readonly', 'true');
                $('input[data-ref="FORM_' + year + '/MAY_FC"]').attr('readonly', 'true');
                $('input[data-ref="FORM_' + year + '/JUN_FC"]').attr('readonly', 'true');
                $('input[data-ref="FORM_' + year + '/JUL_FC"]').attr('readonly', 'true');
            }
        } else {
            $('button[data-ref="BTN/DEALERUNLOCK"]').hide();
        }

        setValue('ADD_QUESTIONS', 'FP_SOURCE', forecast_TY[0].floorplan_source);

    }

    if (mCode !== 'TOT') {
        //set boat unit fields
        //always test for length first or these bomb when there is no data for older years.

        if (actualboatunits_TY.length !== 0) {
            setValue('FORM' + year, mCode + '_TY', actualboatunits_TY[0]['period_' + (monI + 1) + '_units']);
        }

        if (actualboatunits_LY.length !== 0) {
            setValue('FORM' + year, mCode + '_LY', actualboatunits_LY[0]['period_' + (monI + 1) + '_units']);
            setValue('FORM' + (year - 1), mCode + '_TY', actualboatunits_LY[0]['period_' + (monI + 1) + '_units']);
        }
        if (actualboatunits_back2years.length !== 0) { setValue('FORM' + (year - 2), mCode + '_TY', actualboatunits_back2years[0]['period_' + (monI + 1) + '_units']); }
        if (actualboatunits_back3years.length !== 0) { setValue('FORM' + (year - 3), mCode + '_TY', actualboatunits_back3years[0]['period_' + (monI + 1) + '_units']); }
        //set forecast fields and totals
        if (forecast_LY.length !== 0) {
            setValue('FORM' + (year - 1), mCode + '_FC', forecast_LY[0]['period_' + (monI + 1) + '_fc']);
            setValue('FORM' + (year - 1), 'TOT_FC', forecast_LY[0].TOT); //get the stored total
        }

        if (forecast_back2years.length !== 0) {
            setValue('FORM' + (year - 2), mCode + '_FC', forecast_back2years[0]['period_' + (monI + 1) + '_fc']);
            setValue('FORM' + (year - 2), 'TOT_FC', forecast_back2years[0].TOT);

        }
        if (forecast_back3years.length !== 0) {
            setValue('FORM' + (year - 3), mCode + '_FC', forecast_back3years[0]['period_' + (monI + 1) + '_fc']);
            setValue('FORM' + (year - 3), 'TOT_FC', forecast_back3years[0].TOT);
        }
    }
    $.each(roFld, function (i, suffix) {

        if (suffix == '_LY' || suffix == '_TY') {
            $('input[data-ref="FORM' + year + '/' + mCode + suffix + '"]').attr('readonly', true);
            $('input[data-ref="REP_TOOLS_' + year + '/' + mCode + suffix + '"]').attr('readonly', true);
            $('input[data-ref="FORM' + (year - 1) + '/' + mCode + suffix + '"]').attr('readonly', true);
            $('input[data-ref="FORM' + (year - 2) + '/' + mCode + suffix + '"]').attr('readonly', true);
            $('input[data-ref="FORM' + (year - 3) + '/' + mCode + suffix + '"]').attr('readonly', true);
        }
        //only disable the forecast fields for previous years.
        if (suffix == '_FC') {
            $('input[data-ref="REP_TOOLS_' + (year) + '/' + mCode + suffix + '"]').attr('readonly', true);
            $('input[data-ref="FORM' + (year - 1) + '/' + mCode + suffix + '"]').attr('readonly', true);
            $('input[data-ref="FORM' + (year - 2) + '/' + mCode + suffix + '"]').attr('readonly', true);
            $('input[data-ref="FORM' + (year - 3) + '/' + mCode + suffix + '"]').attr('readonly', true);
        }
    });

    $('input[data-ref="FORM' + year + '/TOT_FC' + '"]').attr('readonly', true);
    $('input[data-ref="REP_TOOLS_' + year + '/TOT_REP_FC' + '"]').attr('readonly', true);
    $('input[data-ref="FORM' + year + '/OPEN' + '"]').attr('readonly', true);
    $('input[data-ref="FORM' + year + '/DEALERNAME' + '"]').attr('readonly', true);
});

// Calculate totals.
years = [year, year - 1, year - 2, year - 3];
$.each(years, function (yInd, yr) {
    lyTot = 0;
    tyTot = 0;
    fcTot = 0;
    vals = getAnswers('FORM' + yr);
    //console.log(yr, vals);
    $.each(vals, function (qa, val) {
        obj = qa.split('/');
        ans = obj[1];
        val = Number(val);
        //console.log('This Year', ans, val);
        if (ans.substring(3, 6) == '_LY') {
            //console.log('Last Year', ans, val);
            lyTot += val;
        }
        if (ans.substring(3, 6) == '_TY') {
            ///console.log('This Year', ans, val);
            tyTot += val;
        }
        if (ans.substring(3, 6) == '_FC' && yr == year && ans != 'TOT_FC') { //only for the current year
            //console.log('This Year', ans, val);
            fcTot += val;
            //console.log('fcTot',fcTot);
        }
    });

    if (yr == year) {
        setValue('FORM' + yr, 'TOT_LY', lyTot);
        setValue('FORM' + yr, 'TOT_TY', tyTot);
        setValue('FORM' + yr, 'TOT_FC', fcTot);
        setValue('REP_TOOLS_' + yr, 'TOT_FC', fcTot);
    } else {
        setValue('FORM' + yr, 'TOT_TY', tyTot);
    }
});

// Calculate rep forecast total.
console.log('calculate rep total');
years = [year];
$.each(years, function (yInd, yr) {
    repfcTot = 0;
    vals = getAnswers('REP_TOOLS_' + yr);
    //console.log(yr, vals);
    $.each(vals, function (qa, val) {
        obj = qa.split('/');
        ans = obj[1];
        val = Number(val);
        //console.log('This Year', ans, val);
        //console.log(ans.substring(3, 10));

        if (ans.substring(3, 10) == '_REP_FC' && yr == year && ans != 'TOT_REP_FC') { //only for the current year
            //console.log('This Year', ans, val);
            repfcTot += val;
            //console.log('repfcTot',refcTot);
        }
    });

    if (yr == year) {
        setValue('REP_TOOLS_' + yr, 'TOT_REP_FC', repfcTot);
    }
});


function clearCanvas() {
    console.log('clear sig');
    if ($('#sig_panel').sketch()) {
        $('#sig_panel').sketch().clear();
    }
}

function loadCanvas(dataURL) {
    console.log('load sig');
    var canvas = document.getElementById('sig_panel');
    var context = canvas.getContext('2d');

    // load image from data url
    var imageObj = new Image();
    imageObj.onload = function () {
        context.drawImage(this, 0, 0);
    };

    imageObj.src = dataURL;
}
