console.log('Print a Window Sticker');

//$('div[data-ref="LOADING/SPINNER"]').show().empty().append('<div id="WS-print-loader"><h4>PRINTING&nbsp;<img src="https://boat-builder.benningtonmarine.com/images/ajax-loader.gif"></h4></div>');

//Get the Dealer Name from the Serial Number Master
var dealerinfo = loadByListName('PW_SerialNumberMaster', "WHERE Boat_SerialNo = '" + serial + "'");
var dealername = dealerinfo[0].DealerName;
var dealerno = dealerinfo[0].DealerNumber;
dealerno = dealerno.replace(/^[0]+/g,"");
dealerno = pad(dealerno, 8);
//console.log(dealerno);
//window.boatpricingtype
//Get the Dealer Address and phone from the dealer list.
var dealeraddress = loadByListName('dealers', "WHERE DlrNo = '" + dealerno + "'");
//console.log(dealeraddress);
dealeraddr1 = dealeraddress[0].Add1;
dealeraddr2 = dealeraddress[0].Addr2;
dealercity = dealeraddress[0].City;
dealerstate = dealeraddress[0].State;
dealerphone = dealeraddress[0].PhoneNo;
dealerzip = dealeraddress[0].Zip;
dealerdba = dealeraddress[0].DealerDBA;
dealerweb = dealeraddress[0].Web_URL;

var boatPricing = getValue('DLR','PRC_TYPE');
console.log('Print boatPricing: ',boatPricing);


//get the pricing type
var total = "";
if (hasAnswer('PRICING_TYPE','SELLING_PRICE'))  { type = 'SELLING PRICE', total = total_SP}
else if (hasAnswer('PRICING_TYPE','MSRP'))      { type = 'MSRP', total = total_MS}
else if (hasAnswer('PRICING_TYPE','NO_PRICES')) { type = 'NO PRICES'}
else if (hasAnswer('PRICING_TYPE','BOTH'))      { type = 'MSRP & SELLING PRICE'}

total = Number(total).toFixed(2);

model = getValue('BOAT_INFO', 'BOAT_REAL_MODEL');

// USER AUTHORIZATION: Check if user is authorized to see CPQ boats
var user = getValue('EOS','USER');
var isCpqAuthorized = true;

// DEBUG: Always log these values
console.log('===== PRINT.JS MODEL DEBUG =====');
console.log('window.isCPQBoat:', window.isCPQBoat);
console.log('window.realmodel:', window.realmodel);
console.log('BOAT_INFO/BOAT_REAL_MODEL:', model);
console.log('User authorized for CPQ:', isCpqAuthorized);

// CPQ FALLBACK - Use cpqLhsData.model_id for CPQ boats (e.g. "22MSB", not "Base Boat")
// window.isCPQBoat is set in packagePricing.js (true when year code detection fails)
if (isCpqAuthorized && window.isCPQBoat) {
    console.log('BOAT_INFO/BOAT_REAL_MODEL was:', model);
    model = (window.cpqLhsData && window.cpqLhsData.model_id)
        ? window.cpqLhsData.model_id
        : window.realmodel;
    console.log('Using model for CPQ boat:', model);
}

// CPQ boats: preserve full model name (e.g., 23ML stays 23ML)
// Legacy boats: strip year code (e.g., 2550GBRDE becomes 2550GBR)
if (isCpqAuthorized && window.isCPQBoat) {
    shortmodel = model; // Keep full model name for CPQ boats
    console.log('CPQ boat: Using full model name:', shortmodel);
} else {
    shortmodel = model.substring(0, model.length - 2); //strip the model year designator
    console.log('Legacy boat: Stripped to shortmodel:', shortmodel);
}
console.log('Final shortmodel for title:', shortmodel);
console.log('===== END MODEL DEBUG =====');
var perfpkgid = getValue('BOAT_INFO', 'STD_PERF_PKG');


if (model.indexOf('2221') >= 0) {
    model = model.substring(2, model.length);
    shortmodel = shortmodel.substring(2, shortmodel.length);
    console.log('Keri', model, shortmodel);
}

if (two > 13) {

    if (model.endsWith('SF')) {
            model = model.substring(0, model.length - 2) + 'SE';
        } //Modified for fakies DG

    boatSpecs = loadByListName('boat_specs', "WHERE MODEL = '" + model + "'");

    // CPQ boats may not have boat_specs data - initialize empty array if needed
    if (!boatSpecs || boatSpecs.length === 0) {
        console.log('No boat_specs found for model:', model, '(likely CPQ boat)');
        boatSpecs = [];
    }
}

if(hasAnswer('PRINT_PHOTO','PRINT_PHOTO')){
    if(hasAnswer('DEALER_QUESTIONS','PHOTO_URL')){
        imgUrl = getValue('DEALER_QUESTIONS','PHOTO_URL');
    }
    else{
        alert('No Photo Uploaded');
    }

}
if (!hasAnswer('PRINT_PHOTO', 'PRINT_PHOTO')) {

    var imgUrl;

    // CPQ boats: use Liquifire image — already loaded in window.cpqLhsData by getunregisteredboats.js
    if (window.isCPQBoat) {
        if (window.cpqLhsData && window.cpqLhsData.image_url) {
            var candidateUrl = window.cpqLhsData.image_url;
            // Validate it's a real boat render — furniture-only URLs have view[] (empty) and asset[furn_m_std]
            var isBoatImage = candidateUrl.indexOf('view[side]') !== -1 ||
                              candidateUrl.indexOf('view[orthographic]') !== -1 ||
                              candidateUrl.indexOf('view[3qtr]') !== -1;
            if (isBoatImage) {
                imgUrl = candidateUrl;
                console.log('Using Liquifire image from cpqLhsData:', imgUrl);
            } else {
                console.log('Liquifire URL for', serial, 'is not a boat render (furniture-only) — falling back to legacy image');
            }
        } else {
            console.log('No Liquifire image in cpqLhsData for', serial);
        }
    }

    // Legacy boats (or CPQ fallback if no image stored): use model_images table
    if (!imgUrl) {
        console.log(model, two);
        modelImg = getModelImage('20' + two, model);
        if (modelImg == undefined) { //set image to a white filler if it is missing.
            imgUrl = 'https://s3.amazonaws.com/eosstatic/images/0/552287f6f0f18aaf52d19f6d/window_sticker_missing_model_white_filler.png';
        } else {
            imgUrl = modelImg.replace(/\s/g, "%20");
        }
    }
}

// CPQ Liquifire images are landscape boat renders — display wider than legacy overhead shots
var img;
if (window.isCPQBoat && imgUrl && imgUrl.indexOf('liquifire') !== -1) {
    img = '<img src="' + imgUrl + '" style="max-width:400px; height:auto;">';
} else {
    img = '<img src="' + imgUrl + '" height="90px">';
}
console.log('perfpkgid', perfpkgid);

// Initialize prfPkgs to prevent undefined error
var prfPkgs = [];

// Get Performance Packages
if (perfpkgid.length !== 0 && perfpkgid.length < 3) {
    console.log('got here');
    
    // SF BOAT FIX: For SF boats (2026 model year), load ALL active packages so we can match to actual engine
    // For non-SF boats, load only the package matching perfpkgid
    var modelEndsWithSE = model && model.endsWith('SE');
    var serialYearIs26 = window.serialYear == 26;
    var modelEndsWithSF = model && model.endsWith('SF');
    var isSFBoatForQuery = (modelEndsWithSE && serialYearIs26) || modelEndsWithSF;
    
    console.log('SF Boat Query Check: model=' + model + ', endsWithSE=' + modelEndsWithSE + ', serialYear=' + window.serialYear + ', serialYearIs26=' + serialYearIs26 + ', endsWithSF=' + modelEndsWithSF + ', isSFBoat=' + isSFBoatForQuery);
    
    if (isSFBoatForQuery) {
        console.log('SF Boat: Loading ALL performance packages for model', model);
        prfPkgs = loadByListName('perf_pkg_spec', "WHERE (MODEL ='" + model + "')");
        console.log('SF Boat: Loaded', prfPkgs.length, 'performance packages');
    } else {
        console.log('Non-SF Boat: Loading single package with PKG_ID=' + perfpkgid);
        prfPkgs = loadByListName('perf_pkg_spec', "WHERE (MODEL ='" + model + "') /*AND (STATUS ='Active') */AND (PKG_ID ='" + perfpkgid + "')");
    }
}

console.log(prfPkgs);
//Lookup the description of the Engine Config and the Fuel Type from Local Lists to print words instead of a number.
var engConfigDesc = '';
var fuelTypeDesc = '';
if (boatSpecs.length > 0 && boatSpecs[0].ENG_CONFIG_ID && boatSpecs[0].FUEL_TYPE_ID) {
    var engConfigLookup = loadList('54f4b35d8ff57802739e8f84', 'LIST/engineConfigID["' + boatSpecs[0].ENG_CONFIG_ID + '"]');
    var fuelTypeLookup = loadList('54f4cdb98ff578e6799e8f84', 'LIST/FUEL_TYPE_ID["' + boatSpecs[0].FUEL_TYPE_ID + '"]');
    if (engConfigLookup && engConfigLookup.length > 0) {
        engConfigDesc = engConfigLookup[0].engineConfigName;
    }
    if (fuelTypeLookup && fuelTypeLookup.length > 0) {
        fuelTypeDesc = fuelTypeLookup[0].FUEL_TYPE_NAME;
    }
}
var stds = createStandardsList(model, '20' + model_year);  //function is at the bottom of this action.
stockno = getValue('DEALER_QUESTIONS','STOCK_NO');
if (stockno === false || stockno === true){stockno = ""}

dio1 = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_1');
dio2 = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_2');
dio3 = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_3');
dio4 = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_4');
dio5 = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_5');
dio6 = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_6');
dio7 = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_7');
dio8 = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_8');
dio9 = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_9');
dio10 = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_10');
dio1price = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_1_PRICE');
dio2price = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_2_PRICE');
dio3price = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_3_PRICE');
dio4price = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_4_PRICE');
dio5price = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_5_PRICE');
dio6price = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_6_PRICE');
dio7price = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_7_PRICE');
dio8price = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_8_PRICE');
dio9price = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_9_PRICE');
dio10price = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_10_PRICE');
diototal = getValue('DEALER_INSTALLED_OPTIONS', 'DIO_TOTAL');
specialdesc = getValue('SPECIAL_PRICING', 'SPECIAL_PRICE_DESC');
specialprice = getValue('SPECIAL_PRICING', 'SPECIAL_PRICE');
if(specialdesc === true || specialdesc === false || specialdesc === undefined){
    specialdesc = '';
}

specialprice = specialprice.toString();
//avoid errors when then use $ and ,
specialprice = specialprice.replace(",",""); //remove , and $ so math works
specialprice = specialprice.replace("$","");

var diovals=[dio1, dio1price, dio2, dio2price, dio3, dio3price, dio4, dio4price, dio5, dio5price, dio6, dio6price, dio7, dio7price, dio8,dio8price, dio9, dio9price, dio10,dio10price];
//console.log(diovals);
$.each(diovals, function(i){
  if (diovals[i] === true || diovals[i] === false){
      diovals[i] = '';
  }
});


var additionalCharge = getValue('EXTRAS','ADD_CHARGE');
if (additionalCharge === ""){additionalCharge = 0;}
console.log('additional charge is', additionalCharge);

if(hasAnswer('PRICING_TYPE','SELLING_PRICE')){
    actualtotal = Number(getValue('EXTRAS','TOTAL_NO_DIO')).toFixed(2);
    actualExtTotal = getValue('EXTRAS','TOTAL_EXT');

}
else if(hasAnswer('PRICING_TYPE','MSRP')){
    actualtotal = Number(getValue('EXTRAS','TOTAL_MS_NO_DIO')).toFixed(2);
    actualExtTotal = getValue('EXTRAS','TOTAL_MS_EXT');

}
else if(hasAnswer('PRICING_TYPE','BOTH')){
    actualtotalSP = Number(getValue('EXTRAS','TOTAL_NO_DIO')).toFixed(2);
    actualExtTotalSP = getValue('EXTRAS','TOTAL_EXT');
    actualtotalMS = Number(getValue('EXTRAS','TOTAL_MS_NO_DIO')).toFixed(2);
    actualExtTotalMS = getValue('EXTRAS','TOTAL_MS_EXT');

}

if (diototal === ''){ diototal = 0}
diototal = Number(diototal).toFixed(2);

var hasActiveDio = [dio1, dio2, dio3, dio4, dio5, dio6, dio7, dio8, dio9, dio10].some(function(d) {
    return d && d !== '' && d !== false && d !== true;
});
if (!hasActiveDio) { diototal = '0.00'; }

var discount = getValue('EXTRAS','DISCOUNT');
if (discount === "" || discount === true || discount === false){discount = 0;}
console.log('discount is ', discount);

var tax = getValue('EXTRAS','TAX_RATE');
if (tax === "" || tax === false || tax === true){tax = 1;}
console.log('tax rate is', tax);

if (tax !== '1') {
    if (hasAnswer('PRICING_TYPE', 'SELLING_PRICE')) {
        totaltax = getValue('EXTRAS', 'TAX');
        totaltax = CurrencyFormat2(totaltax);
    }
    else if (hasAnswer('PRICING_TYPE', 'MSRP')) {
        totaltax = getValue('EXTRAS', 'TAX_MS');
        totaltax = CurrencyFormat2(totaltax);
    }
    else if (hasAnswer('PRICING_TYPE', 'BOTH')) {
        totaltaxSP = getValue('EXTRAS', 'TAX');
        totaltaxMS = getValue('EXTRAS', 'TAX_MS');
        totaltaxSP = CurrencyFormat2(totaltaxSP);
        totaltaxMS = CurrencyFormat2(totaltaxMS);
    }
}
else {
    totaltax = 0;
}


if (!hasAnswer('PRICING_TYPE', 'NO_PRICES') && !hasAnswer('PRICING_TYPE', 'BOTH')) {
    actualExtTotal = actualExtTotal.replace(',', '');
    console.log('actualExtTotal', actualExtTotal);
    totaldue = Number(actualExtTotal) - Number(discount);
    var specialdiscount = Number(specialprice) - totaldue;
    totaldue = CurrencyFormat2(totaldue);
    console.log('totaldue', totaldue);

}
else if (hasAnswer('PRICING_TYPE', 'BOTH')) {
    actualExtTotalSP = actualExtTotalSP.replace(',', '');
    actualExtTotalMS = actualExtTotalMS.replace(',', '');
    totaldueSP = Number(actualExtTotalSP) - Number(discount);
    var specialdiscount = Number(specialprice) - totaldueSP;
    totaldueSP = CurrencyFormat2(totaldueSP);
    totaldueMS = Number(actualExtTotalMS) - Number(discount);
    totaldueMS = CurrencyFormat2(totaldueMS);
}



/*
if(!hasAnswer('HIDE_DIO','YES')){ //don't add the dios into the total if they want to hide them.
var actualtotal = Number(total) + Number(diototal) - Number(discount);

if(tax !== '1'){
//totaltax = (Number(actualtotal) * tax)/100;
totaltax = getValue('EXTRAS','TAX');
actualtotal = Number(actualtotal).toFixed(2) + Number(totaltax);
}
else{
totaltax = 0;
actualtotal = Number(actualtotal).toFixed(2);
console.log('actualtotal',actualtotal);
}

}
else{
    var actualtotal = Number(total) - Number(discount);
    totaltax = (Number(actualtotal) * tax)/100;
    actualtotal = actualtotal + totaltax;
}

*/


var dioVar = "";
if (diovals[0] !== '') {
    dioVar += "<table width=\"100%\" border=\"1\"><tbody> ";
    dioVar += "<tr><td width=\"83%\"><strong>Item Description</strong><\/td><td width=\"17%\" align=\"center\"><strong>Sale Price</strong><\/td><\/tr>";
    dioVar += "<tr><td>" + diovals[0] + "<\/td><td align=\"right\">$" + Number(diovals[1]).toFixed(2) + " <\/td><\/tr>";
}
if (diovals[2] !== '') { dioVar += "<tr><td>" + diovals[2] + "<\/td><td align=\"right\">$" + Number(diovals[3]).toFixed(2) + " <\/td><\/tr>"; }
if (diovals[4] !== '') { dioVar += "<tr><td>" + diovals[4] + "<\/td><td align=\"right\">$" + Number(diovals[5]).toFixed(2) + " <\/td><\/tr>"; }
if (diovals[6] !== '') { dioVar += "<tr><td>" + diovals[6] + "<\/td><td align=\"right\">$" + Number(diovals[7]).toFixed(2) + " <\/td><\/tr>"; }
if (diovals[8] !== '') { dioVar += "<tr><td>" + diovals[8] + "<\/td><td align=\"right\">$" + Number(diovals[9]).toFixed(2) + " <\/td><\/tr>"; }
if (diovals[10] !== '') { dioVar += "<tr><td>" + diovals[10] + "<\/td><td align=\"right\">$" + Number(diovals[11]).toFixed(2) + " <\/td><\/tr>"; }
if (diovals[12] !== '') { dioVar += "<tr><td>" + diovals[12] + "<\/td><td align=\"right\">$" + Number(diovals[13]).toFixed(2) + " <\/td><\/tr>"; }
if (diovals[14] !== '') { dioVar += "<tr><td>" + diovals[14] + "<\/td><td align=\"right\">$" + Number(diovals[15]).toFixed(2) + " <\/td><\/tr>"; }
if (diovals[16] !== '') { dioVar += "<tr><td>" + diovals[16] + "<\/td><td align=\"right\">$" + Number(diovals[17]).toFixed(2) + " <\/td><\/tr>"; }
if (diovals[18] !== '') { dioVar += "<tr><td>" + diovals[18] + "<\/td><td align=\"right\">$" + Number(diovals[19]).toFixed(2) + " <\/td><\/tr>"; }

dioVar += "<\/tbody><\/table>";
dioVar += "";

var wsContents = "";
wsContents += "<!doctype html><html><head><meta charset=\"utf-8\"><title>Bennington Window Sticker<\/title><style type=\"text\/css\">";
wsContents += "body,td,th {";
//wsContents += "    border-style: outset;";
//wsContents += "    border-width: thin;";
wsContents += "    font-family: calibri;}";
wsContents += "table, th, td {";
wsContents += "border-spacing:0px;";
wsContents += "padding:2px;";
wsContents += "font-size:10px;";
wsContents += "    border-collapse:collapse;";
wsContents += "   border: 1px solid black;}";
wsContents += "#stickercontent {";
wsContents += "    height: 11.4in;";
wsContents += "    width: 8.2in;";
wsContents += "    position: relative;}";
wsContents += "#column1 {";
wsContents += "    float:left;";
wsContents += "    height: 11.4in;";
wsContents += "    width: 3.7in;";
wsContents += "    padding-right:5px;}";
wsContents += "#column2 {";
wsContents += "    float:left;";
wsContents += "    height: 11.4in;";
wsContents += "    width: 4.3in;}";
wsContents += "";
wsContents += "#dealeraddr {";
wsContents += "    font-size:12px;";
wsContents += "    text-align:center;}";
wsContents += "#stockhull {";
wsContents += "    font-size:10px;";
wsContents += "    font-weight:bold;";
wsContents += "    text-align:center;}";
wsContents += "#dealername {";
wsContents += "    margin-top:10px;";
wsContents += "    font-size:16px;";
wsContents += "    text-align:center;}";
wsContents += "";
wsContents += "#spectable {";
wsContents += "    font-size:10px;";
wsContents += "    padding-top:10px;";
wsContents += "    padding-bottom:10px;";
wsContents += "    text-align:center;}";
wsContents += "#pagetitle {";
wsContents += "    text-align:center;}";
wsContents += "#overheadimg {";
wsContents += "margin-top:15px;";
wsContents += "margin-bottom:10px;";
wsContents += "text-align:center;}";
wsContents += "#perfpkgtbl {";
wsContents += "    font-size:10px;";
wsContents += "    margin-bottom:10px;}";
wsContents += "#footer {    ";
wsContents += "    font-size: 6px;";
wsContents += "    width: 355px;";
wsContents += "    text-align:left;";
//wsContents += "    postion:absolute;";
//wsContents += "    bottom:0;";
wsContents += "    text-align:center;}";
wsContents += "#disclaimer {    ";
wsContents += "    font-size: 8px;";
wsContents += "    width: 100%;";
wsContents += "    postion:absolute;";
//wsContents += "    bottom:0;";
wsContents += "    text-align:left;}";
wsContents += "#includedoptions {";
wsContents += "    margin-bottom:10px;";
wsContents += "    width:100%;";
wsContents += "    font-size:10px;}";
wsContents += "    padding-bottom:10px;}";
wsContents += "#dealerinstalledoptions {";
wsContents += "    font-size:10px;";
wsContents += "    width:100%;";
wsContents += "    margin-bottom:10px;}";
wsContents += "#totals {";
//wsContents += "    position:absolute;";
wsContents += "    bottom:0;";
wsContents += "    font-size:20px;";
wsContents += "    margin-top:10px;";
wsContents += "    width:100%;}";
//wsContents += "    margin-bottom:15px;}";
wsContents += ".totals td {";
wsContents += "    font-size:14px;}";
wsContents += ".title {";
wsContents += "    text-transform: uppercase;";
wsContents += "    color: #FBFBFB;";
wsContents += "    background-color:#000000;";
wsContents += "    text-align:center;}";
wsContents += "#special {";
//wsContents += "    position:absolute;";
//wsContents += "    bottom:0;";
wsContents += "    font-size:20px;";
wsContents += "    margin-top:10px;";
wsContents += "    width:100%;}";
//wsContents += "    margin-bottom:15px;}";

wsContents += ".special td {";
wsContents += "    font-size:14px;}";
wsContents += ".specialtitle {";
wsContents += "    text-transform: uppercase;";
wsContents += "    color: #FBFBFB;";
wsContents += "    background-color:#ff0000;";
wsContents += "    text-align:center;}";


wsContents += "#standards {";
wsContents += "    font-size: 9px;}";
wsContents += "<\/style>";
wsContents += "<\/head>";
wsContents += "<body>";
wsContents += "<div id=\"stickercontent\">";
wsContents += "  <div class=\"column\" id=\"column1\">";
wsContents += "    <div id=\"logo\"><div align=\"center\"><img src=\"https:\/\/s3.amazonaws.com\/eosstatic\/images\/0\/5536c2ba8ff578c9234a8cd6\/Bennington_Pontoon_Boats_chromelogo_small.png\" width=\"235\" height=\"55\"\/><\/div><\/div>";
wsContents += "    <div id=\"dealername\">"+ dealerdba +"<\/div>";
wsContents += "    <div id=\"dealeraddr\">";
wsContents += "      <p>" + dealeraddr1 + "<br>";
//wsContents += "     " + dealeraddr2 + "<br>";
wsContents += "     " + dealercity + ", " + dealerstate + " " + dealerzip +" <br>";
wsContents += "     " + dealerweb + "<br>";
wsContents += "     "+ dealerphone+"<\/p>";
wsContents += "    <\/div>";
wsContents += "     <div class=\"title\" id=\"boatinfo\">BOAT INFORMATION<\/div>";
wsContents += "    <div id=\"stockhull\">Stock #:<u>" + stockno + "<\/u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Hull #: <u>"+ serial +" <\/u><\/div>";

// USER AUTHORIZATION: Check if user is authorized to see CPQ boats
var user = getValue('EOS','USER');
var isCpqAuthorized = true;

// CPQ boats: Use window.cpqLhsData if available AND user is authorized, otherwise use legacy boatSpecs
if (isCpqAuthorized && window.cpqLhsData && window.cpqLhsData.model_id) {
    console.log('Using CPQ LHS data for specs section');
    var cpqData = window.cpqLhsData;

    // Helper function to escape HTML special characters (especially quotes in measurements like 22'-11.5")
    function escapeHtml(text) {
        if (!text) return '';
        var map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.toString().replace(/[&<>"']/g, function(m) { return map[m]; });
    }

    // Convert pontoon gauge to diameter display (0.08 -> 25", 0.10 -> 27")
    var pontoonDiameter = '';
    if (cpqData.pontoon_gauge === '0.08' || cpqData.pontoon_gauge === 0.08) {
        pontoonDiameter = '25"';
    } else if (cpqData.pontoon_gauge === '0.10' || cpqData.pontoon_gauge === 0.10) {
        pontoonDiameter = '27"';
    } else if (cpqData.tube_height) {
        pontoonDiameter = escapeHtml(cpqData.tube_height);
    }

    wsContents += "    <div id=\"spectable\">";
    wsContents += "      <table width=\"300\" border=\"1\" align=\"center\">";
    wsContents += "        <tbody>";
    wsContents += "          <tr>";
    wsContents += "            <td width=\"163\"><strong>SPEC\/CAPACITY</strong><\/td>";
    wsContents += "            <td width=\"121\"><strong>US</strong><\/td>";
    wsContents += "          <\/tr>";
    wsContents += "          <tr>";
    wsContents += "            <td align=\"left\">LOA:<\/td>";
    wsContents += "            <td>" + escapeHtml(cpqData.loa || '') + "<\/td>";
    wsContents += "          <\/tr>";
    wsContents += "          <tr>";
    wsContents += "            <td align=\"left\">Pontoon Length:<\/td>";
    wsContents += "            <td>" + escapeHtml(cpqData.pontoon_length || cpqData.loa || '') + "<\/td>";
    wsContents += "          <\/tr>";
    wsContents += "          <tr>";
    wsContents += "            <td align=\"left\">Deck Length:<\/td>";
    wsContents += "            <td>" + escapeHtml(cpqData.deck_length || '') + "<\/td>";
    wsContents += "          <\/tr>";
    wsContents += "          <tr>";
    wsContents += "            <td align=\"left\">Beam:<\/td>";
    wsContents += "            <td>" + escapeHtml(cpqData.beam || '') + "<\/td>";
    wsContents += "          <\/tr>";
    wsContents += "          <tr>";
    wsContents += "            <td align=\"left\">Pontoon Diameter:<\/td>";
    wsContents += "            <td>" + pontoonDiameter + "<\/td>";
    wsContents += "          <\/tr>";
    wsContents += "          <tr>";
    wsContents += "            <td align=\"left\">Engine Configuration:<\/td>";
    wsContents += "            <td>" + escapeHtml(cpqData.engine_configuration || 'Single Outboard') + "<\/td>";
    wsContents += "          <\/tr>";
    wsContents += "          <tr>";
    wsContents += "            <td align=\"left\">Fuel Capacity (standard, see<br>options):<\/td>";
    wsContents += "            <td>" + escapeHtml(cpqData.fuel_capacity || '') + "<\/td>";
    wsContents += "          <\/tr>";
    wsContents += "        <\/tbody>";
    wsContents += "      <\/table>";
    wsContents += "    <\/div>";
} else if (boatSpecs.length > 0) {
    // Legacy boats: Use boatSpecs from EOS list
    wsContents += "    <div id=\"spectable\">";
    wsContents += "      <table width=\"300\" border=\"1\" align=\"center\">";
    wsContents += "        <tbody>";
    wsContents += "          <tr>";
    wsContents += "            <td width=\"163\"><strong>SPEC\/CAPACITY</strong><\/td>";
    wsContents += "            <td width=\"121\"><strong>US</strong><\/td>";
    wsContents += "          <\/tr>";
    wsContents += "          <tr>";
    wsContents += "            <td align=\"left\">LOA:<\/td>";
    wsContents += "            <td>" + boatSpecs[0].LOA + "<\/td>";
    wsContents += "          <\/tr>";
    wsContents += "          <tr>";
    wsContents += "            <td align=\"left\">Pontoon Length:<\/td>";
    wsContents += "            <td>" + boatSpecs[0].PONT_LEN + "<\/td>";
    wsContents += "          <\/tr>";
    wsContents += "          <tr>";
    wsContents += "            <td align=\"left\">Deck Length:<\/td>";
    wsContents += "            <td>" + boatSpecs[0].DECK_LEN + "<\/td>";
    wsContents += "          <\/tr>";
    wsContents += "          <tr>";
    wsContents += "            <td align=\"left\">Beam:<\/td>";
    wsContents += "            <td>" + boatSpecs[0].BEAM + "<\/td>";
    wsContents += "          <\/tr>";
    wsContents += "          <tr>";
    wsContents += "            <td align=\"left\">Pontoon Diameter:<\/td>";
    wsContents += "            <td>" + boatSpecs[0].PONT_DIAM + "<\/td>";
    wsContents += "          <\/tr>";
    wsContents += "          <tr>";
    wsContents += "            <td align=\"left\">Engine Configuration:<\/td>";
    wsContents += "            <td>" + engConfigDesc + "<\/td>";
    wsContents += "          <\/tr>";
    wsContents += "          <tr>";
    wsContents += "            <td align=\"left\">Fuel Capacity (standard, see options):<\/td>";
    wsContents += "            <td>" + boatSpecs[0].FUEL_CAP + "<\/td>";
    wsContents += "          <\/tr>";
    wsContents += "        <\/tbody>";
    wsContents += "      <\/table>";
    wsContents += "    <\/div>";
} else {
    console.log('Skipping boat specs section - no data available for this model');
}

// CPQ boats: Use window.cpqLhsData for performance specs if user is authorized, otherwise use legacy prfPkgs
if (isCpqAuthorized && window.cpqLhsData && window.cpqLhsData.model_id) {
    console.log('Using CPQ LHS data for performance specs section');
    var cpqData = window.cpqLhsData;

    // Format hull weight (2988.0 -> 2,988 lbs) - keep as-is if it contains "/"
    var hullWeight = '';
    if (cpqData.hull_weight) {
        var weightStr = String(cpqData.hull_weight);
        if (weightStr.includes('/')) {
            // Dual values like "2453/2783" - format both numbers
            var weights = weightStr.split('/');
            var formatted = weights.map(function(w) {
                return Math.round(parseFloat(w.trim())).toLocaleString();
            }).join('/');
            hullWeight = formatted + ' lbs';
        } else {
            // Single value
            hullWeight = Math.round(parseFloat(cpqData.hull_weight)).toLocaleString() + ' lbs';
        }
    }

    // Format max HP (150.0 -> 150 HP) - keep as-is if it contains "/"
    var maxHP = '';
    if (cpqData.max_hp) {
        var hpStr = String(cpqData.max_hp);
        if (hpStr.includes('/')) {
            // Dual values like "90/150" - format both numbers
            var hps = hpStr.split('/');
            var formatted = hps.map(function(h) {
                return Math.round(parseFloat(h.trim()));
            }).join('/');
            maxHP = formatted + ' HP';
        } else {
            // Single value
            maxHP = Math.round(parseFloat(cpqData.max_hp)) + ' HP';
        }
    }

    // Format pontoon gauge (0.08 -> 0.08)
    var pontoonGauge = '';
    if (cpqData.pontoon_gauge) {
        pontoonGauge = parseFloat(cpqData.pontoon_gauge).toFixed(2);
    }

    // Format package name using actual API values (no_of_tubes, pontoon_gauge, transom)
    var packageName = 'Standard Package';
    if (cpqData.perf_package_id && cpqData.no_of_tubes) {
        var tubes = Math.round(parseFloat(cpqData.no_of_tubes));
        // Derive tube diameter from pontoon_gauge (0.08 -> 25", 0.10 -> 27") — from API
        var tubeSize = '';
        if (cpqData.pontoon_gauge === '0.08' || cpqData.pontoon_gauge === 0.08) {
            tubeSize = '25';
        } else if (cpqData.pontoon_gauge === '0.10' || cpqData.pontoon_gauge === 0.10) {
            tubeSize = '27';
        }
        packageName = tubes + '. With' + (tubeSize ? ' ' + tubeSize + '"' : '') + ' Tubes';

        // Use transom field from API directly
        if (cpqData.transom) {
            packageName += ' (' + cpqData.transom + '" transom)';
        }
    }

    wsContents += "    <div class=\"title\">PERFORMANCE PACKAGE SPECS<\/div>";
    wsContents += "    <div id=\"perfpkgtbl\">";
    wsContents += "    <table width=\"355\" border=\"1\"><tbody><tr>";
    wsContents += "            <td colspan=\"4\" align=\"center\">" + packageName + "<\/td><\/tr>";
    wsContents += "          <tr><td>Person Capacity<\/td><td>Hull Weight<\/td><td>Max HP<\/td><td>Pontoon Gauge<\/td><\/tr>";
    wsContents += "          <tr><td>" + (cpqData.person_capacity || '') + "<\/td><td>" + hullWeight + "<\/td><td>" + maxHP + "<\/td><td>" + pontoonGauge + "<\/td><\/tr>";
    wsContents += "        <\/tbody><\/table>";
    wsContents += "    <\/div>";
} else if (perfpkgid.length !== 0 && perfpkgid.length < 3 && perfpkgid !== undefined) {
    // Legacy boats: Use prfPkgs from EOS list
    
    // SF BOAT FIX: Match performance package to actual engine HP
    // For SF boats (2026 model using 2025 matrix), find package matching actual engine
    // Note: SF models get transformed to SE in packagePricing.js, so we check for serial year 26 + SE suffix
    console.log('SF Boat Fix Debug: model=' + model + ', serialYear=' + window.serialYear + ', type=' + typeof window.serialYear);
    var isSFBoat = (model && model.endsWith('SE') && window.serialYear == 26) || 
                   (model && model.endsWith('SF'));
    
    console.log('SF Boat Fix Debug: isSFBoat=' + isSFBoat);
    
    if (isSFBoat && window.boatoptions && window.boatoptions.length > 0) {
        console.log('SF Boat detected - checking for correct performance package match');
        
        // Find engine in boatoptions
        var engineItem = null;
        for (var i = 0; i < window.boatoptions.length; i++) {
            if (window.boatoptions[i].ItemMasterProdCat === 'EN7') {
                engineItem = window.boatoptions[i];
                break;
            }
        }

        if (engineItem && prfPkgs && prfPkgs.length > 0) {
            // Extract HP from engine description
            var engineHP = null;
            var engineDesc = engineItem.ItemDesc1 || '';
            console.log('SF Boat Fix: Engine description:', engineDesc);

            // Try "200HP" format first
            var hpMatch = engineDesc.match(/(\d+)\s*HP/i);
            if (hpMatch) {
                engineHP = parseInt(hpMatch[1]);
            } else {
                // Fallback: look for standalone numbers (100-600)
                var numMatch = engineDesc.match(/\b(1\d{2}|2\d{2}|3\d{2}|4\d{2}|5\d{2}|600)\b/);
                if (numMatch) {
                    engineHP = parseInt(numMatch[1]);
                }
            }

            // Find matching performance package
            if (engineHP) {
                console.log('SF Boat Fix: Looking for package with HP matching', engineHP);
                var matchingIndex = -1;
                for (var j = 0; j < prfPkgs.length; j++) {
                    var pkgHP = prfPkgs[j].MAX_HP;
                    if (pkgHP) {
                        var hpNumMatch = String(pkgHP).match(/\d+/);
                        if (hpNumMatch) {
                            var pkgHPNum = parseInt(hpNumMatch[0]);
                            if (pkgHPNum === engineHP) {
                                console.log('SF Boat Fix: Found matching package', prfPkgs[j].PKG_NAME, 'with HP', pkgHP);
                                matchingIndex = j;
                                break;
                            }
                        }
                    }
                }
                
                // Fallback: if no exact match, find lowest package whose MaxHP >= engineHP
                // e.g. 350HP engine on 25QXSBA maps to ESP at 500HP (no 350HP package exists)
                if (matchingIndex === -1) {
                    var bestIndex = -1;
                    var bestHP = Infinity;
                    for (var k = 0; k < prfPkgs.length; k++) {
                        var fbHP = prfPkgs[k].MAX_HP;
                        if (fbHP) {
                            var fbHPNum = parseInt(String(fbHP).match(/\d+/)[0]);
                            if (fbHPNum >= engineHP && fbHPNum < bestHP) {
                                bestHP = fbHPNum;
                                bestIndex = k;
                            }
                        }
                    }
                    if (bestIndex !== -1) {
                        console.log('SF Boat Fix: No exact match, using lowest capable package', prfPkgs[bestIndex].PKG_NAME, 'with HP', prfPkgs[bestIndex].MAX_HP);
                        matchingIndex = bestIndex;
                    }
                }

                // Swap first package with matching one
                if (matchingIndex > 0) {
                    console.log('SF Boat Fix: Swapping package index 0 with index', matchingIndex);
                    var temp = prfPkgs[0];
                    prfPkgs[0] = prfPkgs[matchingIndex];
                    prfPkgs[matchingIndex] = temp;
                } else if (matchingIndex === 0) {
                    console.log('SF Boat Fix: First package already matches - no swap needed');
                } else {
                    console.log('SF Boat Fix: No suitable package found for HP', engineHP);
                }
                
                // Check if selected package has valid capacity, if not find one with valid capacity
                if (prfPkgs[0].CAP && (prfPkgs[0].CAP === '0' || prfPkgs[0].CAP === '0 People' || prfPkgs[0].CAP === 0 || String(prfPkgs[0].CAP).match(/^(0|\s*0\s*people?)$/i))) {
                    console.log('SF Boat Fix: Selected package has 0 capacity, looking for package with valid capacity');
                    var validCapIndex = -1;
                    var bestDiff = Infinity;
                    
                    for (var m = 0; m < prfPkgs.length; m++) {
                        var pkg = prfPkgs[m];
                        var hasValidCap = pkg.CAP && 
                                         pkg.CAP !== '0' && 
                                         pkg.CAP !== '0 People' && 
                                         pkg.CAP !== 0 &&
                                         !String(pkg.CAP).match(/^(0|\s*0\s*people?)$/i);
                        
                        if (hasValidCap && pkg.MAX_HP) {
                            var pkgHPNumValid = parseInt(String(pkg.MAX_HP).match(/\d+/)[0]);
                            var diffValid = Math.abs(pkgHPNumValid - engineHP);
                            
                            if (diffValid < bestDiff) {
                                bestDiff = diffValid;
                                validCapIndex = m;
                            }
                        }
                    }
                    
                    if (validCapIndex >= 0 && validCapIndex !== 0) {
                        console.log('SF Boat Fix: Swapping to package with valid capacity - index', validCapIndex, 'HP:', prfPkgs[validCapIndex].MAX_HP, 'Cap:', prfPkgs[validCapIndex].CAP);
                        var tempCap = prfPkgs[0];
                        prfPkgs[0] = prfPkgs[validCapIndex];
                        prfPkgs[validCapIndex] = tempCap;
                    } else if (validCapIndex === 0) {
                        console.log('SF Boat Fix: First package already has valid capacity');
                    } else {
                        console.log('SF Boat Fix: No package with valid capacity found');
                    }
                }
            } else {
                console.log('SF Boat Fix: Could not extract HP from engine description');
            }
        } else {
            console.log('SF Boat Fix: No engine item found in boatoptions');
        }
    }
    // END SF BOAT FIX
    
    wsContents += "    <div class=\"title\">PERFORMANCE PACKAGE SPECS<\/div>";
    wsContents += "    <div id=\"perfpkgtbl\">";
    wsContents += "    <table width=\"355\" border=\"1\"><tbody><tr>";
    wsContents += "            <td colspan=\"4\" align=\"center\">" + prfPkgs[0].PKG_NAME + "<\/td><\/tr>";
    wsContents += "          <tr><td>Person Capacity<\/td><td>Hull Weight<\/td><td>Max HP<\/td><td>Pontoon Gauge<\/td><\/tr>";
    wsContents += "          <tr><td>" + prfPkgs[0].CAP + "<\/td><td>" + prfPkgs[0].WEIGHT + "<\/td><td>" + prfPkgs[0].MAX_HP + "<\/td><td>" + prfPkgs[0].PONT_GAUGE + "<\/td><\/tr>";
    wsContents += "        <\/tbody><\/table>";
    wsContents += "    <\/div>";
}

wsContents += "    <div class=\"title\" id=\"standardstitle\">STANDARD FEATURES<\/div>";

// CPQ boats: Use window.cpqStandardFeatures if user is authorized and data is available, otherwise use legacy stds
if (isCpqAuthorized && window.cpqStandardFeatures) {
    console.log('Using CPQ standard features');
    var standardsHtml = '';

    // Format: Area • feature1 • feature2 • feature3 •
    var areas = ['Interior Features', 'Exterior Features', 'Console Features', 'Warranty'];
    var areaLabels = {
        'Interior Features': 'Interior',
        'Exterior Features': 'Exterior',
        'Console Features': 'Console Features',
        'Warranty': 'Warranty'
    };

    areas.forEach(function(area) {
        if (window.cpqStandardFeatures[area] && window.cpqStandardFeatures[area].length > 0) {
            standardsHtml += '<strong>' + areaLabels[area] + '<\/strong> • ';
            standardsHtml += window.cpqStandardFeatures[area].join(' • ') + ' •<br>';
        }
    });

    wsContents += "    <div id=\"standards\">" + standardsHtml + "<\/div> ";
} else {
    console.log('Using legacy standards list');
    wsContents += "    <div id=\"standards\">" + stds + "<\/div> ";
}

wsContents += "  <\/div>";
wsContents += "  <div class=\"column\" id=\"column2\">";
// DEBUG: Log values right before title construction
console.log('===== TITLE CONSTRUCTION DEBUG =====');
console.log('model_year:', model_year);
console.log('shortmodel:', shortmodel);
console.log('type:', type);
console.log('Title will be: 20' + model_year + ' ' + shortmodel + ' ' + type);
console.log('===== END TITLE DEBUG =====');
if(boatPricing =='SV'){
    wsContents += "    <div id=\"pagetitle\">20"+model_year +" " + shortmodel + "<\/div>";
}else{
    wsContents += "    <div id=\"pagetitle\">20"+model_year +" " + shortmodel + " " + type  +"<\/div>";
}
wsContents += "    <div id=\"overheadimg\"> " + img + "<\/div>";

wsContents += "    <div class=\"title\">INCLUDED OPTIONS <\/div>";

// Clone the table and apply active filters before printing
var includedEl = document.getElementById('included');
console.log('=== STRUCK ROWS PRINT DEBUG ===');
console.log('document.getElementById("included"):', includedEl ? 'FOUND' : 'NULL');
console.log('window.struckRows:', window.struckRows ? JSON.stringify(Array.from(window.struckRows)) : 'undefined');
var includedTableHtml = includedEl ? includedEl.outerHTML : '';
var tempDiv = document.createElement('div');
tempDiv.innerHTML = includedTableHtml;
var tableClone = tempDiv.querySelector('#included');
console.log('tableClone:', tableClone ? 'FOUND' : 'NULL');
if (tableClone) {
    var allRows = tableClone.querySelectorAll('tbody tr');
    console.log('Total rows in clone:', allRows.length);
    allRows.forEach(function(r, idx) {
        var eb = r.querySelector('.row-eye-btn');
        var rk = eb ? eb.getAttribute('data-rowkey') : '(no eye btn)';
        console.log('Row', idx, '| data-struck:', r.getAttribute('data-struck'), '| rowKey:', rk, '| inStruckRows:', window.struckRows ? window.struckRows.has(rk) : 'N/A');
    });
    console.log('=== END STRUCK ROWS DEBUG ===');
    var rows = tableClone.querySelectorAll('tbody tr');
    rows.forEach(function(row) {
        // Filter "No..." items
        if (window.hideUnselectedBoatOptions) {
            var firstTd = row.querySelector('td:first-child');
            if (firstTd) {
                var descSpan = firstTd.querySelector('.desc-editable');
                var desc = (descSpan ? descSpan.textContent : firstTd.textContent).trim().toUpperCase();
                if (desc.startsWith('NO ') || desc.startsWith('NO-')) {
                    row.remove();
                    return;
                }
            }
        }
        // Struck rows are excluded from the window sticker entirely
        // Primary check: data-struck attribute stamped at click time (most reliable)
        if (row.getAttribute('data-struck') === 'true') {
            row.remove();
            return;
        }
        // Secondary check: key in window.struckRows
        if (window.struckRows && window.struckRows.size > 0) {
            var eyeBtn = row.querySelector('.row-eye-btn');
            if (eyeBtn && window.struckRows.has(eyeBtn.getAttribute('data-rowkey'))) {
                row.remove();
                return;
            }
        }
        // Fallback: remove any row whose cells are visually struck (line-through inline style)
        if (row.querySelector('td[style*="line-through"]')) {
            row.remove();
            return;
        }
    });
    // Remove write-in rows from DOM capture — they will be re-added from window.writeInItems below
    // Use both class and data attribute to ensure removal regardless of EOS serialization quirks
    tableClone.querySelectorAll('tr.writein-row, tr[data-writein="true"]').forEach(function(row) { row.remove(); });

    // Apply description edits from window.descEdits (keyed by rowKey)
    if (window.descEdits) {
        tableClone.querySelectorAll('.desc-editable[data-rowkey]').forEach(function(span) {
            var key = span.getAttribute('data-rowkey');
            if (key && window.descEdits[key] !== undefined) {
                span.textContent = window.descEdits[key];
            }
        });
    }

    // Append write-in items from window.writeInItems
    if (window.writeInItems && window.writeInItems.length > 0) {
        var tbody = tableClone.querySelector('tbody');
        if (tbody) {
            window.writeInItems.forEach(function(item) {
                // Skip struck write-in rows
                if (window.struckRows && window.struckRows.has(item.rowKey)) return;
                var tr = document.createElement('tr');
                var tdDesc = document.createElement('td');
                tdDesc.textContent = item.desc || '';
                tr.appendChild(tdDesc);
                var tdItem = document.createElement('td');
                tdItem.textContent = item.itemno || '';
                tr.appendChild(tdItem);
                var tdQty = document.createElement('td');
                tdQty.align = 'center';
                tdQty.textContent = item.qty || '1';
                tr.appendChild(tdQty);
                ['DC', 'MS', 'SP'].forEach(function(type) {
                    var td = document.createElement('td');
                    td.setAttribute('type', type);
                    td.align = 'right';
                    td.textContent = item[type.toLowerCase()] || '';
                    // Match column visibility to pricing type so write-in rows stay aligned
                    if (type === 'DC' && !hasAnswer('PRICING_TYPE', 'DEALER_COST')) { td.style.display = 'none'; }
                    if (type === 'MS' && !hasAnswer('PRICING_TYPE', 'MSRP') && !hasAnswer('PRICING_TYPE', 'BOTH')) { td.style.display = 'none'; }
                    if (type === 'SP' && !hasAnswer('PRICING_TYPE', 'SELLING_PRICE') && !hasAnswer('PRICING_TYPE', 'BOTH')) { td.style.display = 'none'; }
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });
        }
    }

    // Strip eye button elements so they don't appear in print output
    tableClone.querySelectorAll('.row-eye-btn').forEach(function(btn) { btn.remove(); });
    // Strip contenteditable and dashed outlines
    tableClone.querySelectorAll('[contenteditable]').forEach(function(el) {
        el.removeAttribute('contenteditable');
        el.style.outline = '';
    });
    includedTableHtml = tableClone.outerHTML;
}

wsContents += "    <div id=\"includedoptions\">" + includedTableHtml + "<\/div>";

// Add write-in item prices to totals
var writeInMS = 0, writeInSP = 0, writeInDC = 0;
if (window.writeInItems && window.writeInItems.length > 0) {
    window.writeInItems.forEach(function(item) {
        if (window.struckRows && window.struckRows.has(item.rowKey)) return;
        var qty = parseFloat(item.qty) || 1;
        writeInMS += (parseFloat((item.ms || '').replace(/[$,]/g, '')) || 0) * qty;
        writeInSP += (parseFloat((item.sp || '').replace(/[$,]/g, '')) || 0) * qty;
        writeInDC += (parseFloat((item.dc || '').replace(/[$,]/g, '')) || 0) * qty;
    });
}
var taxRate = (tax !== '1') ? Number(tax) / 100 : 0;
function addWriteIn(base, extra) { return CurrencyFormat2(Number(String(base).replace(/[$,]/g, '')) + extra); }
if (hasAnswer('PRICING_TYPE', 'SELLING_PRICE') && writeInSP !== 0) {
    actualtotal = (Number(actualtotal) + writeInSP).toFixed(2);
    if (tax !== '1') { totaltax = addWriteIn(totaltax, writeInSP * taxRate); }
    totaldue = addWriteIn(totaldue, writeInSP + writeInSP * taxRate);
} else if (hasAnswer('PRICING_TYPE', 'MSRP') && writeInMS !== 0) {
    actualtotal = (Number(actualtotal) + writeInMS).toFixed(2);
    if (tax !== '1') { totaltax = addWriteIn(totaltax, writeInMS * taxRate); }
    totaldue = addWriteIn(totaldue, writeInMS + writeInMS * taxRate);
} else if (hasAnswer('PRICING_TYPE', 'DEALER_COST') && writeInDC !== 0) {
    actualtotal = (Number(actualtotal) + writeInDC).toFixed(2);
    if (tax !== '1') { totaltax = addWriteIn(totaltax, writeInDC * taxRate); }
    totaldue = addWriteIn(totaldue, writeInDC + writeInDC * taxRate);
} else if (hasAnswer('PRICING_TYPE', 'BOTH')) {
    if (writeInMS !== 0) {
        actualtotalMS = (Number(actualtotalMS) + writeInMS).toFixed(2);
        if (tax !== '1') { totaltaxMS = addWriteIn(totaltaxMS, writeInMS * taxRate); }
        totaldueMS = addWriteIn(totaldueMS, writeInMS + writeInMS * taxRate);
    }
    if (writeInSP !== 0) {
        actualtotalSP = (Number(actualtotalSP) + writeInSP).toFixed(2);
        if (tax !== '1') { totaltaxSP = addWriteIn(totaltaxSP, writeInSP * taxRate); }
        totaldueSP = addWriteIn(totaldueSP, writeInSP + writeInSP * taxRate);
    }
}

if (!hasAnswer('HIDE_DIO', 'YES')) {  //allow the dios to be filled out, but not print.
    wsContents += "    <div id=\"diotitle\" class=\"title\">DEALER INSTALLED OPTIONS<\/div>";
    wsContents += "    <div id=\"dealerinstalledoptions\">" + dioVar + "<\/div>";
}

if (!hasAnswer('PRICING_TYPE', 'NO_PRICES') && !hasAnswer('PRICING_TYPE', 'BOTH')) { //don't show any totals if no prices is set as a pricing type.
    wsContents += "    <div class= \"totals\" id=\"totals\"><table width=\"100%\" border=\"1\" align=\"center\">";
    wsContents += "    <div class=\"title\">TOTALS<\/div>";
    wsContents += "  <tbody><tr><td colspan=\"2\"><div align=\"center\">" + dealerdba + "<\/div><\/td><\/tr>";
    // EJM 1.8.24 changed series to SV_23 for "Low, No Haggle Pricing" to appear
    if(type =='MSRP' && boatPricing =='SV_23'){        wsContents += "    <tr><td width=\"191\">Low, No Haggle Pricing:<\/td><td align=\"right\" width=\"163\">$" + CurrencyFormat2(actualtotal) + "<\/td><\/tr>";    }
    else{        wsContents += "    <tr><td width=\"191\">" + type + ":<\/td><td align=\"right\" width=\"163\">$" + CurrencyFormat2(actualtotal) + "<\/td><\/tr>";    }
    if (!hasAnswer('HIDE_DIO', 'YES')) {  //allow the dios to be filled out, but not print.
        wsContents += "    <tr><td>DEALER ADD-ONS:<\/td><td align=\"right\">$" + CurrencyFormat2(diototal) + "<\/td><\/tr>";
    }
    if (tax != 1) {        wsContents += "    <tr><td>" + tax + " % TAX:<\/td><td align=\"right\">$" + totaltax + "<\/td><\/tr>";    }
    if (discount != 0) {        wsContents += "    <tr><td>DEPOSIT:<\/td><td align=\"right\">$ -" + discount + "<\/td><\/tr>";    }
    if(boatPricing =='SV'){
       wsContents += "    <tr><td><strong>TOTAL:<\/strong> <div style=\"font-size: 10px\">*Excludes freight and prep</div><\/td><td align=\"right\">$" + totaldue + "<\/td><\/tr>";
    }else{
        wsContents += "    <tr><td><strong>TOTAL:<\/strong><\/td><td align=\"right\">$" + totaldue + "<\/td><\/tr>";
    }


    if(type =='MSRP' && boatPricing =='SV_23'){
        //EJM 1.8.24 Changed series to SV_23 fpr "*Join the Family Promotion Priced with Low, No Haggle Pricing
        wsContents += "  <\/tbody><\/table><div style=\"font-size: 13px\"><strong>*Join the Family Promotion Priced with Low, No Haggle Pricing</strong></div><\/div> ";
    }else{
        wsContents += "  <\/tbody><\/table><\/div> ";
    }
}
//edit here for both msrp and selling price
if (hasAnswer('PRICING_TYPE', 'BOTH')) { //don't show any totals if no prices is set as a pricing type.
    wsContents += "    <div class= \"totals\" id=\"totals\"><table width=\"100%\" border=\"1\" align=\"center\">";
    wsContents += "    <div class=\"title\">TOTALS<\/div>";
    wsContents += "    <tbody><tr><td colspan=\"3\"><div align=\"center\">" + dealerdba + "<\/div><\/td><\/tr>";
    // EJM 1.8.24 changed series to SV_23 for "Low, No Haggle Pricing"
    if(boatPricing =='SV_23'){
        wsContents += "    <tr><td width=\"191\"></td><td width=\"100\"align=\"center\"><strong>Low, No Haggle Pricing</strong><\/td><td align=\"center\"><strong>SALE</strong></td></tr>";
    }else{
        wsContents += "    <tr><td width=\"191\"></td><td width=\"100\"align=\"center\"><strong>MSRP</strong><\/td><td align=\"center\"><strong>SALE</strong></td></tr>";
    }
    wsContents += "    <tr><td width=\"191\"></td><td width=\"100\" align=\"right\">$" + CurrencyFormat2(actualtotalMS) + "<\/td><td align=\"right\">$" + CurrencyFormat2(actualtotalSP) + "</td></tr>";
    //wsContents += "    <td align=\"right\" width=\"163\">$"+ CurrencyFormat2(actualtotal) + "<\/td><\/tr>";
    if (!hasAnswer('HIDE_DIO', 'YES')) {  //allow the dios to be filled out, but not print.
        wsContents += "    <tr><td>DEALER ADD-ONS:<\/td><td align=\"right\">$" + CurrencyFormat2(diototal) + "<\/td><td align=\"right\">$" + CurrencyFormat2(diototal) + "<\/td><\/tr>";
    }

    if (tax != 1) { wsContents += "    <tr><td>" + tax + " % TAX:<\/td><td align=\"right\">$" + totaltaxMS + "<\/td><td align=\"right\">$" + totaltaxSP + "<\/td><\/tr>"; }
    if (discount != 0) { wsContents += "    <tr><td>DEPOSIT:<\/td><td align=\"right\">$ -" + discount + "<\/td><\/tr>"; }
        if(boatPricing =='SV'){
            wsContents += "    <tr><td><strong>TOTAL:<\/strong> <div style=\"font-size: 10px\">*Excludes freight and prep</div><\/td><td align=\"right\">$" + totaldueMS + "<\/td><td align=\"right\">$" + totaldueSP + "<\/td><\/tr>";
        }else{
            wsContents += "    <tr><td><strong>TOTAL:<\/strong><\/td><td align=\"right\">$" + totaldueMS + "<\/td><td align=\"right\">$" + totaldueSP + "<\/td><\/tr>";
        }

    //Added footer text underneath the pricing
    //EJM 1.8.24 changed series to SV_23 for "*Join the Family Promotion Priced with Low, No Haggle Pricing"
    if(boatPricing =='SV_23'){
        wsContents += "  <\/tbody><\/table><div style=\"font-size: 13px\"><strong>*Join the Family Promotion Priced with Low, No Haggle Pricing</strong></div><\/div> ";

    }else{
        wsContents += "  <\/tbody><\/table><\/div> ";
    }
}

if(hasAnswer('PRINT_SPECIAL_PRICE','YES') && !hasAnswer('PRICING_TYPE','NO_PRICES')){
    wsContents += "    <div class= \"special\" id=\"special\"><table width=\"100%\" border=\"1\" align=\"center\">";
    wsContents += "    <div class=\"specialtitle\">SPECIAL SAVINGS<\/div>";
    wsContents += "    <tbody><tr><td colspan=\"2\"><div align=\"center\">"+ specialdesc + "<\/div><\/td><\/tr>";
    wsContents += "    <tr><td width=\"191\">SPECIAL DISCOUNT:</td><td width=\"100\"align=\"right\"><strong>$"+CurrencyFormat2(specialdiscount) +"</strong><\/td></tr>";
    wsContents += "    <tr><td width=\"191\">FINAL SELLING PRICE</td><td width=\"100\" align=\"right\"><strong>$" + CurrencyFormat2(specialprice)+"</strong><\/td></tr>";
    wsContents += "  <\/tbody><\/table><\/div><\/div>  ";
}

if (hasAnswer('PRINT_SPECIAL_PRICE', 'YES') && hasAnswer('PRICING_TYPE', 'NO_PRICES')) {
    wsContents += "    <div class= \"special\" id=\"special\"><table width=\"100%\" border=\"1\" align=\"center\">";
    wsContents += "    <div class=\"specialtitle\">SPECIAL PRICING<\/div>";
    wsContents += "    <tbody><tr><td colspan=\"2\"><div align=\"center\">" + specialdesc + "<\/div><\/td><\/tr>";
    wsContents += "    <tr><td width=\"191\">FINAL SELLING PRICE</td><td width=\"100\" align=\"right\"><strong>$" + CurrencyFormat2(specialprice) + "</strong><\/td></tr>";
    wsContents += "  <\/tbody><\/table><\/div><\/div>  ";
}


wsContents += "<\/div>  ";  //moved the copyright to under the totals so it doesn't overlap the standards.
wsContents += " <div id=\"footer\">*All prices found on this boat builder and website are based on standard MSRP in US Dollars. ";
wsContents += " Prices DO NOT include destination fees, prep, registration fees, taxes, dealer installed options,";
wsContents += " or any other applicable discounts or charges. Prices, materials, standard equipment and options are subject to change without notice. ";
wsContents += " Please contact your nearest dealer to determine exact pricing at the time of purchase.</br>";
wsContents += " Copyright - 2006 - 2016 Bennington All Rights Reserved.<\/div>";
wsContents += "<\/div>";
wsContents += "<\/div>  ";
wsContents += "<\/body>";
wsContents += "<\/html>";
wsContents += "";

var windowsticker = wsContents;
console.log(windowsticker);
//newWindow = window.open('windowsticker', '_blank');
//newWindow.document.write(windowsticker);

pdf = generatePDFGuest('Window Sticker ' + serial, windowsticker);
var url = pdf.url.replace(/\s/g, "%20");
window.open(url);


///FUNCTIONS//

function createStandardsList(model, modelyear) {

    var standardsmatrixlist = 'standards_matrix' + '_20' + modelyear;

    standardsList = loadByListName('standards_list');

    console.log('model year is ', model_year);
    if (model_year === '14' || model_year === '15' || model_year === '16' || model_year === '17') {
        window.twoLetters = model.substring(model.length - 2);
        //TODO: Model Change add the new year here or move to a more global array
        if (twoLetters === 'DR') { two = 14; }
        else if (twoLetters === 'DE') { two = 15; }
        else if (twoLetters === 'DF') { two = 16; }
        else if (twoLetters === 'DL') { two = 17; }
        else if (twoLetters === 'DI') { two = 18; }
        else if (twoLetters === 'DN') { two = 19; }
        else if (twoLetters === 'SG') { two = 20; }
        else if (twoLetters === 'SD') { two = 21; }

        console.log('Getting the Standards Matrix');
        window.stndsMtrx = loadByListName('standards_matrix' + '_20' + two, "WHERE (MODEL ='" + model + "')");
    }


    //console.table('stndsMtrx ', stndsMtrx);
    var speccontent = '<div class = "specreportcolumns">';
    var categories = loadList('54ee2d2b8ff578a13797c76c'); //report_category_spec_print_order local list

    sortedspeccats = sortByKey(categories, Number('PRINT_ORDER'));

    $.each(sortedspeccats, function(l, cat) {
        standardscat = sortedspeccats[l].CATEGORY_NAME;
        console.log('standardscat is ', standardscat);

        thisModelStandards = $.grep(stndsMtrx, function(Extract) {
            return ((Extract.CATEGORY == standardscat));
        });

        var printed = 0;

        $.each(thisModelStandards, function(j, stnd) {
            var loop = (thisModelStandards.length);
            category = thisModelStandards[j].CATEGORY;
            stdpartno = thisModelStandards[j].STANDARD;
            //console.log(stdpartno);
            //Get the desc from the list of standards so that desc changes can be maintained more easily.
            thisstandard = $.grep(standardsList, function (GetStandardDesc) {
                return ((GetStandardDesc.STANDARD == stdpartno));
            });
            if (thisstandard.length > 0) {
                standard = thisstandard[0].STAND_DESC;
            }
            else {
                // For CPQ boats, use OPT_NAME directly when STANDARD not found in standards_list
                standard = thisModelStandards[j].OPT_NAME || "";
            }
            catdivname = category.replace(/\s/g, "_"); //div ids can't have spaces

            if (loop > 0) {
                if (printed != 1) { //stop the category from reprinting after the first time.
                    var speccategorydivs = '<div id="' + catdivname + '"><strong></br>' + category + ' &#8226; </strong>';
                    speccontent += speccategorydivs;
                    printed = 1;
                }
            }
            if (loop > 0) {
                //standard = thisModelStandards[j].OPT_NAME;
                speccontent += standard + ' &#8226; </td></tr>';
                //console.log(speccontent);
            }
            if (loop === 1) {
                speccontent += '</tbody></table></div>';
            } else if (j === loop - 1) {
                speccontent += '</tbody></table></div>';
            }
        });
    });
    speccontent = speccontent + '</div></body></html>';
    //console.log(speccontent);
    return speccontent;
}

//function to pad the eosNo with 0s to get to 8 characters.
function pad(n, width, z) {
    z = z || '0';
    n = n + '';
    return n.length >= width ? n : new Array(width - n.length + 1).join(z) + n;
}
    //end of pad

//$('div[data-ref="LOADING/SPINNER"]').show().empty()
