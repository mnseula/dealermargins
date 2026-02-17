console.log('Get Poster Options');

// Create a deep copy of boattable to preserve full descriptions
window.originalBoatTable = [];
if (typeof boattable !== 'undefined' && boattable) {
    for (var i = 0; i < boattable.length; i++) {
        window.originalBoatTable.push({
            'ItemNo': boattable[i].ItemNo,
            'ItemDesc1': boattable[i].ItemDesc1,
            'MCT': boattable[i].MCT
        });
    }
    console.log('DEBUG: Created originalBoatTable copy with', window.originalBoatTable.length, 'items');
    // Log first few items to verify content
    console.log('DEBUG: Sample originalBoatTable items:');
    for (var debugIdx = 0; debugIdx < Math.min(5, window.originalBoatTable.length); debugIdx++) {
        console.log('  -', window.originalBoatTable[debugIdx].ItemNo, ':', window.originalBoatTable[debugIdx].ItemDesc1);
    }
}

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

// HTML attribute escape function - uses single quotes for attributes and escapes single quotes in content
function escapeHtmlAttribute(text) {
    if (!text) return text;
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

//$('div[data-ref="OPTIONS/OPTIONS"]').children('div').remove();
// $('div[data-ref="SPECS/SPECS"]').children('div').remove();

//$('input[id="model"]').attr('readonly', 'true');

reset('POSTER_IMG');
reset('PERF_LOGOS');
reset('COLOR');

if(getValue('BOAT_INFO','HULL_NO') === false || getValue('BOAT_INFO','HULL_NO') === true || getValue('BOAT_INFO','HULL_NO') === undefined){
    smallPopup('Please select an Unregistered Boat from the first tab.');
}
var previouslySaved = sStatement('SEL_ONE_BOAT_FLYER',[serial]).length;


//if previously saved, get it from here instead of the serial number master - SEL_ONE_BOAT_LINES_FLYER_OPTIONS
console.log(previouslySaved);


var beginningHTML="";
beginningHTML += "<!doctype html>";
beginningHTML += "<html>";
beginningHTML += "<head>";
beginningHTML += "<meta charset=\"utf-8\">";
beginningHTML += "<title>Rename and Sort Options</title>";
//beginningHTML += "<script src=\"https://code.jquery.com/jquery-1.12.4.js\"></script>";
//beginningHTML += "<script src=\"https://code.jquery.com/ui/1.12.1/jquery-ui.js\"></script>";
beginningHTML += "<link rel=\"stylesheet\" href=\"https://code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css\">";
beginningHTML += "<script>";
beginningHTML += "  $( function() {";
beginningHTML += "    $( \"#sortable\" ).sortable({";
beginningHTML += "      placeholder: \"ui-state-highlight\"";
beginningHTML += "    });";
beginningHTML += "    $( \"#sortable\" ).disableSelection();";
beginningHTML += "  } );";
beginningHTML += "  </script>";

beginningHTML += "<script>" + xButtons.toString() +  "</script>";


function xButtons(){
    $('.opt-x').on('click',function(){
        console.log($(this));
        if ($(this).parent().hasClass('ui-state-focus')){
            console.log('focus');
            $(this).parent().switchClass('ui-state-focus','ui-state-error');
            $(this).parent().insertAfter($('.opt-x').last().parent());
            $(this).parent().removeClass('indent');
        } else {
            console.log('error state');
            $(this).parent().switchClass('ui-state-error','ui-state-focus');
            $(this).parent().removeClass('indent');
        }
    });
}

/*function xButtons(){
 $('.opt-x').on('click',function(){
 console.log($(this));
 if ($(this).parent().hasClass('ui-state-focus')){
 console.log('focus');
 //$(this).parent().switchClass('ui-state-focus','ui-state-error');
 $(this).parent().addClass('ui-state-error').removeClass('ui-state-focus');
 //$(this).parent().switchClass('ui-state-focus','ui-state-error');
 $(this).parent().addClass('indent');
 $(this).parent().insertAfter($('.opt-x').last().parent());
 $(this).parent().addClass('ui-state-error').removeClass('ui-state-focus');
 } else {
 console.log('error state');
 //$(this).parent().switchClass('ui-state-error','ui-state-focus');
 $(this).parent().addClass('ui-state-focus').removeClass('ui-state-error');
 $(this).parent().removeClass('indent');
 }
 });
 }*/

beginningHTML += "<style>";
beginningHTML += "#options{";
beginningHTML += "    font-family:Calibri;";
beginningHTML += "    font-size:18px;";
beginningHTML += "    background-color:#ffffff;";
beginningHTML += "    color:#000000;";
beginningHTML += "    }";
beginningHTML += "#options ul{";
beginningHTML += "    list-style-type: none;";
beginningHTML += "    }    ";
beginningHTML += ".indent{";
beginningHTML += "    margin-left: 10px;";
beginningHTML += "    }    ";
beginningHTML += "#options input[type=text]{";
beginningHTML += "    width: 400px;";
beginningHTML += "    }    ";
beginningHTML += "</style>";
beginningHTML += "</head>";
beginningHTML += "<body>";
beginningHTML += "<div id=\"options\">";
beginningHTML += "";



var endingHTML="";
endingHTML += "</ul>";
endingHTML += "</div>";
endingHTML += "</body>";
endingHTML += "</html>";




var optionsList = '<ul id="sortable">';
// Use single quotes for value attribute to avoid issues with double quotes in descriptions
// Store itemno in data-itemno attribute for reliable retrieval
var newOptionItem1 = '<li class="ui-state-focus" data-itemno=\'';
var newOptionItem1hidden = '<li class="ui-state-error indent" data-itemno=\'';
var newOptionItem2 = '\'><span class="ui-icon ui-icon-arrowthick-2-n-s"></span><input type="text" value=\'';
var newOptionItem3 = '\' name = \'tb';
var newOptionItem4 = '\' size="75"><input onclick="xButtons()" class="opt-x" type="button" value="X"></li>';

if(previouslySaved === 0){
    console.log('Not Previously Saved');
    $.each(boattable, function(i) {
        var itemdesc = boattable[i].ItemDesc1;
        var itemno = boattable[i].ItemNo;
        var mct = boattable[i].MCT;
        if(mct !== 'BOAT' && mct !== 'BOATPKG' && mct !== 'Disc - Selling' && itemno !== 'NPPNPRICE16S' && itemno !== 'NPPNPRICE18S' && itemno !== 'NPPNPRICE19S' && itemno !== 'NPPNPRICE20S' && itemno !== 'NPPNPRICE21S' && itemno !== 'NPPNPRICE22S' && itemno !== 'NPPNPRICE23S' && itemno !== 'NPPNPRICE24S'&& itemno !== 'NPPNPRICE25S'&& itemno !== 'NPPNPRICELX/LT' && itemdesc !== 'true' && itemdesc !== 'TRUE' && !/^\d$/.test(itemdesc)){
            // New template: data-itemno stores itemno, value stores description, name uses itemno
            optionsList += newOptionItem1 + escapeHtmlAttribute(itemno) + newOptionItem2 + escapeHtmlAttribute(itemdesc) + newOptionItem3 + escapeHtmlAttribute(itemno) + newOptionItem4;
        }
    });
}

else{
    console.log('Previously Saved');
    boattable2 = sStatement('SEL_ONE_BOAT_FLYER',[serial]);
    pricingtable = sStatement('SEL_ONE_BOAT_FLYER_PRICING',[serial]);
    //console.table(pricingtable);

    // Build lookup map by truncated description
    var descLookupMap = {};
    // Build lookup map from description to item number (for fixing corrupted saved data)
    var descToItemNoMap = {};
    if (window.originalBoatTable && window.originalBoatTable.length > 0) {
        for (var m = 0; m < window.originalBoatTable.length; m++) {
            var origDesc = window.originalBoatTable[m].ItemDesc1;
            var origItemNo = window.originalBoatTable[m].ItemNo;
            if (origDesc) {
                // Store mapping from truncated to full description
                var upperDesc = origDesc.toUpperCase();
                descLookupMap[upperDesc] = origDesc;
                // Also store 30-char truncated version
                if (upperDesc.length > 30) {
                    descLookupMap[upperDesc.substring(0, 30)] = origDesc;
                }
                // Store mapping from description to item number (for corruption recovery)
                descToItemNoMap[upperDesc] = origItemNo;
            }
        }
    }
    console.log('DEBUG descLookupMap keys (first 10):', Object.keys(descLookupMap).slice(0, 10));
    console.log('DEBUG descToItemNoMap keys (first 10):', Object.keys(descToItemNoMap).slice(0, 10));

    $.each(boattable2, function(j) {
        var itemdesc = boattable2[j].itemdesc;
        var itemno = boattable2[j].part;
        var hidden = boattable2[j].hidden;
        //var mct = boattable2[j].MCT;

        // Look up full description by matching truncated description
        var upperItemDesc = itemdesc.toUpperCase();
        if (descLookupMap[upperItemDesc] && descLookupMap[upperItemDesc].length > itemdesc.length) {
            console.log('Found full description for:', itemdesc, '->', descLookupMap[upperItemDesc]);
            itemdesc = descLookupMap[upperItemDesc];
        }
        
        // FIX: Recover corrupted item numbers (when description was saved instead of item number)
        // Detect corruption: itemno contains spaces, is >30 chars, or doesn't look like typical item number
        var isItemNoCorrupted = (itemno.indexOf(' ') > -1 || itemno.length > 30);
        if (isItemNoCorrupted && descToItemNoMap[upperItemDesc]) {
            console.log('CORRUPTION DETECTED: itemno was "' + itemno + '", fixing to "' + descToItemNoMap[upperItemDesc] + '"');
            itemno = descToItemNoMap[upperItemDesc];
        }

        //if(mct !== 'BOAT' && mct !== 'BOATPKG'){
        //optionsList += newOptionItem1 + itemdesc + newOptionItem2 + itemno + newOptionItem3 + itemno + newOptionItem4;
        console.log('DEBUG itemdesc before escape:', itemdesc);
        console.log('DEBUG itemdesc after escape:', escapeHtml(itemdesc));
        console.log('hidden',hidden);
        if ((hidden === '0' || hidden === 0) && itemno !== 'NPPNPRICE16S' && itemno !== 'NPPNPRICE18S' && itemno !== 'NPPNPRICE19S' && itemno !== 'NPPNPRICE20S' && itemno !== 'NPPNPRICE21S' && itemno !== 'NPPNPRICE22S' && itemno !== 'NPPNPRICE23S' && itemno !== 'NPPNPRICE24S'&& itemno !== 'NPPNPRICE25S'&& itemno !== 'NPPNPRICELX/LT' && itemdesc !== 'true' && itemdesc !== 'TRUE' && !/^\d$/.test(itemdesc)){
            // New template: data-itemno stores itemno, value stores description, name uses itemno
            optionsList += newOptionItem1 + escapeHtmlAttribute(itemno) + newOptionItem2 + escapeHtmlAttribute(itemdesc) + newOptionItem3 + escapeHtmlAttribute(itemno) + newOptionItem4;
        }
        else{
            optionsList += newOptionItem1hidden + escapeHtmlAttribute(itemno) + newOptionItem2 + escapeHtmlAttribute(itemdesc) + newOptionItem3 + escapeHtmlAttribute(itemno) + newOptionItem4;
        }

        //}
    });


}
// optionsList;

var pageHTML = beginningHTML + optionsList + endingHTML;

//console.log(pageHTML);

$('div[data-ref="OPTIONS/OPTIONS"]').append(pageHTML);
var model = getValue('BOAT_INFO','BOAT_MODEL');
// Replace 'SE' with 'SF' if model ends with 'SE'
if (model.endsWith('SF')) {
    model = model.slice(0, -2) + 'SE';
}
if (realmodel.endsWith('SF')) {
    realmodel = realmodel.slice(0, -2) + 'SE';
}

var perfpkgid = getValue('BOAT_INFO', 'STD_PERF_PKG');
console.log("ZACH PERF PKG ID: "+perfpkgid);
var prfPkgs = loadByListName('perf_pkg_spec', "WHERE (MODEL ='" + realmodel + "') /*AND (STATUS ='Active') */AND (PKG_ID ='" + perfpkgid + "')");
var specs = getSpecTbl2(realmodel);

$('div[data-ref="SPECS/SPECS"]').append(specs);



console.log(specs);

function getSpecTbl2(realmodel) { //used in standards/specs in the product.

    // Get Boat Specs
    //var listid = getListID('boat_specs'); //use getlistid to get the boat_specs list id
    boatSpecs = loadByListName('boat_specs',"WHERE MODEL = '" + realmodel + "'");
    //console.log(boatSpecs);

    var loa = boatSpecs[0].LOA;
    loa = loa.replace(/'/g, "&apos;").replace(/"/g, "&quot;");

    var beam = boatSpecs[0].BEAM;
    beam = beam.replace(/'/g, "&apos;").replace(/"/g, "&quot;");

    var diam = boatSpecs[0].PONT_DIAM;
    diam = diam.replace(/'/g, "&apos;").replace(/"/g, "&quot;");

    //Lookup the description of the Engine Config and the Fuel Type from Local Lists to print words instead of a number.
    // CPQ Fix: Add error handling for missing engine config data
    var engConfigDesc = 'Single Outboard'; // Default for CPQ boats
    var fuelTypeDesc = 'Gasoline'; // Default for CPQ boats
    
    try {
        if (boatSpecs[0].ENG_CONFIG_ID) {
            var engConfigResult = loadByListName('list_EngineTypes', 'LIST/engineConfigID["' + boatSpecs[0].ENG_CONFIG_ID + '"]');
            if (engConfigResult && engConfigResult.length > 0 && engConfigResult[0].engineConfigName) {
                engConfigDesc = engConfigResult[0].engineConfigName;
            }
        }
        
        if (boatSpecs[0].FUEL_TYPE_ID) {
            var fuelTypeResult = loadByListName('list_FuelTypes', 'LIST/FUEL_TYPE_ID["' + boatSpecs[0].FUEL_TYPE_ID + '"]');
            if (fuelTypeResult && fuelTypeResult.length > 0 && fuelTypeResult[0].FUEL_TYPE_NAME) {
                fuelTypeDesc = fuelTypeResult[0].FUEL_TYPE_NAME;
            }
        }
    } catch (e) {
        console.log('CPQ FLYER - Using default engine/fuel specs for CPQ boat');
    }

    //console.log(boatSpecs);
    // Create Spec Table
    var specCapTbl = '<div><table border="0" cellpadding="0" cellspacing="5" style="width: 250px;">' +
        '<tbody>' +
        '<td style="text-align: left; font-size:13px; white-space: nowrap;">MODEL:</td>' +
        '<td style="text-align: left; font-size:13px"><input type="text" id="model" value="' + model + '"></td>' +
        '</tr>' +
        '<tr>' +
        '<td style="text-align: left; font-size:13px; white-space: nowrap;">POWER:</td>' +
        '<td style="text-align: left; font-size:13px white-space: nowrap;"><input type="text" id="engine" value="' + engConfigDesc + '"></td>' +
        '</tr>' +
        '<tr>' +
        '<td style="text-align: left; font-size:13px; white-space: nowrap;">LENGTH:</td>' +
        '<td style="text-align: left; font-size:13px"><input type="text" id="loa" value="' + loa + '"></td>' +
        '</tr>' +
        //'<tr>' +
        //'<td style="text-align: left; font-size:13px; white-space: nowrap;">PONTOON LENGTH:</td>' +
        //'<td style="text-align: left; font-size:13px"><input type="text" id="toon_length" value="' + boatSpecs[0].PONT_LEN + '"></td>' +
        //'</tr>' +
        //'<tr>' +
        //'<td style="text-align: left; font-size:13px; white-space: nowrap;">DECK LENGTH:</td>' +
        //'<td style="text-align: left; font-size:13px"><input type="text" id="deck" value="' + boatSpecs[0].DECK_LEN + '"></td>' +
        //'</tr>' +
        '<tr>' +
        '<td style="text-align: left; font-size:13px; white-space: nowrap;">BEAM:</td>' +
        '<td style="text-align: left; font-size:13px"><input type="text" id="beam" value="' + beam + '"></td>' +
        '</tr>' +
        '<tr>' +
        '<td style="text-align: left; font-size:13px; white-space: nowrap;">DIAMETER:</td>' +
        '<td style="text-align: left; font-size:13px"><input type="text" id="diameter" value="' + diam + '"></td>' +
        '</tr>' +
        '<tr>' +
        '<td style="text-align: left; font-size:13px; white-space: nowrap;">CAPACITY:</strong></td>' +
        '<td style="text-align: left; font-size:13px"><input type="text" id="cap" value="' + (function() { if(window.cpqLhsData) { console.log('CPQ LHS Data fields:', Object.keys(window.cpqLhsData)); console.log('CPQ LHS Data:', window.cpqLhsData); return window.cpqLhsData.person_capacity || window.cpqLhsData.max_person_capacity || window.cpqLhsData.capacity || ''; } else { return (prfPkgs && prfPkgs.length > 0 ? prfPkgs[0].CAP : ''); } })() + '"></td>' +
        '</tr>' +
        '<tr>' +
        '<td style="text-align: left; font-size:13px; white-space: nowrap;">HULL WEIGHT:</strong></td>' +
        '<td style="text-align: left; font-size:13px"><input type="text" id="weight" value="' + (window.cpqLhsData && window.cpqLhsData.hull_weight ? window.cpqLhsData.hull_weight : (prfPkgs && prfPkgs.length > 0 ? prfPkgs[0].WEIGHT : '')) + '"></td>' +
        '</tr>' +
        '<tr>' +
        '<td style="text-align: left; font-size:13px; white-space: nowrap;">FUEL CAPACITY:</strong></td>' +
        '<td style="text-align: left; font-size:13px"><input type="text" id="fuel" value="' + boatSpecs[0].FUEL_CAP + ' gal"></td>' +
        '</tr>' +
        '</tbody>' +
        '</table><br/></div>';

    return specCapTbl;
}

// Check if this is a CPQ boat
var isCpqBoat = (window.cpqBaseBoatMSRP && Number(window.cpqBaseBoatMSRP) > 0 && 
                 window.cpqBaseBoatDealerCost && Number(window.cpqBaseBoatDealerCost) > 0);

console.log('CPQ FLYER DEBUG - window.cpqBaseBoatMSRP:', window.cpqBaseBoatMSRP);
console.log('CPQ FLYER DEBUG - window.cpqBaseBoatDealerCost:', window.cpqBaseBoatDealerCost);
console.log('CPQ FLYER DEBUG - isCpqBoat:', isCpqBoat);

if (isCpqBoat) {
    // CPQ BOAT: Use CPQ pricing data
    console.log('CPQ FLYER - Using CPQ pricing data');
    
    // Use CPQ MSRP
    var cpqMSRP = Number(window.cpqBaseBoatMSRP);
    flyerMSRP = cpqMSRP.toLocaleString("en-US", {minimumFractionDigits: 0, maximumFractionDigits: 0});
    console.log('CPQ FLYER DEBUG - Setting FLYER_MSRP to:', flyerMSRP);
    setValue('PRICING','FLYER_MSRP',flyerMSRP);
    
    // Get the calculated sale price from DLR2 (set by Calculate2021.js)
    var cpqSalePrice = getValue('DLR2', 'PKG_SALE');
    console.log('CPQ FLYER DEBUG - DLR2.PKG_SALE:', cpqSalePrice);
    
    if (!cpqSalePrice || cpqSalePrice === true || cpqSalePrice === false) {
        // Fallback: calculate from CPQ dealer cost
        console.log('CPQ FLYER DEBUG - Using fallback dealer cost');
        cpqSalePrice = Number(window.cpqBaseBoatDealerCost); // This is simplified - actual calc includes margins
    }
    
    console.log('CPQ FLYER DEBUG - Final cpqSalePrice:', cpqSalePrice);

    if (cpqSalePrice && Number(cpqSalePrice) > 0) {
        // Format sale price with commas, no decimals
        var formattedSalePrice = Number(cpqSalePrice).toLocaleString("en-US", {minimumFractionDigits: 0, maximumFractionDigits: 0});
        console.log('CPQ FLYER DEBUG - Setting FLYER_FINAL_PRICE to:', formattedSalePrice);
        setValue('PRICING','FLYER_FINAL_PRICE', formattedSalePrice);

        // Calculate discount for CPQ boats
        var calculatedDiscount = cpqMSRP - Number(cpqSalePrice);
        console.log('CPQ FLYER DEBUG - calculatedDiscount:', calculatedDiscount);
        if (calculatedDiscount > 0) {
            // Normal case: Sale price is less than MSRP, show savings
            console.log('CPQ FLYER DEBUG - Setting FLYER_DISCOUNT to:', Math.round(calculatedDiscount));
            setValue('PRICING','FLYER_DISCOUNT', Math.round(calculatedDiscount).toString());
        } else {
            // Sale price >= MSRP, show $0 savings
            console.log('CPQ FLYER - Sale price >= MSRP, setting discount to $0');
            setValue('PRICING','FLYER_DISCOUNT', '0');
        }
    } else {
        console.log('CPQ FLYER DEBUG - cpqSalePrice is not valid:', cpqSalePrice);
    }
} else {
    // LEGACY BOAT: Use EXTRAS table pricing
    window.flyerMSRP = (getValue('EXTRAS','TOTAL_MS_EXT'));
    flyerMSRP = flyerMSRP.slice(0, -3);
    
    setValue('PRICING','FLYER_MSRP',flyerMSRP);
    
    // Set selling price and calculate discount for new boats
    var flyerSellingPrice = getValue('EXTRAS','TOTAL');
    if(flyerSellingPrice && flyerSellingPrice !== '' && flyerSellingPrice !== true && flyerSellingPrice !== false) {
        // Remove any formatting and set final price
        flyerSellingPrice = flyerSellingPrice.toString().replace(/[^0-9.]/g, '');
        setValue('PRICING','FLYER_FINAL_PRICE',flyerSellingPrice);
        
        // Calculate discount: MSRP - Sale Price
        var msrpNum = parseFloat(flyerMSRP.replace(/[^0-9.]/g, '')) || 0;
        var saleNum = parseFloat(flyerSellingPrice) || 0;
        var calculatedDiscount = msrpNum - saleNum;
        if(calculatedDiscount > 0) {
            setValue('PRICING','FLYER_DISCOUNT',calculatedDiscount.toFixed(2));
        }
    }
}

document.getElementById("model").disabled = true;
document.getElementById("loa").disabled = true;
document.getElementById("beam").disabled = true;
document.getElementById("diameter").disabled = true;
document.getElementById("weight").disabled = true;

if(previouslySaved !== 0 && pricingtable && pricingtable.length > 0){
    console.log('Restore Previously Saved Pricing and Settings');

    // CPQ Fix: Don't restore spec values for CPQ boats - use values from window.cpqLhsData instead
    if (!isCpqBoat) {
        document.getElementById("engine").value = pricingtable[0].power;
        document.getElementById("cap").value = pricingtable[0].capacity;
        document.getElementById("fuel").value = pricingtable[0].fuel;
    } else {
        console.log('CPQ FLYER - Skipping restore of spec values (using CPQ LHS data)');
    }

    // CPQ Fix: Don't restore pricing values for CPQ boats - use calculated values instead
    if (!isCpqBoat) {
        if(pricingtable[0].title !== '1'){
            setValue('PRICING','FLYER_TITLE',pricingtable[0].title);
        }
        if(pricingtable[0].msrp !== '1'){
            setValue('PRICING','FLYER_MSRP',pricingtable[0].msrp);
        }
        if(pricingtable[0].discount !== '1'){
            setValue('PRICING','FLYER_DISCOUNT',pricingtable[0].discount);
        }
        if(pricingtable[0].final_price !== '1'){
            setValue('PRICING','FLYER_FINAL_PRICE',pricingtable[0].final_price);
        }
    } else {
        console.log('CPQ FLYER - Skipping restore of pricing values, using calculated values');
    }
    
    setValue('PRICING','FONT_SIZE',pricingtable[0].font);
    if(pricingtable[0].dlr_boat_img_url.length > 1){
        setValue('DLR_IMG','DLR_IMG_URL',pricingtable[0].dlr_boat_img_url);
    }

    setAnswer('POSTER_IMG',pricingtable[0].posterimg);
    setAnswer('PERF_LOGOS',pricingtable[0].perf_logo);
    setAnswer('COLOR',pricingtable[0].print_options);
}
