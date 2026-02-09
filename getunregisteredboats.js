console.debug('STARTUP Get Unregistered Boats');
window.prodpicsPath = 'https://prodpics.s3.amazonaws.com/';

$('div[data-ref="' + 'PRODPICS/PRODPICS"]').empty();
$('button[data-ref="' + 'DOWNLOADS/DOWNLOADALL"]').hide();


dealerDropdown = $.parseJSON(decodeURIComponent(sessionStorage.arwing3)).DLR_DD;
if (dealerDropdown !== '') {
    ddButtons = '     <button id="filter_boats">Search</button>'; //+
    //'     <button id="show_all">Show All</button>';
} else {
    ddButtons = '';
    var dlrno = window[profile].DEALER_NO;
    setValue('DLR', 'DLR_NO', dlrno);
    buildTable(dlrno, dlrno);
    bindSelect();
}

$('[data-ref="BOATS/DLRS"]').append(
    '<left>' +
    dealerDropdown + ddButtons +
    '</left>'
);

// Dealer Select / Search Button
$('#filter_boats').on('click', function () {

    var dlrno = Number($('#dealer_select').val());
    setValue('DLR', 'DLR_NO', dlrno);
    //});

    //var dlrno = '000000551820';
    var dlrnoClean = dlrno;
    dlrno = pad(dlrno, 12);
    buildTable(dlrno, dlrnoClean);
    bindSelect();
}); //end of on click event


function bindSelect() {
    $('#dealerBoats').on('click', '.selectBoat', function () {
        $('div[data-ref="' + 'PRODPICS/PRODPICS"]').empty();
        //New clearing for changing dealers
        $('div[data-ref="BOATS/PRODPICSZIP"]').empty();
        $('button[data-ref="' + 'DOWNLOADS/DOWNLOADALL"]').hide();
        $('div[data-ref="OPTIONS/OPTIONS"]').children('div').remove();
        $('div[data-ref="SPECS/SPECS"]').children('div').remove();
        reset('PRICING');

        reset('BOAT_INFO');
        //reset('BOAT_INFO','HULL_NO');
        reset('DEALER_INSTALLED_OPTIONS');
        reset('DEALER_QUESTIONS');
        reset('DLR');

        if (dealerDropdown === '') {
            var dlrno = window[profile].DEALER_NO;
            setValue('DLR', 'DLR_NO', dlrno);
        } else {
            var dlrno = Number($('#dealer_select').val());
            setValue('DLR', 'DLR_NO', dlrno);
        }

        reset('DLR2');
        reset('PRINT_PHOTO');
        reset('MARGINS');
        reset('FREIGHTPREP');
        reset('EXTRAS');
        reset('SPECIAL_PRICING');
        reset('PRINT_SPECIAL_PRICE');
        window.SN = $(this).attr('id');
        console.log('Selected serial number is ' + SN);
        setValue('BOAT_INFO', 'HULL_NO', SN);
        setAnswer('FILTER', 'APPLIED');
        $('[class="nav sets nav-tabs"]:eq(0)').find('a:eq(1)').click(); //click window sticker information tab


        setAnswer('PRICING_TYPE', 'NO_PRICES');
        window.boattable = [];
        window.serial = getValue('BOAT_INFO', 'HULL_NO');
        window.freight = 0;
        window.prep = 0;

        loadPreviousSticker(serial);

        window.model_year = serial.substring(serial.length - 2);

        var snmRec = sStatement('SEL_ONE_SER_NO_MST', ([serial]));
        var snmInvoiceNo = snmRec[0].InvoiceNo;
        var boatinvoiceno = snmInvoiceNo; //boatmodel[0].InvoiceNo;
        var engineRec = sStatement('SEL_ONE_ENG_SER_NO_MST', ([serial]));

        if (engineRec.length > 0) {
            console.log('engineRec is ', engineRec);
            var engineERPNo = engineRec[0].ERP_OrderNo;
            //console.log('engineERPNo', engineERPNo);
            var enginebrand = engineRec[0].EngineBrand;
        } else {
            var engineERPNo = '';
        }

        setValue('BOAT_INFO', 'BOAT_INVOICE_NO', boatinvoiceno);

        loadPackagePricing(model_year, serial, snmInvoiceNo, engineERPNo);

        if (model === "22GFSDN") { model = "22GFSAPGDN"; }
        if (model === "22GSDN") { model = "22GSAPGDN"; }

        setValue('DLR', 'PRC_TYPE', boatpricingtype);
        //get the MSRP of the boat from the package pricing list.
        console.log('Engine Brand: ', enginebrand);

            if (enginebrand !== undefined && enginebrand.length > 0 && model.indexOf('IO') == -1) {
            if (enginebrand === 'MERCURY ENGINES' || enginebrand === 'MERCURY DB ENGIN' || enginebrand === 'MERCUR DB ENGIN' || enginebrand === '2B547667' || enginebrand === 'Mercury OB') { boatpkgitemno = 'MercPKG'; }
            else if (enginebrand === 'YAMAHA ENGINES' || enginebrand === 'YAMAHA ENGINE' || enginebrand === 'YAMAHA  DB ENGIN' || enginebrand === '63PX 1206969' || enginebrand === '63PX 1207669' || enginebrand === '63PX 1207662' || enginebrand === 'Yamaha OB') { boatpkgitemno = 'YamahaPKG'; }
            else if (enginebrand === 'HONDA ENGINES' || enginebrand === 'HONDA ENGINE' || enginebrand === 'ENGINE DB HONDA') { boatpkgitemno = 'HondaPKG'; }
            else if (enginebrand === 'SUZUKI ENGINES' || enginebrand === 'SUZUKI ENGINE' || enginebrand === 'DB SUZUKI ENGIN' || enginebrand === 'Suzuki OB') { boatpkgitemno = 'SuzukiPKG'; }
            else if (enginebrand === 'BOMBARDIER ENGINES' || enginebrand === 'EVINRUDE ENGINES' || enginebrand === 'EVINRUDE ENGINE' || enginebrand === 'Bombardier' || enginebrand === 'BMC ENGINES' || enginebrand === 'BOMB DB ENGIN') { boatpkgitemno = 'BombPKG'; }
            else if (enginebrand === 'TORQUEEDO ENGINES' || enginebrand === 'TORQUEEDO' || enginebrand === 'TORQEEDO' || enginebrand === 'TORQEEDO ENGINES' || enginebrand === 'ELECTRIC ENGINE') { boatpkgitemno = 'TorqPKG'; }
            else if (enginebrand === 'MINNKOTA ENGINES' || enginebrand === 'MINNKOTA') { boatpkgitemno = 'MinnKotaPKG'; }
            console.debug('boatpkgitemno is ', boatpkgitemno);
        }
        else if (model.indexOf('IO') > -1) {
            if (enginebrand === 'VOLVO I/O') { boatpkgitemno = model + 'V'; }
            else if (enginebrand === 'MERCURY I/O' || enginebrand === 'MERCRUISER I/O') {
                boatpkgitemno = model + 'M';
                console.log('Keri 128');
                //console.log('boatpkgitemno is ', boatpkgitemno);
            }
            else {
                //ZS Added this 5/31/2024... IO boat did not have engine.
                boatpkgitemno = '';
            }
        } else {
            boatpkgitemno = 'nopkg';
            console.debug('boatpkgitemno is ', boatpkgitemno);
        }

        console.log('boatpkgitemno is ', boatpkgitemno);
        console.log(model);
        window.pkgmsrp = '0';

        if (boatpricingtype !== 'REG' && model.indexOf('IO') == -1 && boatpkgitemno !== undefined) {
            var pkgmsrprec = $.grep(bpp, function (x) {
                return x.Model === model && x.Part === boatpkgitemno;
            });
        }
        console.log('Keri 139');
        if (boatpricingtype !== 'REG' && model.indexOf('IO') == -1 && boatpkgitemno !== undefined && pkgmsrprec.length > 0) {
        //if (pkgmsrprec.length > 0) {
            window.pkgmsrp = pkgmsrprec[0].price_MSRP;
        }

        if (pkgmsrp === undefined) { pkgmsrp = 0; }
        setValue('DLR', 'PKGMSRP', pkgmsrp);

        //get price type descriptions

        var priceLine = '';
        if (boatpricingtype == 'REG') { priceLine = 'REG'; }

        if (boatYear < 21) {
            if ((boatpricingtype === 'PP' || boatpricingtype === 'PPD' || boatpricingtype === 'SV') && pkgmsrp === 0) { priceLine = boatpricingtype + '_NO_MSRP'; }
            if ((boatpricingtype === 'PP' || boatpricingtype === 'PPD' || boatpricingtype === 'SV') && pkgmsrp !== 0) { priceLine = boatpricingtype + '_MSRP'; }
        }
        else {
            priceLine = boatpricingtype;
        }

        var PriceDescLine = $.grep(priceDesc, function (x) { return x.TYPE == 'LONG_DESC'; });
        var sPriceLine = $.grep(priceDesc, function (z) { return z.TYPE == 'SALE'; });
        var msPriceLine = $.grep(priceDesc, function (y) { return y.TYPE == 'MSRP'; });
        console.log('sPriceLine is ', sPriceLine);
        console.log('msPriceLine is ', msPriceLine);
        console.log('Price Desc is ', PriceDescLine);

        setValue('PRC_DESC', 'PRC_DESC_SALE', sPriceLine[0][priceLine]);
        setValue('PRC_DESC', 'PRC_DESC_MSRP', msPriceLine[0][priceLine]);
        setValue('PRC_DESC', 'PTYPE_DESC', PriceDescLine[0][priceLine]);

        changeLabel('PRC_DESC', 'PRC_DESC_SALE', sPriceLine[0][priceLine]);
        changeLabel('PRC_DESC', 'PRC_DESC_MSRP', msPriceLine[0][priceLine]);
        changeLabel('PRC_DESC', 'PTYPE_DESC', PriceDescLine[0][priceLine]);

        // Remove number from model.
        window.realmodel = model;
        model = model.replace(/\d+/g, '');

        console.log('series', series);
        setValue('DLR', 'SERIES', series);

        if(previoussticker.length === 0){
        applyDealerMargins();
        }

        var engineinvoiceno = "";
        var perfpkgpartno = "";

        //getMargins();

        stockno = getValue('DEALER_QUESTIONS', 'STOCK_NO');

/////////////////////////////////////////////////////////////////////////////
       if(serialYear < 21){
        Calculate();
       }else{
           Calculate2021();
       }

        // CPQ FIX: For CPQ boats, use full model name. For legacy boats, strip last 2 chars (year code)
        if (window.isCPQBoat) {
            console.log('CPQ boat detected - using full model name:', realmodel);
            setValue('BOAT_INFO', 'BOAT_MODEL', realmodel);

            // CPQ: Load LHS specification data from MySQL database
            console.log('===== CPQ LHS DATA LOAD =====');

            var cpqYear = 2025; // CPQ boats are 2025 model year
            var cpqHullNo = serial; // Hull number to get specific performance package

            console.log('Calling GET_CPQ_LHS_DATA with params:');
            console.log('  @PARAM1 (model_id):', realmodel);
            console.log('  @PARAM2 (year):', cpqYear);
            console.log('  @PARAM3 (hull_no):', cpqHullNo);

            try {
                var cpqLhsData = sStatement('GET_CPQ_LHS_DATA', [realmodel, cpqYear, cpqHullNo]);
                console.log('CPQ LHS Data returned:', cpqLhsData);
                console.log('Type:', typeof cpqLhsData);
                console.log('Is array?', Array.isArray(cpqLhsData));

                if (cpqLhsData && cpqLhsData.length > 0) {
                    console.log('✅ SUCCESS: Got LHS data for model', realmodel, 'hull', cpqHullNo);
                    console.log('Performance Package:', cpqLhsData[0].perf_package_id || 'N/A');
                    console.log('Data:', cpqLhsData[0]);

                    // Store in window variable for print.js to use
                    window.cpqLhsData = cpqLhsData[0];
                    console.log('CPQ LHS data stored in window.cpqLhsData');
                } else {
                    console.warn('⚠️ No LHS data returned for model', realmodel);
                }
            } catch (error) {
                console.error('❌ Error loading CPQ LHS data:', error);
                console.error('Error details:', JSON.stringify(error));
            }
            console.log('===== END CPQ LHS DATA LOAD =====');

            // CPQ: Load standard features from MySQL database
            console.log('===== CPQ STANDARD FEATURES LOAD =====');

            console.log('Calling GET_CPQ_STANDARD_FEATURES with params:');
            console.log('  @PARAM1 (model_id):', realmodel);
            console.log('  @PARAM2 (year):', cpqYear);

            try {
                var cpqStandardFeatures = sStatement('GET_CPQ_STANDARD_FEATURES', [realmodel, cpqYear]);
                console.log('CPQ Standard Features returned:', cpqStandardFeatures);
                console.log('Type:', typeof cpqStandardFeatures);
                console.log('Is array?', Array.isArray(cpqStandardFeatures));

                // DEBUG: Log the structure to see what we're actually getting
                if (cpqStandardFeatures && typeof cpqStandardFeatures === 'object') {
                    console.log('Object keys:', Object.keys(cpqStandardFeatures));
                    console.log('First few entries:', Object.keys(cpqStandardFeatures).slice(0, 3));
                    if (Object.keys(cpqStandardFeatures).length > 0) {
                        var firstKey = Object.keys(cpqStandardFeatures)[0];
                        console.log('First entry [' + firstKey + ']:', cpqStandardFeatures[firstKey]);
                    }
                }

                // Convert object to array if needed (sStatement might return object with numeric keys)
                var featuresArray = cpqStandardFeatures;
                if (cpqStandardFeatures && !Array.isArray(cpqStandardFeatures) && typeof cpqStandardFeatures === 'object') {
                    console.log('Converting object to array...');
                    featuresArray = Object.values(cpqStandardFeatures);
                    console.log('Converted array length:', featuresArray.length);
                }

                console.log('Features array length:', featuresArray ? featuresArray.length : 0);

                if (featuresArray && featuresArray.length > 0) {
                    console.log('✅ SUCCESS: Got', featuresArray.length, 'standard features for model', realmodel);

                    // Group features by area
                    window.cpqStandardFeatures = {
                        'Interior Features': [],
                        'Exterior Features': [],
                        'Console Features': [],
                        'Warranty': []
                    };

                    featuresArray.forEach(function(feature) {
                        if (window.cpqStandardFeatures[feature.area]) {
                            window.cpqStandardFeatures[feature.area].push(feature.description);
                        }
                    });

                    console.log('CPQ Standard Features grouped by area:');
                    console.log('  Interior:', window.cpqStandardFeatures['Interior Features'].length);
                    console.log('  Exterior:', window.cpqStandardFeatures['Exterior Features'].length);
                    console.log('  Console:', window.cpqStandardFeatures['Console Features'].length);
                    console.log('  Warranty:', window.cpqStandardFeatures['Warranty'].length);
                } else {
                    console.warn('⚠️ No standard features returned for model', realmodel);
                    window.cpqStandardFeatures = null;
                }
            } catch (error) {
                console.error('❌ Error loading CPQ standard features:', error);
                console.error('Error details:', JSON.stringify(error));
                window.cpqStandardFeatures = null;
            }
            console.log('===== END CPQ STANDARD FEATURES LOAD =====');
        } else {
            console.log('Legacy boat detected - stripping last 2 chars from:', realmodel);
            setValue('BOAT_INFO', 'BOAT_MODEL', realmodel.substring(0, realmodel.length - 2));
        }
        setValue('BOAT_INFO', 'BOAT_REAL_MODEL', realmodel);
        setValue('BOAT_INFO', 'HULL_NO', serial);
        setValue('BOAT_INFO', 'BOAT_INVOICE_NO', boatinvoiceno);
        setValue('BOAT_INFO', 'ENG_INVOICE_NO', engineinvoiceno);
        setValue('BOAT_INFO', 'PERF_PKG_ON_BOAT', perfpkgpartno);
        $('input[data-ref="BOAT_INFO/BOAT_MODEL"]').attr('readonly', 'true');
        $('input[data-ref="BOAT_INFO/BOAT_REAL_MODEL"]').attr('readonly', 'true');
        $('input[data-ref="BOAT_INFO/HULL_NO"]').attr('readonly', 'true');
        $('input[data-ref="BOAT_INFO/BOAT_INVOICE_NO"]').attr('readonly', 'true');
        $('input[data-ref="BOAT_INFO/ENG_INVOICE_NO"]').attr('readonly', 'true');
        $('input[data-ref="BOAT_INFO/STD_PERF_PKG"]').attr('readonly', 'true');
        $('input[data-ref="BOAT_INFO/PERF_PKG_ON_BOAT"]').attr('readonly', 'true');
        $('input[data-ref="DEALER_QUESTIONS/PHOTO_URL"]').attr('readonly', 'true');
        $('input[data-ref="DEALER_INSTALLED_OPTIONS/DIO_TOTAL"]').attr('readonly', 'true');
        //var standardsmatrixlist = 'standards_matrix' + '_20' + model_year;
        //var listid = getListID(standardsmatrixlist);
        //if(SN = 'ETWS8824J526')
        //{
            //perfpkgpartno = "914209"
        //}

        console.log(stndsMtrx);
        //get the perf pkg id for either the standard pkg or the purchased pkg
        if (perfpkgpartno === "") {
            console.log('no perf pkg on this boat');
            //look for the standard perf pkg if there isn't a different one on the boat
            window.defaultperfpkgid = "";
            // s99 = PP#4, s101 = PP#1, s102 = PP#2, s244 = 10 ft. wides PP#11, S247= 10ft wides PP #11
            if (typeof stndsMtrx !== 'undefined') {
                $.each(stndsMtrx, function (j) {
                    var part = stndsMtrx[j].STANDARD;
                    if (part === 'S99') { defaultperfpkgid = '4'; }
                    if (part === 'S101') { defaultperfpkgid = '1'; }
                    if (part === 'S102') { defaultperfpkgid = '2'; }
                    if (part === 'S309') { defaultperfpkgid = '12'; }
                    if (part === 'S312') { defaultperfpkgid = '16'; }
                    if (part === 'S244' || part === 'S247') { defaultperfpkgid = '11'; }
                });
            }
            setValue('BOAT_INFO', 'STD_PERF_PKG', defaultperfpkgid);
        } else {
            //it has a perf pkg, figure out the id so you can print just the perf specs for this boat.
            var defaultperfpkgidonboat = getUdpByPart(boatproductid, perfpkgpartno, 'PerfPkgID');
            if (defaultperfpkgidonboat === null) { //hit a snag where some parts weren't in the 2015 prod. Look in 16 if you can't find it.
                var defaultperfpkgidonboat = getUdpByPart('568974f2a9d29adf3e5ecfce', perfpkgpartno, 'PerfPkgID');
            }
            setValue('BOAT_INFO', 'STD_PERF_PKG', defaultperfpkgidonboat);
            //figure out how to get the perf pkg id from the perfpkgpartno via the udp that matches it.
        }

        $('#included').remove(); //delete the included table if it exists so that removing the engined doesn't make 2.

        GenerateBoatTable(boattable);

    });  //end of on click

} //end of bind




/*FUNCTIONS*/

//get info about the engine to lookup the default 25 or 50hp part for the boat pkg.
function buildTable(dlrno, dlrnoClean) {
    data = sStatement('WS_GET_UNREG_BOATS', [pad(dlrno, 12), dlrnoClean, pad(dlrnoClean, 8)]);
    //looping through this before elements are done to try to give this a head start

    for (var i in data) { SerNumberHasImages(data[i]['Boat_SerialNo'], data[i]['SerialModelYear'], data[i]['ProdNo']); }

    console.log('boats', data);

    var boat_table =
        '<table id="dealerBoats" border="1" style="width: 100%" cellpadding="4" cellspacing="1">' +
        '<thead>' +
        '   <tr>' +
        '       <td>Boat Serial Number</td>' +
        '       <td>Boat Model</td>' +
        // '<td>Dealer Name</td>' +
        '       <td>Panel Color</td>' +
        '       <td>Accent Panel</td>' +
        '       <td>Actions</td>';

    boat_table += '<td></td>';


    boat_table += '   </tr>' +
        '   <tr>' +
        '       <td><input type="text" value="" width: 100px;></td>' +
        '       <td><input type="text" value="" width: 100px;></td>' +
        '       <td><input type="text" value="" width: 100px;></td>' +
        '       <td><input type="text" value="" width: 100px;></td>' +
        '       <td><input type="text" value="" width: 100px;></td>';
    //Make the Empty TD header placeholder

    boat_table += '<td></td>';
    //}

    boat_table += '   </tr></thead><tbody>';

    for (var i in data) {
        boat_table +=
            '<tr>' +
            '<td>' + data[i]['Boat_SerialNo'] + '</td>' +
            '<td>' + data[i]['BoatDesc1'] + '</td>' +
            //'<td>' + data[i]['DealerName'] + '</td>' +
            '<td>' + data[i]['PanelColor'] + '</td>' +
            '<td>' + data[i]['AccentPanel'] + '</td>' +
            '<td style="text-align: center">' +
            '<span>' +
            '<a id="' + data[i]['Boat_SerialNo'] + '" href="#" class="selectBoat">' +
            '<span style="color: blue">[Select ' + data[i]['Boat_SerialNo'] + ']</span></a>&nbsp</td>';


        boat_table += '<td><div id="hasProductionImages_' + data[i]['Boat_SerialNo'] + '"></div></td>';
        boat_table += '</tr>';
    }

    boat_table += '</tbody></table>';

    $('div[data-ref="BOATS/UNREG"]').children('div').remove();
    $('div[data-ref="BOATS/UNREG"]').append(boat_table);
    //Looping through the array before the DB is actually drawn and it is just raw HTML here

    LoopCheckImagesArray();

    $('#dealerBoats').dataTable({
        "bSortCellsTop": true,
    });

    var table = $('#dealerBoats').DataTable();
    //Loops over every TD with the input box
    $('#dealerBoats td input').each(function (i, el) {
        console.log(i, el);
        var col = table.column(i);

        $(el).on('keyup change', function () {
            if (col.search() !== this.value) {
                col.search(this.value).draw();
            }
        });
    });

    $.each($('.text_filter'), function () {
        $(this).attr('class', 'text_filter search_init input-small');
    });
    //on every redraw lets make sure the images are there

    $('#dealerBoats').on('draw.dt', function () {
        LoopCheckImagesArray();
    });
}


// Assign ID to Upload Button
$('[class="btn btn-attach-upload btn-small btn-primary"]').attr('id', 'upload');

// On-click function.
$('#upload').on('click', function () {
    getUpload();
});

//DEBUGGING!
//console.error('pkgrowtotal_MS',pkgrowtotal_MS);
//console.error('boatrowtotal_MS',boatrowtotal_MS);
//console.error('enginerowtotal_MS',enginerowtotal_MS);
//console.error('prerigrowtotal_MS',prerigrowtotal_MS);
//console.error('rowstotal_MS',rowstotal_MS);
