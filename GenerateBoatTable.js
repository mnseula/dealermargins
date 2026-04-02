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
            var rowKey = (itemno + '_' + desc).replace(/"/g, '&quot;');
            rows = rows + '<tr><td><span class="row-eye-btn" data-rowkey="' + rowKey + '" title="Click to strike out" style="cursor:pointer;margin-right:5px;font-size:14px;vertical-align:middle;user-select:none">👁</span>' + escapeHtml(desc) + '</td><td>' + escapeHtml(itemno) + '</td><td align="center">' + qty + '</td><td type="DC" align="right">' + dc + '</td><td type="MS" align="right">' + msrp + '</td><td type="SP" align="right">' + sp + '</td></tr>';
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

    // Row-strikethrough: reset state when navigating to a new boat
    var currentSerial = getValue('BOAT_INFO', 'HULL_NO') || '';
    if (!window.generatorLastSerial || window.generatorLastSerial !== currentSerial) {
        window.struckRows = new Set();
        window.strikeZeroPriceOptions = false;
        window.hideUnselectedBoatOptions = false;
        window.descEdits = {};       // {rowKey: newText} for edited descriptions
        window.writeInItems = [];    // [{rowKey, desc, itemno, qty, dc, ms, sp}]
        window.generatorLastSerial = currentSerial;
    }
    if (!window.struckRows) { window.struckRows = new Set(); }
    if (!window.descEdits) { window.descEdits = {}; }
    if (!window.writeInItems) { window.writeInItems = []; }

    // Make item descriptions editable in-place; tag each span with its rowKey so
    // print.js can apply edits from window.descEdits without relying on DOM capture
    $('#included tbody tr').each(function() {
        var rowKey = $(this).find('.row-eye-btn').attr('data-rowkey') || '';
        var td = $(this).find('td:first-child')[0];
        if (!td) return;
        var textNodes = [];
        $(td).contents().each(function() { if (this.nodeType === 3 && this.nodeValue.trim()) { textNodes.push(this); } });
        textNodes.forEach(function(node) {
            var span = document.createElement('span');
            span.className = 'desc-editable';
            span.contentEditable = 'true';
            span.setAttribute('data-rowkey', rowKey);
            span.style.cssText = 'outline:none;cursor:text;';
            span.title = 'Click to edit description';
            // Re-apply any previously saved edit for this row
            span.textContent = (window.descEdits[rowKey] !== undefined) ? window.descEdits[rowKey] : node.nodeValue;
            node.parentNode.replaceChild(span, node);
        });
    });

    // Save description edits to window.descEdits so print.js can pick them up
    $('#included').on('input.descedit', '.desc-editable[data-rowkey]', function() {
        window.descEdits[$(this).attr('data-rowkey')] = this.textContent;
    });

    // Re-apply previously struck rows after re-render
    $('#included tbody tr').each(function() {
        var eyeBtn = $(this).find('.row-eye-btn');
        if (eyeBtn.length && window.struckRows.has(eyeBtn.attr('data-rowkey'))) {
            $(this).find('td').css({ 'text-decoration': 'line-through', 'color': '#aaa' });
            eyeBtn.css({ 'text-decoration': 'line-through', 'opacity': '0.35' }).attr('title', 'Click to restore');
        }
    });

    // Handler: toggle strikethrough and eye icon style
    $('#included').on('click', '.row-eye-btn', function() {
        var key = $(this).attr('data-rowkey');
        var row = $(this).closest('tr');
        if (window.struckRows.has(key)) {
            window.struckRows.delete(key);
            row.find('td').css({ 'text-decoration': '', 'color': '' });
            $(this).css({ 'text-decoration': '', 'opacity': '' }).attr('title', 'Click to strike out');
        } else {
            window.struckRows.add(key);
            row.find('td').css({ 'text-decoration': 'line-through', 'color': '#aaa' });
            $(this).css({ 'text-decoration': 'line-through', 'opacity': '0.35' }).attr('title', 'Click to restore');
        }
    });

    // ALL BOATS: Add checkboxes for unselected options (CPQ only) and $0 strikethrough
    var isCpqBoat = (pkgrowtotal_SP > 0);

    // Remove existing container if present (prevents duplicates on DOM reload)
    $('#hideUnselectedOptionsContainer').remove();
    var currentHideUnselected = (window.hideUnselectedBoatOptions === true);
    var currentStrikeZeroPrice = (window.strikeZeroPriceOptions === true);

    var checkboxHtml = '<div id="hideUnselectedOptionsContainer" style="margin-top: 10px; margin-bottom: 10px;">' +
        '<label style="font-family: Calibri; font-size: 14px; cursor: pointer;">' +
        '<input type="checkbox" id="hideUnselectedOptions" style="margin-right: 5px;"' + (currentHideUnselected ? ' checked' : '') + '>' +
        'Hide unselected boat options' +
        '</label>&nbsp;&nbsp;&nbsp;' +
        '<label style="font-family: Calibri; font-size: 14px; cursor: pointer;">' +
        '<input type="checkbox" id="strikeZeroPriceOptions" style="margin-right: 5px;"' + (currentStrikeZeroPrice ? ' checked' : '') + '>' +
        'Strike out $0 options' +
        '</label>' +
        '<div style="margin-top: 8px; font-family: Calibri; font-size: 11px; color: #888; line-height: 1.5;">' +
        '&#128065; Click the eye icon next to any item to strike it out &mdash; it will stay visible here so you have a record, but it will <strong>not</strong> appear on the printed window sticker. ' +
        'Use the checkboxes above to strike out entire groups at once. Click the eye again to undo.' +
        '</div>' +
        '</div>';
    $('div[data-ref="INCLUDED/INCLUDED_OPTIONS"]').append(checkboxHtml);

    // Write-in item button
    $('#writeInItemContainer').remove();
    var writeInHtml = '<div id="writeInItemContainer" style="margin-top: 6px; margin-bottom: 4px;">' +
        '<button id="addWriteInItem" style="font-family: Calibri; font-size: 13px; cursor: pointer; padding: 3px 10px;">+ Add write-in item</button>' +
        '<div style="font-family: Calibri; font-size: 11px; color: #888; margin-top: 5px; line-height: 1.6;">' +
        'For this print only &mdash; write-in items are not saved and will be gone when you navigate away.<br>' +
        'To show both MSRP and Sale Price on your write-in item, select <strong>Sale &amp; MSRP</strong> from the <strong>Pricing Type To Print</strong> options before adding your item.' +
        '</div>' +
        '</div>';
    $('div[data-ref="INCLUDED/INCLUDED_OPTIONS"]').append(writeInHtml);

    // Use event delegation so the handler survives any re-renders of the container
    $('div[data-ref="INCLUDED/INCLUDED_OPTIONS"]').off('click.writein').on('click.writein', '#addWriteInItem', function() {
        var rowKey = 'writein-' + Date.now();

        // Register item in window.writeInItems — print.js reads from here, not the DOM
        var item = { rowKey: rowKey, desc: '', itemno: '', qty: '1', dc: '', ms: '', sp: '' };
        window.writeInItems.push(item);

        var tr = document.createElement('tr');
        tr.className = 'writein-row';
        tr.setAttribute('data-writein', 'true');

        // Description cell
        var tdDesc = document.createElement('td');
        var eyeSpan = document.createElement('span');
        eyeSpan.className = 'row-eye-btn';
        eyeSpan.setAttribute('data-rowkey', rowKey);
        eyeSpan.setAttribute('title', 'Click to strike out');
        eyeSpan.style.cssText = 'cursor:pointer;margin-right:5px;font-size:14px;vertical-align:middle;user-select:none';
        eyeSpan.innerHTML = '&#128065;';
        var descSpan = document.createElement('span');
        descSpan.className = 'desc-editable';
        descSpan.contentEditable = 'true';
        descSpan.setAttribute('data-rowkey', rowKey);
        descSpan.style.cssText = 'min-width:120px;display:inline-block;padding:1px 3px;';
        descSpan.textContent = '';
        descSpan.addEventListener('input', function() { item.desc = this.textContent; window.descEdits[rowKey] = this.textContent; });
        tdDesc.appendChild(eyeSpan);
        tdDesc.appendChild(descSpan);
        tr.appendChild(tdDesc);

        // Item # cell
        var tdItem = document.createElement('td');
        tdItem.contentEditable = 'true';
        tdItem.style.cssText = 'min-width:40px;padding:1px 3px;';
        tdItem.addEventListener('input', function() { item.itemno = this.textContent; });
        tr.appendChild(tdItem);

        // Qty cell
        var tdQty = document.createElement('td');
        tdQty.contentEditable = 'true';
        tdQty.align = 'center';
        tdQty.style.cssText = 'min-width:20px;padding:1px 3px;';
        tdQty.textContent = '1';
        tdQty.addEventListener('input', function() { item.qty = this.textContent; });
        tr.appendChild(tdQty);

        // Price cells
        ['DC', 'MS', 'SP'].forEach(function(type) {
            var td = document.createElement('td');
            td.setAttribute('type', type);
            td.contentEditable = 'true';
            td.align = 'right';
            td.style.cssText = 'min-width:50px;padding:1px 3px;';
            td.addEventListener('input', (function(t) { return function() { item[t.toLowerCase()] = this.textContent; }; })(type));
            tr.appendChild(td);
        });

        $('#included tbody').append(tr);

        // Show exactly the columns that match the selected pricing type
        var $newRow = $(tr);
        $newRow.find('[type="DC"],[type="MS"],[type="SP"]').hide();
        if (hasAnswer('PRICING_TYPE', 'MSRP'))               { $newRow.find('[type="MS"]').show(); }
        else if (hasAnswer('PRICING_TYPE', 'SELLING_PRICE')) { $newRow.find('[type="SP"]').show(); }
        else if (hasAnswer('PRICING_TYPE', 'BOTH'))          { $newRow.find('[type="MS"],[type="SP"]').show(); }
        else if (hasAnswer('PRICING_TYPE', 'DEALER_COST'))   { $newRow.find('[type="DC"]').show(); }
        // NO_PRICES: no price columns shown

        descSpan.focus();
    });

    // Handler: hide unselected ("No...") items
    $('#hideUnselectedOptions').on('change', function() {
        var hideUnselected = $(this).prop('checked');
        window.hideUnselectedBoatOptions = hideUnselected;
        $('#included tbody tr').each(function() {
            var firstTd = $(this).find('td:first');
            if (firstTd.length > 0) {
                var descSpan = firstTd.find('.desc-editable');
                var desc = (descSpan.length ? descSpan.text() : firstTd.text()).trim().toUpperCase();
                if (desc.startsWith('NO ') || desc.startsWith('NO-')) {
                    $(this).toggle(!hideUnselected);
                }
            }
        });
    });

    // Handler: strike out $0 price items using the same eye/strikethrough mechanism
    $('#strikeZeroPriceOptions').on('change', function() {
        var strikeZero = $(this).prop('checked');
        window.strikeZeroPriceOptions = strikeZero;
        $('#included tbody tr').each(function() {
            var eyeBtn = $(this).find('.row-eye-btn');
            if (!eyeBtn.length) return;
            var msTd = $(this).find('td[type="MS"]');
            var spTd = $(this).find('td[type="SP"]');
            if (msTd.length && spTd.length) {
                var msVal = parseFloat(msTd.text().trim()) || 0;
                var spVal = parseFloat(spTd.text().trim()) || 0;
                if (msVal === 0 && spVal === 0) {
                    var key = eyeBtn.attr('data-rowkey');
                    if (strikeZero) {
                        window.struckRows.add(key);
                        $(this).find('td').css({ 'text-decoration': 'line-through', 'color': '#aaa' });
                        eyeBtn.css({ 'text-decoration': 'line-through', 'opacity': '0.35' }).attr('title', 'Click to restore');
                    } else {
                        window.struckRows.delete(key);
                        $(this).find('td').css({ 'text-decoration': '', 'color': '' });
                        eyeBtn.css({ 'text-decoration': '', 'opacity': '' }).attr('title', 'Click to strike out');
                    }
                }
            }
        });
    });

    // Apply persisted state immediately after render
    $('#hideUnselectedOptions').trigger('change');
    $('#strikeZeroPriceOptions').trigger('change');

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
    var hasActiveDioItems = false;
    for (var dioN = 1; dioN <= 10; dioN++) {
        var dioDesc = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_' + dioN);
        if (dioDesc && dioDesc !== '' && dioDesc !== false && dioDesc !== true) {
            hasActiveDioItems = true;
            break;
        }
    }
    if (!hasActiveDioItems) { dio = 0; }
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
