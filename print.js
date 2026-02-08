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

// CPQ FALLBACK - Use window.realmodel for CPQ boats
// window.isCPQBoat is set in packagePricing.js (true when year code detection fails)
// This is more reliable than checking if model equals 'Base Boat'
if (window.isCPQBoat) {
    console.log('CPQ boat detected (isCPQBoat = true) - using window.realmodel instead of BOAT_INFO');
    console.log('BOAT_INFO/BOAT_REAL_MODEL was:', model);
    model = window.realmodel;
    console.log('Using model from window.realmodel:', model);
}

shortmodel = model.substring(0, model.length - 2); //strip the model year designator
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

    //window.twoLetters = model.substring(model.length - 2);
    //if (twoLetters === 'DR') { two = '14'; }
    //else if (twoLetters === 'DE') { two = '15'; }
    //else if (twoLetters === 'DF') { two = '16'; }
    //else if (twoLetters === 'DL') { two = '17'; }
    //else if (twoLetters === 'DI') { two = '18'; }
    //else if (twoLetters === 'DN') { two = '19'; }
    //else if (twoLetters === 'SG') { two = '20'; }

    console.log(model, two);
    modelImg = getModelImage('20' + two, model);

    // Create Image
    if (modelImg == undefined) { //set image to a white filler if it is missing.
        var imgUrl = 'https://s3.amazonaws.com/eosstatic/images/0/552287f6f0f18aaf52d19f6d/window_sticker_missing_model_white_filler.png';
        //sendEmail('krimbaugh@benningtonmarine.com','A Window Sticker for Boat Model ' + model + ' is missing the image from the model_images table.','Model Image Missing');
    } else {
        var imgUrl = modelImg.replace(/\s/g, "%20");
    }
}

var img = '<img src="' + imgUrl + '" height="90px">';
console.log('perfpkgid', perfpkgid);

// Initialize prfPkgs to prevent undefined error
var prfPkgs = [];

// Get Performance Packages
if (perfpkgid.length !== 0 && perfpkgid.length < 3) {
    console.log('got here');
    prfPkgs = loadByListName('perf_pkg_spec', "WHERE (MODEL ='" + model + "') /*AND (STATUS ='Active') */AND (PKG_ID ='" + perfpkgid + "')");
}

console.log(prfPkgs);
//Lookup the description of the Engine Config and the Fuel Type from Local Lists to print words instead of a number.
if (boatSpecs.length > 0) {
    var engConfigDesc = loadList('54f4b35d8ff57802739e8f84', 'LIST/engineConfigID["' + boatSpecs[0].ENG_CONFIG_ID + '"]')[0].engineConfigName;
    var fuelTypeDesc = loadList('54f4cdb98ff578e6799e8f84', 'LIST/FUEL_TYPE_ID["' + boatSpecs[0].FUEL_TYPE_ID + '"]')[0].FUEL_TYPE_NAME;
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
wsContents += "    font-size: 10px;}";
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

if (perfpkgid.length !== 0 && perfpkgid.length < 3 && perfpkgid !== undefined) {
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
wsContents += "    <div id=\"standards\">" + stds + "<\/div> ";
wsContents += "  <\/div>";
wsContents += "  <div class=\"column\" id=\"column2\">";
if(boatPricing =='SV'){
    wsContents += "    <div id=\"pagetitle\">20"+model_year +" " + shortmodel + "<\/div>";
}else{
    wsContents += "    <div id=\"pagetitle\">20"+model_year +" " + shortmodel + " " + type  +"<\/div>";
}
wsContents += "    <div id=\"overheadimg\"> " + img + "<\/div>";
wsContents += "    <div class=\"title\">INCLUDED OPTIONS <\/div>";
wsContents += "    <div id=\"includedoptions\">" + document.getElementById('included').outerHTML + "<\/div>";

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
                standard = "";
            }
            // standard = thisModelStandards[j].OPT_NAME;
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
