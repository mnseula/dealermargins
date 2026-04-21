if ((hasAnswer('TERMS', 'TERMS') && hasAnswer('SIGNED_BY', 'SIGNED_BY') && hasAnswer('SIGNED_BY', 'DATE_SIGNED')) || getValue('PROFILE', 'TYPE') === 'BEN') {
    process();
} else {
    eosPopup('Please agree to the the terms and enter the name and date signed.');
}

function process() {
    var dlr = getValue('DLR_INFO', 'DLR_DBA');
    var primary = getValue('DLR_INFO', 'CONT_NAME');
    var add1 = getValue('DLR_INFO', 'ADD1');
    var city = getValue('DLR_INFO', 'CITY');
    var st = getValue('DLR_INFO', 'STATE');
    var zip = getValue('DLR_INFO', 'ZIP');
    var phone = getValue('DLR_INFO', 'PHONE');
    var web = getValue('DLR_INFO', 'WEB');

    var dlrno = getValue('CUSTSERV', 'FIND');
    var signer = getValue('SIGNED_BY', 'SIGNED_BY'); if (signer === true || signer === false || signer === undefined) { signer = ""; }
    var datesigned = getValue('SIGNED_BY', 'DATE_SIGNED'); if (datesigned === true || datesigned === false || datesigned === undefined) { datesigned = ""; }
    var ant_vol_disc = getValue('ADD_QUESTIONS', 'ANT_VOL_DISC'); if (ant_vol_disc === true || ant_vol_disc === false || ant_vol_disc === undefined) { ant_vol_disc = ""; }
    var comments = getValue('ADD_QUESTIONS', 'COMMENTS'); if (comments === true || comments === false || comments === undefined) { comments = ""; }
    var terms = getValue('TERMS', 'TERMS');
    var privacy = 0;
    var eu = 0;

    var signature = getValue('HIDE', 'SIG_DATA');

    $('#sigimg').remove();  //keep the images from duplicating
    var sigurl = signature;
    //console.log(sigurl);

    if (sigurl.length === 0 || sigurl === undefined || sigurl === false) {
        sigurl = 'https://s3.amazonaws.com/eosstatic/images/0/5588726d8ff578d92ccd71ad/Bennington_Pontoon_Boat_Canvas_Transparent.png';
        console.log('Keri', sigurl);
    }
    path = '<img src="' + sigurl + '" style="padding: 0px; border: 0px; box-shadow: 0px; width:70%;" class="thumbnail" crossorigin="anonymous">';


    var opencount = getValue('FORM' + year, 'OPEN');
    if (opencount === true || opencount === false) {
        opencount = "0";
    }

    var totally = getValue('FORM' + year, 'TOT_LY'); if (totally === false) { totally = ""; } if (totally === true) { totally = '0' }
    var totalfc = getValue('FORM' + year, 'TOT_FC'); if (totalfc === false) { totalfc = "0"; } if (totalfc === true) { totalfc = '0' }
    var totalty = getValue('FORM' + year, 'TOT_TY'); if (totalty === false) { totalty = ""; } if (totalty === true) { totalty = '0' }

    var augly = getValue('FORM' + year, 'AUG_LY'); if (augly === false) { augly = ""; }
    var augfc = getValue('FORM' + year, 'AUG_FC'); if (augfc === false) { augfc = "0"; } if (augfc === true) { augfc = "0"; }
    var augty = getValue('FORM' + year, 'AUG_TY'); if (augty === false) { augty = "0"; }

    var seply = getValue('FORM' + year, 'SEP_LY'); if (seply === false) { seply = ""; }
    var sepfc = getValue('FORM' + year, 'SEP_FC'); if (sepfc === false) { sepfc = "0"; } if (sepfc === true) { sepfc = "0"; }
    var septy = getValue('FORM' + year, 'SEP_TY'); if (septy === false) { septy = "0"; }

    var octly = getValue('FORM' + year, 'OCT_LY'); if (octly === false) { octly = ""; }
    var octfc = getValue('FORM' + year, 'OCT_FC'); if (octfc === false) { octfc = "0"; } if (octfc === true) { octfc = "0"; }
    var octty = getValue('FORM' + year, 'OCT_TY'); if (octty === false) { octty = "0"; }

    var novly = getValue('FORM' + year, 'NOV_LY'); if (novly === false) { novly = ""; }
    var novfc = getValue('FORM' + year, 'NOV_FC'); if (novfc === false) { novfc = "0"; } if (novfc === true) { novfc = "0"; }
    var novty = getValue('FORM' + year, 'NOV_TY'); if (novty === false) { novty = "0"; }

    var decly = getValue('FORM' + year, 'DEC_LY'); if (decly === false) { decly = ""; }
    var decfc = getValue('FORM' + year, 'DEC_FC'); if (decfc === false) { decfc = "0"; } if (decfc === true) { decfc = "0"; }
    var decty = getValue('FORM' + year, 'DEC_TY'); if (decty === false) { decty = "0"; }

    var janly = getValue('FORM' + year, 'JAN_LY'); if (janly === false) { janly = ""; }
    var janfc = getValue('FORM' + year, 'JAN_FC'); if (janfc === false) { janfc = "0"; } if (janfc === true) { janfc = "0"; }
    var janty = getValue('FORM' + year, 'JAN_TY'); if (janty === false) { janty = "0"; }

    var febly = getValue('FORM' + year, 'FEB_LY'); if (febly === false) { febly = ""; }
    var febfc = getValue('FORM' + year, 'FEB_FC'); if (febfc === false) { febfc = "0"; } if (febfc === true) { febfc = "0"; }
    var febty = getValue('FORM' + year, 'FEB_TY'); if (febty === false) { febty = "0"; }

    var marly = getValue('FORM' + year, 'MAR_LY'); if (marly === false) { marly = ""; }
    var marfc = getValue('FORM' + year, 'MAR_FC'); if (marfc === false) { marfc = "0"; } if (marfc === true) { marfc = "0"; }
    var marty = getValue('FORM' + year, 'MAR_TY'); if (marty === false) { marty = "0"; }

    var aprly = getValue('FORM' + year, 'APR_LY'); if (aprly === false) { aprly = ""; }
    var aprfc = getValue('FORM' + year, 'APR_FC'); if (aprfc === false) { aprfc = "0"; } if (aprfc === true) { aprfc = "0"; }
    var aprty = getValue('FORM' + year, 'APR_TY'); if (aprty === false) { aprty = "0"; }

    var mayly = getValue('FORM' + year, 'MAY_LY'); if (mayly === false) { mayly = ""; }
    var mayfc = getValue('FORM' + year, 'MAY_FC'); if (mayfc === false) { mayfc = "0"; } if (mayfc === true) { mayfc = "0"; }
    var mayty = getValue('FORM' + year, 'MAY_TY'); if (mayty === false) { mayty = "0"; }

    var junly = getValue('FORM' + year, 'JUN_LY'); if (junly === false) { junly = ""; }
    var junfc = getValue('FORM' + year, 'JUN_FC'); if (junfc === false) { junfc = "0"; } if (junfc === true) { junfc = "0"; }
    var junty = getValue('FORM' + year, 'JUN_TY'); if (junty === false) { junty = "0"; }

    var jully = getValue('FORM' + year, 'JUL_LY'); if (jully === false) { jully = ""; }
    var julfc = getValue('FORM' + year, 'JUL_FC'); if (julfc === false) { julfc = "0"; } if (julfc === true) { julfc = "0"; }
    var julty = getValue('FORM' + year, 'JUL_TY'); if (julty === false) { julty = "0"; }


    var dlrPlan = "";
    dlrPlan += "<!doctype html>";
    dlrPlan += "<html>";
    dlrPlan += "<head>";
    dlrPlan += "<meta charset=\"utf-8\">";
    dlrPlan += "<title>Dealer Business Plan<\/title>";
    dlrPlan += "";
    dlrPlan += "<style>";
    dlrPlan += "#forecast {";
    dlrPlan += "    font-family: \"Trebuchet MS\", Arial, Helvetica, sans-serif;";
    dlrPlan += "    width: 100%;";
    dlrPlan += "    border-collapse: collapse;";
    dlrPlan += "}";
    dlrPlan += "";
    dlrPlan += "#forecast td, #forecast th {";
    dlrPlan += "    font-size: 1em;";
    dlrPlan += "    border: 1px solid #c6c6c6;";
    dlrPlan += "    padding: 3px 7px 2px 7px;";
    dlrPlan += "}";
    dlrPlan += "";
    dlrPlan += "#forecast th {";
    dlrPlan += "    font-size: 1.1em;";
    dlrPlan += "    text-align: left;";
    dlrPlan += "    padding-top: 5px;";
    dlrPlan += "    padding-bottom: 4px;";
    dlrPlan += "    background-color: #c6c6c6;";
    dlrPlan += "    color: #ffffff;";
    dlrPlan += "}";
    dlrPlan += "";
    dlrPlan += "#forecast tr.alt td {";
    dlrPlan += "    color: #000000;";
    dlrPlan += "    background-color: #c6c6c6;";
    dlrPlan += "}";
    dlrPlan += "<\/style>";
    dlrPlan += "<\/head>";
    dlrPlan += "";
    dlrPlan += "<body>";
    dlrPlan += "";
    dlrPlan += "<table width=\"819\" height=\"884\" border=\"0\">";
    dlrPlan += "  <tbody>";
    dlrPlan += "    <tr>";
    dlrPlan += "      <td colspan=\"2\" align=\"center\"><h2><strong>Dealer Business Plan<\/strong><\/h2>";
    dlrPlan += "      <h3>Model Year " + year + "<\/h3><\/td>";
    dlrPlan += "    <\/tr>";
    dlrPlan += "    <tr>";
    dlrPlan += "      <td width=\"361\" valign=\"top\"><h4>" + dlr + " - " + dlrno + "<br>";
    dlrPlan += "        " + add1 + "<br>";
    dlrPlan += "        " + city + " " + st + ", " + zip + "<br>";
    dlrPlan += "        " + phone + "<br>";
    dlrPlan += "        " + web + "<\/h4>";
    dlrPlan += "        <h5>Primary Contact: " + primary + "<\/h5>";
    dlrPlan += "        <h5>Floorplan Source:<\/h5>";
    dlrPlan += "        <h5>Comments: " + comments + " <\/h5>";
    dlrPlan += "        <p><br>";
    dlrPlan += "      <\/p><\/td>";
    dlrPlan += "     <td width=\"448\" rowspan=\"2\" align=\"center\" valign=\"top\"><p>Current Open Orders: " + opencount + "<\/p>";
    dlrPlan += "      <table width=\"324\" height=\"516\" border=\"0\" id=\"forecast\">";
    dlrPlan += "        <tbody>";
    dlrPlan += "          <tr>";
    dlrPlan += "            <td width=\"66\" align=\"center\"><strong>Month<\/strong><\/td>";
    dlrPlan += "            <td width=\"83\" align=\"center\"><strong>Actual<br>";
    dlrPlan += "              " + year - 1 + "<\/strong><\/td>";
    dlrPlan += "            <td width=\"90\" align=\"center\"><strong>Forecast<br>";
    dlrPlan += "              " + year + "<\/strong><\/td>";
    dlrPlan += "            <td width=\"67\" align=\"center\"><strong>Actual<br>";
    dlrPlan += "              " + year + "<\/strong><\/td>";
    dlrPlan += "          <\/tr>";
    dlrPlan += "          <tr>";
    dlrPlan += "            <td><strong>Aug<\/strong><\/td>";
    dlrPlan += "            <td align=\"center\">" + augly + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + augfc + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + augty + "<\/td>";
    dlrPlan += "          <\/tr>";
    dlrPlan += "          <tr>";
    dlrPlan += "            <td height=\"28\"><strong>Sep<\/strong><\/td>";
    dlrPlan += "           <td align=\"center\">" + seply + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + sepfc + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + septy + "<\/td>";
    dlrPlan += "          <\/tr>";
    dlrPlan += "          <tr>";
    dlrPlan += "            <td height=\"29\"><strong>Oct<\/strong><\/td>";
    dlrPlan += "            <td align=\"center\">" + octly + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + octfc + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + octty + "<\/td>";
    dlrPlan += "          <\/tr>";
    dlrPlan += "          <tr>";
    dlrPlan += "            <td height=\"29\"><strong>Nov<\/strong><\/td>";
    dlrPlan += "           <td align=\"center\">" + novly + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + novfc + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + novty + "<\/td>";
    dlrPlan += "          <\/tr>";
    dlrPlan += "          <tr>";

    dlrPlan += "            <td height=\"29\"><strong>Dec<\/strong><\/td>";
    dlrPlan += "            <td align=\"center\">" + decly + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + decfc + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + decty + "<\/td>";
    dlrPlan += "          <\/tr>";
    dlrPlan += "          <tr>";
    dlrPlan += "            <td height=\"29\"><strong>Jan<\/strong><\/td>";
    dlrPlan += "            <td align=\"center\">" + janly + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + janfc + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + janty + "<\/td>";
    dlrPlan += "          <\/tr>";
    dlrPlan += "          <tr>";

    dlrPlan += "            <td height=\"29\"><strong>Feb<\/strong><\/td>";
    dlrPlan += "            <td align=\"center\">" + febly + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + febfc + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + febty + "<\/td>";
    dlrPlan += "          <\/tr>";
    dlrPlan += "          <tr>";
    dlrPlan += "            <td height=\"29\"><strong>Mar<\/strong><\/td>";
    dlrPlan += "            <td align=\"center\">" + marly + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + marfc + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + marty + "<\/td>";
    dlrPlan += "          <\/tr>";
    dlrPlan += "          <tr>";

    dlrPlan += "            <td height=\"29\"><strong>Apr<\/strong><\/td>";
    dlrPlan += "           <td align=\"center\">" + aprly + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + aprfc + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + aprty + "<\/td>";
    dlrPlan += "          <\/tr>";
    dlrPlan += "          <tr>";
    dlrPlan += "            <td height=\"29\"><strong>May<\/strong><\/td>";
    dlrPlan += "           <td align=\"center\">" + mayly + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + mayfc + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + mayty + "<\/td>";
    dlrPlan += "          <\/tr>";
    dlrPlan += "          <tr>";
    dlrPlan += "            <td height=\"29\"><strong>Jun<\/strong><\/td>";
    dlrPlan += "            <td align=\"center\">" + junly + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + junfc + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + junty + "<\/td>";
    dlrPlan += "          <\/tr>";
    dlrPlan += "          <tr>";
    dlrPlan += "            <td height=\"29\"><strong>Jul<\/strong><\/td>";
    dlrPlan += "            <td align=\"center\">" + jully + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + julfc + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + julty + "<\/td>";
    dlrPlan += "          <\/tr>";
    dlrPlan += "            <td><strong>Totals<\/strong><\/td>";
    dlrPlan += "            <td align=\"center\">" + totally + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + totalfc + "<\/td>";
    dlrPlan += "            <td align=\"center\">" + totalty + "<\/td>";
    dlrPlan += "          <\/tr>";

    dlrPlan += "        <\/tbody>";
    dlrPlan += "    <\/table>";
    dlrPlan += "      <br>";
    dlrPlan += "      <table width=\"448\" border=\"0\">";
    dlrPlan += "        <tbody>";
    dlrPlan += "          <tr>";
    dlrPlan += "            <td align=\"center\"><h4><strong>Total <br>";
    dlrPlan += "              Units<br>Forecasted<\/strong><\/h4><\/td>";
    //dlrPlan += "            <td align=\"center\"><h4>Suggested<br>Volume<br>";
    //dlrPlan += "              Discount<\/h4><\/td>";
    dlrPlan += "            <td align=\"center\"><h4>Actual<br>";
    dlrPlan += "              Volume<br>";
    dlrPlan += "              Discount<\/h4><\/td>";
    dlrPlan += "            <\/tr>";
    dlrPlan += "          <tr>";
    dlrPlan += "            <td align=\"center\" valign=\"top\"><h4>" + totalfc + "<\/h4><\/td>";
    //dlrPlan += "            <td align=\"center\" valign=\"top\"><h4>6%<\/h4><\/td>";
    dlrPlan += "            <td align=\"center\" valign=\"top\"><h4>" + ant_vol_disc + "%<\/h4><\/td>";
    dlrPlan += "            <\/tr>";
    dlrPlan += "        <\/tbody>";
    dlrPlan += "  <\/table><\/td>";
    dlrPlan += "    <\/tr>";
    dlrPlan += "    <tr>";
    dlrPlan += "      <td height=\"528\" valign=\"bottom\"><h4>Signed By: " + signer + "<br>";
    dlrPlan += "        Date Signed: " + datesigned + "<\/h4>";

    if (terms == true) {
        dlrPlan += " <p><input name=\"checkbox\" type=\"checkbox\" id=\"checkbox\" checked>Dealer has read and understands that all Bennington boat orders are subject to its <a href=https://s3.amazonaws.com/eosstatic/files/5d4d6bd40952574a06c55a20/Bennington%20Ad%20Policy_revFINAL%207.8.19.pdf>Advertising Policy</a>.</p>";
    } else {
        dlrPlan += " <p><input name=\"checkbox\" type=\"checkbox\" id=\"checkbox\" > Dealer has read and understands that all Bennington boat orders are subject to its <a href=https://s3.amazonaws.com/eosstatic/files/5d4d6bd40952574a06c55a20/Bennington%20Ad%20Policy_revFINAL%207.8.19.pdf>Advertising Policy</a>.</p>";
    }

    //dlrPlan += "      <p>"+ path +"<\/p><\/td>";
    dlrPlan += "    <\/tr><tr><td> <br></td></tr>";
    dlrPlan += "    <tr>";
    dlrPlan += "      <td><p></p><p><strong>Owner/Principal Signature:</strong>";
    dlrPlan += "      <\/br>" + path + "<\/p><\/td>";
    dlrPlan += "    <\/tr>";
    dlrPlan += "  <\/tbody>";
    dlrPlan += "<\/table>";
    dlrPlan += "";
    dlrPlan += "<\/body>";
    dlrPlan += "<\/html>";

    //debugger
    pdf = generatePDFGuest('DealerPlan' + randomString(10), dlrPlan);
    console.log(pdf)
    var url = pdf.url.replace(/\s/g, "%20");
    window.open(url);
    reset('BTN', 'PRINT');

    function generatePDF(name, html) {
        if (!html) {
            console.error('You must supply both a name and HTML as parameters');
            return false;
        }
        return sAjax('POST', { name: name, html: html }, 'json', '/docgen/generate_pdf/');
    }

    function generatePDFGuest(name, html) {
        if (!html) {
            console.error('You must supply both a name and HTML as parameters');
            return false;
        }
        return sAjax('POST', { name: name, html: html }, 'json', '/cart_pdf/generate/');
    }
}
