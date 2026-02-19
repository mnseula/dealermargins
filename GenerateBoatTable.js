/*-------  Metadata -----
   *** Please do not touch this header ***

ID: 5f242378d4ecb36ef893c93a
NAME: Generate Table On Screen
CODE: GENERATE
RULE:
DOWNLOAD DATE: 2025-10-06T19:09:37.354Z

-------------------------*/

window.GenerateBoatTable = window.GenerateBoatTable || function (boattable) {
    console.log('Generate');

    // HTML escape function to prevent quote characters from breaking HTML
    function escapeHtml(text) {
        if (!text) return text;
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    if (hasAnswer('RMV_ENG', 'YES')) {
        var removeeng = '1';
    } else {
        var removeeng = '0';
    }

    window.table = "";
    var pkgrow = "";
    var boatrow = "";
    var baseboatrow = "";
    var enginerow = "";
    var prerigrow = "";
    var rows = "";

    //vars to keep running totals
    var pkgrowtotal_SP = 0;
    var boatrowtotal_SP = 0;
    var baseboatrowtotal_SP = 0;
    var enginerowtotal_SP = 0;
    var prerigrowtotal_SP = 0;
    var rowstotal_SP = 0;

    var pkgrowtotal_MS = 0;
    var boatrowtotal_MS = 0;
    var baseboatrowtotal_MS = 0;
    var enginerowtotal_MS = 0;
    var prerigrowtotal_MS = 0;
    var rowstotal_MS = 0;

    window.total_SP = 0;
    window.total_MS = 0;


    var additionalCharge = getValue('EXTRAS', 'ADD_CHARGE');
    if (additionalCharge === "") {
        additionalCharge = 0;
    }
    window.hasupgradedprerig = '0';
    prerigrow = '';

    // Sort boattable by MSRP (descending) then by Item Description (alphabetically)
    boattable.sort(function(a, b) {
        var msrpA = Number(a.MSRP) || 0;
        var msrpB = Number(b.MSRP) || 0;
        // Sort by MSRP descending (highest first)
        if (msrpB !== msrpA) {
            return msrpB - msrpA;
        }
        // Then by description alphabetically
        var descA = (a.ItemDesc1 || '').toUpperCase();
        var descB = (b.ItemDesc1 || '').toUpperCase();
        if (descA < descB) return -1;
        if (descA > descB) return 1;
        return 0;
    });

    $.each(boattable, function (i) {
        var desc = boattable[i].ItemDesc1;
        var itemno = boattable[i].ItemNo;
        var mct = boattable[i].MCT;
        var prodCategory = boattable[i].PC;
        var qty = boattable[i].Qty;
        var dc = Number(boattable[i].DealerCost).toFixed(2);
        var sp = Number(boattable[i].SalePrice).toFixed(2);
        var msrp = Number(boattable[i].MSRP).toFixed(2);
        var inc = boattable[i].Increment;

        if (mct === 'BOATPKG') {
            pkgrow = '<tr>' + '<td>' + escapeHtml(desc) + '</td><td>' + escapeHtml(itemno) + '</td><td align="center">1</td><td type = "DC" align="right">' + dc + '</td><td type= "MS" align="right">' + msrp + '</td><td type = "SP" align="right">' + sp + '</td></tr>';
            pkgrowtotal_SP = pkgrowtotal_SP + Number(sp);
            pkgrowtotal_MS = pkgrowtotal_MS + Number(msrp);
        } else if (mct === 'BOA' || mct === 'PONTOONS' || mct === 'Pontoon Boats OB') {
            // Base boat items - BOA for legacy boats, PONTOONS for CPQ boats
            console.log('DEBUG: Found base boat item:', itemno, desc, 'MCT:', mct, 'MSRP:', msrp);
            baseboatrow += '<tr>' + '<td>' + escapeHtml(desc) + '</td><td>' + escapeHtml(itemno) + '</td><td align="center">' + qty + '</td><td type="DC" align="right">' + dc + '</td><td type="MS" align="right">' + msrp + '</td><td type="SP" align="right">' + sp + '</td></tr>';
            baseboatrowtotal_SP = baseboatrowtotal_SP + Number(sp);
            baseboatrowtotal_MS = baseboatrowtotal_MS + Number(msrp);
        } else if (mct === 'ENGINES' && inc === '1') { //never gonna show the full price of an engine.
            enginerow += '<tr>' + '<td>' + escapeHtml(desc) + '</td><td>' + escapeHtml(itemno) + '</td><td align="center">' + qty + '</td><td type="DC" align="right">' + dc + '</td><td type="MS" align="right">' + msrp + '</td><td type="SP" align="right">' + sp + '</td></tr>';
            enginerowtotal_SP = enginerowtotal_SP + Number(sp);
            enginerowtotal_MS = enginerowtotal_MS + Number(msrp);
        } else if (mct === 'PRE-RIG' && inc === '1' && dc > 0) {
            window.hasupgradedprerig = '1';
            prerigrow += '<tr>' + '<td>' + escapeHtml(desc) + '</td><td>' + escapeHtml(itemno) + '</td><td align="center">' + qty + '</td><td type="DC" align="right">' + dc + '</td><td type="MS" align="right">' + msrp + '</td><td type="SP" align="right">' + sp + '</td></tr>';
            //if (prodCategory != 'PL1' && prodCategory != 'PL2' && prodCategory != 'PL3' && prodCategory != 'PL4' && prodCategory != 'PL5' && prodCategory != 'PL6') {
            prerigrowtotal_SP = prerigrowtotal_SP + Number(sp);
            prerigrowtotal_MS = prerigrowtotal_MS + Number(msrp);
            //}
            //At the end here is where we should do the skips
        } else if (mct === 'PRE-RIG' && inc !== '1' && dc > 0) {
            window.hasupgradedprerig = '0'
            //nsole.log('Has Upgraded Prerig ', hasupgradedprerig);
            prerigrow += '<tr>' + '<td>' + escapeHtml(desc) + '</td><td>' + escapeHtml(itemno) + '</td><td align="center">' + qty + '</td><td type="DC" align="right">' + dc + '</td><td type="MS" align="right">' + msrp + '</td><td type="SP" align="right">' + sp + '</td></tr>';
            //if (prodCategory != 'PL1' && prodCategory != 'PL2' && prodCategory != 'PL3' && prodCategory != 'PL4' && prodCategory != 'PL5' && prodCategory != 'PL6') {
            prerigrowtotal_SP = prerigrowtotal_SP + Number(sp);
            prerigrowtotal_MS = prerigrowtotal_MS + Number(msrp);
            //}
            //At the end here is where we should do the skips
        } else if (mct !== 'ENGINES' && inc !== '1' && mct !== 'PRE-RIG' && mct !== 'Disc - Selling') {
            rows = rows + '<tr>' + '<td>' + escapeHtml(desc) + '</td><td>' + escapeHtml(itemno) + '</td><td align="center">' + qty + '</td><td type="DC" align="right">' + dc + '</td><td type="MS" align="right">' + msrp + '</td><td type="SP" align="right">' + sp + '</td></tr>';
            rowstotal_SP = rowstotal_SP + Number(sp);
            rowstotal_MS = rowstotal_MS + Number(msrp);
        } else {
            console.log('Fell through the display!', boattable[i]);
            console.log('Note that prerigs do not display on their own like when the engines is on the boat because they are in the package');
        }
    });


    console.log('remove engine', removeeng);
    console.log('hasupgradedprerig', hasupgradedprerig);
    console.log('DEBUG: baseboatrow length:', baseboatrow.length);
    console.log('DEBUG: baseboatrowtotal_MS:', baseboatrowtotal_MS);
    console.log('DEBUG: baseboatrowtotal_SP:', baseboatrowtotal_SP);

    // CPQ FIX: Read boat package values from DLR2 table (set by Calculate2021.js)
    // This ensures CPQ boats include the base boat cost in totals
    console.log('DEBUG: Before reading DLR2 values');
    console.log('DEBUG: pkgrowtotal_SP from boattable loop =', pkgrowtotal_SP);
    console.log('DEBUG: pkgrowtotal_MS from boattable loop =', pkgrowtotal_MS);

    var pkgSaleRaw = getValue('DLR2', 'PKG_SALE');
    var pkgMsrpRaw = getValue('DLR2', 'PKG_MSRP');
    console.log('DEBUG: getValue DLR2/PKG_SALE returned:', pkgSaleRaw, 'type:', typeof pkgSaleRaw);
    console.log('DEBUG: getValue DLR2/PKG_MSRP returned:', pkgMsrpRaw, 'type:', typeof pkgMsrpRaw);

    var boatPackageSP = Number(pkgSaleRaw) || 0;
    var boatPackageMS = Number(pkgMsrpRaw) || 0;
    console.log('DEBUG: After Number conversion: SP =', boatPackageSP, ', MS =', boatPackageMS);

    if (boatPackageSP > 0 || boatPackageMS > 0) {
        console.log('CPQ BOAT - Using boat package from DLR2: SP=$' + boatPackageSP + ', MS=$' + boatPackageMS);
        // Override the row totals with values from DLR2
        pkgrowtotal_SP = boatPackageSP;
        pkgrowtotal_MS = boatPackageMS;
        console.log('DEBUG: Set pkgrowtotal_SP =', pkgrowtotal_SP);
        console.log('DEBUG: Set pkgrowtotal_MS =', pkgrowtotal_MS);
    } else {
        console.log('DEBUG: DLR2 values are 0 or undefined - using boattable totals');
    }

    if (removeeng === '0' && hasupgradedprerig !== '1') {
        if (boatpricingtype == 'SV') {
            if (pkgrowtotal_SP > 0) {
                // CPQ boat: pkgrowtotal already includes base boat from DLR2, don't add baseboatrowtotal again
                total_SP = pkgrowtotal_SP + enginerowtotal_SP + rowstotal_SP;
                total_MS = pkgrowtotal_MS + enginerowtotal_MS + rowstotal_MS;
                console.log('CPQ total_SP (without baseboatrow):', total_SP);
                console.log('CPQ total_MS (without baseboatrow):', total_MS);
            } else {
                // Legacy boat: include baseboatrowtotal as before
                total_SP = baseboatrowtotal_SP + boatrowtotal_SP + enginerowtotal_SP + rowstotal_SP;
                total_MS = baseboatrowtotal_MS + boatrowtotal_MS + enginerowtotal_MS + rowstotal_MS;
                console.log('Legacy total_SP', total_SP);
                console.log('Legacy total_MS', total_MS);
            }
            console.log('Pricing is SV, Upgraded Prerig - NO, removeengine - NO');
            table = '<table id = "included" border="1" cellpadding="3" cellspacing="1" style="width: 100%; margin:auto">' +
                '<tbody>' + '<tr>' + '<td colspan="1" style="text-align: left"><strong>Item Description</strong></td>' +
                '<td><strong>Item #</strong></td><td><strong>Qty</strong></td><td type="DC"><strong>Dealer Cost</strong></td><td type="MS"><strong>MSRP</strong></td><td type="SP"><strong>Sale Price</strong></td></tr>' + baseboatrow + pkgrow + enginerow + rows + '</tbody>' + '</table>';
        } else {
            table = '<table id = "included" border="1" cellpadding="3" cellspacing="1" style="width: 100%; margin:auto">' +
                '<tbody>' + '<tr>' + '<td colspan="1" style="text-align: left"><strong>Item Description</strong></td>' +
                '<td><strong>Item #</strong></td><td><strong>Qty</strong></td><td type="DC"><strong>Dealer Cost</strong></td><td type="MS"><strong>MSRP</strong></td><td type="SP"><strong>Sale Price</strong></td></tr>' + baseboatrow + pkgrow + enginerow + rows + '</tbody>' + '</table>';
            if (pkgrowtotal_SP > 0) {
                // CPQ boat: pkgrowtotal already includes base boat from DLR2, don't add baseboatrowtotal again
                total_SP = pkgrowtotal_SP + enginerowtotal_SP + rowstotal_SP;
                total_MS = pkgrowtotal_MS + enginerowtotal_MS + rowstotal_MS;
                console.log('CPQ total_SP (without baseboatrow):', total_SP);
                console.log('CPQ total_MS (without baseboatrow):', total_MS);
            } else {
                // Legacy boat: include baseboatrowtotal as before
                total_SP = baseboatrowtotal_SP + pkgrowtotal_SP + enginerowtotal_SP + rowstotal_SP;
                total_MS = baseboatrowtotal_MS + pkgrowtotal_MS + enginerowtotal_MS + rowstotal_MS;
                console.log('Legacy total_SP', total_SP);
                console.log('Legacy total_MS', total_MS);
            }
        }
        //console.log(table);
    } else if (removeeng === '0' && hasupgradedprerig === '1') {
        console.log('Engine Not removed but has upgraded prerig');
        table = '<table id = "included" border="1" cellpadding="3" cellspacing="1" style="width: 100%; margin:auto">' +
            '<tbody>' + '<tr>' + '<td colspan="1" style="text-align: left"><strong>Item Description</strong></td>' +
            '<td><strong>Item #</strong></td><td><strong>Qty</strong></td><td type="DC"><strong>Dealer Cost</strong></td><td type="MS"><strong>MSRP</strong></td><td type="SP"><strong>Sale Price</strong></td></tr>' + baseboatrow + pkgrow + enginerow + prerigrow + rows + '</tbody>' + '</table>';

        if (pkgrowtotal_SP > 0) {
            // CPQ boat: pkgrowtotal already includes base boat from DLR2, don't add baseboatrowtotal again
            total_SP = pkgrowtotal_SP + enginerowtotal_SP + prerigrowtotal_SP + rowstotal_SP;
            total_MS = pkgrowtotal_MS + enginerowtotal_MS + prerigrowtotal_MS + rowstotal_MS;
            console.log('CPQ with prerig total_SP (without baseboatrow):', total_SP);
            console.log('CPQ with prerig total_MS (without baseboatrow):', total_MS);
        } else {
            // Legacy boat: include baseboatrowtotal as before
            total_SP = baseboatrowtotal_SP + pkgrowtotal_SP + enginerowtotal_SP + prerigrowtotal_SP + rowstotal_SP;
            total_MS = baseboatrowtotal_MS + pkgrowtotal_MS + enginerowtotal_MS + prerigrowtotal_MS + rowstotal_MS;
            console.log('Legacy with prerig total_SP', total_SP);
            console.log('Legacy with prerig total_MS', total_MS);
        }
        console.log('pkgrowtotal_MS', pkgrowtotal_MS);
        console.log('enginerowtotal_MS', enginerowtotal_MS);
        console.log('prerigrowtotal_MS', prerigrowtotal_MS);
        console.log('rowstotal_MS', rowstotal_MS);
        //console.log(table);

    } else if (removeeng === '1') {
        console.log('Engine has been removed layout');
        table = '<table id = "included" border="1" cellpadding="3" cellspacing="1" style="width: 100%; margin:auto">' +
            '<tbody>' + '<tr>' + '<td colspan="1" style="text-align: left"><strong>Item Description</strong></td>' +
            '<td><strong>Item #</strong></td><td><strong>Qty</strong></td><td type="DC">Dealer Cost</td><td type="MS"><strong>MSRP</strong></td><td type="SP"><strong>Sale Price</strong</td></tr>' + baseboatrow + boatrow + prerigrow + rows + '</tbody>' + '</table>';

        // CPQ FIX: Use pkgrowtotal if set (CPQ boat), otherwise use boatrowtotal + baseboatrowtotal (legacy boat)
        if (pkgrowtotal_SP > 0) {
            console.log('DEBUG: Using pkgrowtotal (CPQ boat) for removed engine case');
            // CPQ boat: pkgrowtotal already includes base boat from DLR2, don't add baseboatrowtotal again
            total_SP = pkgrowtotal_SP + prerigrowtotal_SP + rowstotal_SP;
            total_MS = pkgrowtotal_MS + prerigrowtotal_MS + rowstotal_MS;
            console.log('CPQ removed engine total_SP (without baseboatrow):', total_SP);
            console.log('CPQ removed engine total_MS (without baseboatrow):', total_MS);
        } else {
            console.log('DEBUG: Using boatrowtotal + baseboatrowtotal (legacy boat) for removed engine case');
            // Legacy boat: include baseboatrowtotal as before
            total_SP = baseboatrowtotal_SP + boatrowtotal_SP + prerigrowtotal_SP + rowstotal_SP;
            total_MS = baseboatrowtotal_MS + boatrowtotal_MS + prerigrowtotal_MS + rowstotal_MS;
            console.log('Legacy removed engine total_SP', total_SP);
            console.log('Legacy removed engine total_MS', total_MS);
        }
        console.log('total_SP', total_SP);
        console.log('total_MS', total_MS);
    }


    //Append and Set and Make Read Only
    $('div[data-ref="INCLUDED/INCLUDED_OPTIONS"]').append(table);
    $('[type="SP"],[type="MS"],[type="DC"]').hide();
    //$('[type="DC"]').show();
    if (hasAnswer('PRICING_TYPE', 'MSRP')) {
        $('[type="MS"]').show();
    } else if (hasAnswer('PRICING_TYPE', 'SELLING_PRICE')) {
        $('[type="SP"]').show();
    } else if (hasAnswer('PRICING_TYPE', 'DEALER_COST')) {
        $('[type="DC"]').show();
    }
    //console.log('total sp', total_SP);
    //console.log('total ms', total_MS);
    dio = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_TOTAL');
    if (dio === "") {
        dio = 0;
    }
    var discount = getValue('EXTRAS', 'DISCOUNT');
    if (discount === "") {
        discount = 0;
    }
    var tax = getValue('EXTRAS', 'TAX_RATE');
    if (tax === "") {
        tax = 1;
    }

    //no dio totals
    setValue('EXTRAS', 'TOTAL_NO_DIO', Number(total_SP));
    setValue('EXTRAS', 'TOTAL_MS_NO_DIO', Number(total_MS));

    //Sale Price
    if (!hasAnswer('HIDE_DIO', 'YES')) {
        totalnotax = Number(total_SP) + Number(dio);// + Number(additionalCharge); //commented out 12-7-21
        setValue('EXTRAS', 'TOTAL', CurrencyFormat2(totalnotax));
    } else {
        totalnotax = Number(total_SP) - Number(discount); //don't add dios
        setValue('EXTRAS', 'TOTAL', CurrencyFormat2(totalnotax));
    }
    totaltax = (Number(totalnotax) * tax) / 100;
    displaytotal = Number(totalnotax) + Number(totaltax);
    console.log('total tax', totaltax);
    setValue('EXTRAS', 'TAX', CurrencyFormat2(totaltax));
    setValue('EXTRAS', 'TOTAL_EXT', CurrencyFormat2(displaytotal));
    //MSRP
    if (!hasAnswer('HIDE_DIO', 'YES')) {
        totalnotaxms = Number(total_MS) + Number(dio);
        setValue('EXTRAS', 'TOTAL_MSRP', CurrencyFormat2(totalnotaxms));
    } else {
        totalnotaxms = Number(total_MS) - Number(discount); //don't add dios
        setValue('EXTRAS', 'TOTAL_MSRP', CurrencyFormat2(totalnotaxms));
    }
    totaltaxms = (Number(totalnotaxms) * tax) / 100;
    displaytotalms = Number(totalnotaxms) + Number(totaltaxms);
    setValue('EXTRAS', 'TAX_MS', CurrencyFormat2(totaltaxms));
    setValue('EXTRAS', 'TOTAL_MS_EXT', CurrencyFormat2(displaytotalms));

    if (hasAnswer('PRICING_TYPE', 'MSRP')) {
        $('[type="MS"]').show();
    } else if (hasAnswer('PRICING_TYPE', 'SELLING_PRICE')) {
        $('[type="SP"]').show();
    } else if (hasAnswer('PRICING_TYPE', 'DEALER_COST')) {
        $('[type="DC"]').show();
    } else if (hasAnswer('PRICING_TYPE', 'BOTH')) {
        $('[type="SP"]').show();
        $('[type="MS"]').show();
    }


};
