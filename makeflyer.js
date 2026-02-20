console.log('Generating Poster');

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

window.flyerDiscount = (getValue('PRICING', 'FLYER_DISCOUNT'));
window.flyerFinal = (getValue('PRICING', 'FLYER_FINAL_PRICE'));
window.flyerTitle = (getValue('PRICING', 'FLYER_TITLE'));
if (flyerTitle === true) {
    flyerTitle = "";
}
window.flyerMSRP = (getValue('PRICING', 'FLYER_MSRP'));

console.log('CPQ FLYER DEBUG makeflyer - flyerDiscount:', flyerDiscount, 'type:', typeof flyerDiscount);
console.log('CPQ FLYER DEBUG makeflyer - flyerFinal:', flyerFinal);
console.log('CPQ FLYER DEBUG makeflyer - flyerMSRP:', flyerMSRP);

if (flyerDiscount === false || flyerDiscount === true) {
    flyerDiscount = '';
}
if (flyerFinal === false || flyerFinal === true) {
    flyerFinal = '';
}
if (flyerTitle === false || flyerTitle === true) {
    flyerTitle = '';
}

var optionalPricing = getValue('PRICING', 'ADDITIONAL_INFO');
if(optionalPricing === false) {
    optionalPricing = '';
}
console.log("ADDITIONAL PRICE INFO:"+ optionalPricing);

var dlr = getValue('DLR', 'DLR_NO');
var dlrlogourlrec = loadByListName('DLR_LOGOS', 'LIST/Dlr_No[="' + dlr + '"]');
console.log(dlrlogourlrec);

if (dlrlogourlrec.length > 0) {
    var dlrlogourl = dlrlogourlrec[0].Logo_URL;
}
//console.log('dealer logo url is ', dlrlogourl);


var i = 1; //order
//var content = '<head><style>#features{font-family:Calibri;font-size:14;font-weight:bold;}</style></head>';
//var content ="<ul id = \"descList\">";
//content += '<div id="features"><h2 align="center">FEATURES</h2>';
    var contentSize = 0; //to track the size of the list in order to move to new row.
    var itemsPerPagePortrait = 55; // Approximate items per page for portrait
    var currentPagePortrait = 1;
    var accentCol = "DEFAULT COLOR";
    
    // Create lookup map from originalBoatTable to get full descriptions
    var fullDescMap = {};
    var sourceTable = (typeof window.originalBoatTable !== 'undefined' && window.originalBoatTable) 
        ? window.originalBoatTable 
        : ((typeof boattable !== 'undefined' && boattable) ? boattable : []);
    
    console.log('DEBUG makeflyer - sourceTable type:', typeof sourceTable, 'length:', sourceTable ? sourceTable.length : 0);
    console.log('DEBUG makeflyer - using originalBoatTable:', !!(typeof window.originalBoatTable !== 'undefined' && window.originalBoatTable));
    
    $.each(sourceTable, function(i) {
        var btItemNo = sourceTable[i].ItemNo;
        var btItemDesc = sourceTable[i].ItemDesc1;
        if (btItemNo && btItemDesc) {
            fullDescMap[btItemNo] = btItemDesc;
        }
    });
    
    console.log('DEBUG makeflyer - fullDescMap keys:', Object.keys(fullDescMap).slice(0, 10));

    // First loop to get accent color
    $('#sortable li').each(function(index) {
        var desc = $(this).find('input[type="text"]').val() || '';
        var accentHelp = "PANEL -";
        if (desc && desc.includes(accentHelp)) {
            accentCol = desc.slice(8);
        }
    });

    // Build content list
    var content = "<ul id = \"descList\">";
    
    $('#sortable li').each(function(index) {
        var part = $(this).attr('data-itemno') || '';
        // Find the input directly within this li element to avoid selector issues with special characters
        var desc = $(this).find('input[type="text"]').val() || '';
        var state = $(this).attr('class') || '';

        // Use full description from boattable if available
        if (part && fullDescMap[part] && fullDescMap[part].length > desc.length) {
            desc = fullDescMap[part];
        }

        if (desc && state.indexOf('ui-state-focus') !== -1) {
            hide = 0;
            
            // Check if we need a page break (every itemsPerPagePortrait items)
            if (contentSize > 0 && contentSize % itemsPerPagePortrait === 0) {
                content += '</ul>';
                content += '<div class="page-break" style="page-break-before: always; margin-top: 20px;">';
                content += '<div style="font-size: 20px; font-weight: bold; margin-bottom: 10px; font-family: Helvetica Neue, Helvetica, Arial, sans-serif;">KEY FEATURES AND OPTIONS</div>';
                content += '<ul>';
                currentPagePortrait++;
            }
            
            content += '<li>' + escapeHtml(desc) + '</li>';
            contentSize++;
        } else {
            hide = 1;
        }

        i++;
    });

console.log("Zach");
//console.log("List Size: " + contentSize);
console.log(accentCol);
//content += '</ul>';
//console.log(content);

var underImage = getAnswer('POSTER_IMG');
var underVal = 0;
console.log('awijuhfaoiuwhjtriajiowt    '+ underImage);

switch(underImage) {
    case "POSTER_IMG/GENERIC_1" :
        underVal = -100;
        break;
    case "POSTER_IMG/GENERIC_2" :
        underVal = -150;
        break;
    case "POSTER_IMG/GENERIC_3" :
        underVal = -200;
        break;
    case "POSTER_IMG/GENERIC_4" :
        underVal = -200;
        break;
    case "POSTER_IMG/GENERIC_5" :
        underVal = 0;
        break;
    case "POSTER_IMG/GENERIC_6" :
        underVal = -100;
        break;
    case "POSTER_IMG/GENERIC_7" :
        underVal = -200;
        break;
    case "POSTER_IMG/GENERIC_8" :
        underVal = 0;
        break;
    case "POSTER_IMG/GENERIC_9" :
        underVal = -50;
        break;
    case "POSTER_IMG/GENERIC_10" :
        underVal = -200;
        break;
    case "POSTER_IMG/GENERIC_11" :
        underVal = -150;
        break;
    case "POSTER_IMG/GENERIC_12" :
        underVal = -100;
        break;
    case "POSTER_IMG/GENERIC_13" :
        underVal = -170;
        break;
    case "POSTER_IMG/GENERIC_14" :
        underVal = -200;
        break;
    case "POSTER_IMG/GENERIC_15" :
        underVal = -100;
        break;
    case "POSTER_IMG/GENERIC_16" :
        underVal = -250;
        break;
    case "POSTER_IMG/GENERIC_17" :
        underVal = -150;
        break;
    case "POSTER_IMG/GENERIC_18" :
        underVal = -200;
        break;
}

var ribbonColor = "https://s3.amazonaws.com/eosstatic/images/0/624209d9d4ecb36ab2286312/Ribbon.png"; //Default Ribbon Color
var ribbonFont = "white"; //Default Font Color

switch (accentCol) {
    case "SUNSET RED":
        ribbonColor = "https://s3.amazonaws.com/eosstatic/images/0/62508677d4ecb3510595968f/Ribbon_sunset.png";
        break;
    case "SMOKEY GRANITE":
        ribbonColor = "https://s3.amazonaws.com/eosstatic/images/0/625088a8d4ecb3534844e022/Ribbon_smokeygranite.png";
        break;
    //case "METALLIC WHITE":
        //ribbonColor = "https://s3.amazonaws.com/eosstatic/images/0/6287ca38095257696d6a0007/Ribbon_white.png";
        //ribbonFont = "black";
        //break;
    case "METALLIC SORREL":
        ribbonColor = "https://s3.amazonaws.com/eosstatic/images/0/62508a89d4ecb35149c04205/Ribbon_sorrel.png";
        break;
    case "ROSSA RED":
        ribbonColor = "https://s3.amazonaws.com/eosstatic/images/0/62508a87d4ecb3514931627d/Ribbon_rossa.png";
        break;
    case "MEDITERRANEAN BLUE":
        ribbonColor = "https://s3.amazonaws.com/eosstatic/images/0/62508a81d4ecb3559958a29f/Ribbon_mediterranean.png";
        break;
    case "MIDNIGHT BLACK":
        ribbonColor = "https://s3.amazonaws.com/eosstatic/images/0/62508a7fd4ecb35567c05303/Ribbon_black.png";
        break;
    case "METALLIC SILVER":
        ribbonColor = "https://s3.amazonaws.com/eosstatic/images/0/62508a87d4ecb35599db531a/Ribbon_silver.png";
        break;
    case "METALLIC PLATINUM":
        ribbonColor = "https://s3.amazonaws.com/eosstatic/images/0/62508a85d4ecb35601971277/Ribbon_platinum.png";
        break;
    case "FIRECRACKER":
        ribbonColor = "https://s3.amazonaws.com/eosstatic/images/0/62508a7fd4ecb3547dc65554/Ribbon_firecracker.png";
        break;
    case "OCEAN BLUE":
        ribbonColor = "https://s3.amazonaws.com/eosstatic/images/0/62508a84d4ecb3547d75f18c/Ribbon_ocean.png";
        break;
}

var optionalMessage = "";
if (isAnswered('DEALER_MSG', 'MESSAGE') === true) {
    optionalMessage = getValue('DEALER_MSG', 'MESSAGE');
}

if (hasAnswer('LAYOUT', 'PORTRAIT')) {
    var content = "<ul id = \"descList\">";

    // Create lookup map from originalBoatTable to get full descriptions
    var fullDescMap = {};
    var sourceTable = (typeof window.originalBoatTable !== 'undefined' && window.originalBoatTable) 
        ? window.originalBoatTable 
        : ((typeof boattable !== 'undefined' && boattable) ? boattable : []);
    
    console.log('DEBUG makeflyer - sourceTable type:', typeof sourceTable, 'length:', sourceTable ? sourceTable.length : 0);
    console.log('DEBUG makeflyer - using originalBoatTable:', !!(typeof window.originalBoatTable !== 'undefined' && window.originalBoatTable));
    
    $.each(sourceTable, function(i) {
        var btItemNo = sourceTable[i].ItemNo;
        var btItemDesc = sourceTable[i].ItemDesc1;
        if (btItemNo && btItemDesc) {
            fullDescMap[btItemNo] = btItemDesc;
        }
    });
    
    console.log('DEBUG makeflyer - fullDescMap keys:', Object.keys(fullDescMap).slice(0, 10));

    $('#sortable li').each(function(index) {
        var part = $(this).attr('data-itemno') || '';
        // Find the input directly within this li element to avoid selector issues with special characters
        var desc = $(this).find('input[type="text"]').val() || '';
        var state = $(this).attr('class') || '';

        // Use full description from boattable if available
        if (part && fullDescMap[part] && fullDescMap[part].length > desc.length) {
            desc = fullDescMap[part];
        }

        if (desc && state.indexOf('ui-state-focus') !== -1) {
            hide = 0;
            content += '<li>' + escapeHtml(desc) + '</li>';
            contentSize++;
        } else {
            hide = 1;
        }

        i++;
    });

    content += '</ul>';


    var flyerbody = "";
    flyerbody += "<!doctype html>";
    flyerbody += "<html>";
    flyerbody += "<head>";
    flyerbody += "<meta charset=\"utf-8\">";
    flyerbody += "<title>Bennington Show Poster<\/title>";
    flyerbody += "<\/head>";
    flyerbody += "<style>";
    flyerbody += "    #top {";
    flyerbody += "        position: absolute;";
    flyerbody += "        width: 1063px;";
    flyerbody += "        z-index: 1;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #ribbon {";
    flyerbody += "        position: absolute;";
    flyerbody += "        width: 310px;";
    flyerbody += "        height: 390px;";
    flyerbody += "        top: 180px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        z-index: 10;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #image {";
    flyerbody += "        position: absolute;";
    flyerbody += "        width: 680px;";
    flyerbody += "        height: 330px;";
    flyerbody += "        top: 180px;";
    flyerbody += "        left: 360px;";
    flyerbody += "        z-index: 1;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #perf {";
    flyerbody += "        position: absolute;";
    flyerbody += "        height: 120px;";
    flyerbody += "        top: 1100px;";
    flyerbody += "        left: 90px;";
    flyerbody += "        z-index: 1;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #msrp {";
    flyerbody += "        position: absolute;";
    flyerbody += "        width: 310px;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 20px;";
    flyerbody += "        top: 215px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "        color: " + ribbonFont + ";";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #msrpPrice {";
    flyerbody += "        position: absolute;";
    flyerbody += "        width: 310px;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 235px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-size: 35px;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "        color: " + ribbonFont + ";";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #savings {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 300px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-size: 20px;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "        color: " + ribbonFont + ";";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #savingsPrice {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 320px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        font-size: 40px;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "        color: " + ribbonFont + ";";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #saleprice {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 390px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-size: 25px;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "        color: " + ribbonFont + ";";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #saleMoney {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 420px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-size: 60px;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "        color: " + ribbonFont + ";";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #optionalPricing {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 490px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-size: 18px;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "        color: " + ribbonFont + ";";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #title1 {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 580px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        left: 40px;";
    flyerbody += "        font-size: 20px;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #title2 {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 600px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-size: 30px;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #power {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 670px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-size: 15px;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #powerContent {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 685px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-size: 22px;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #length {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 730px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-size: 15px;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #lengthContent {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 745px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-size: 23px;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #beam {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 790px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-size: 15px;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #beamContent {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 805px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-size: 23px;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #dia {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 850px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-size: 15px;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #diaContent {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 865px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-size: 23px;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #capacity {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 910px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-size: 15px;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #capacityContent {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 925px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-size: 22px;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #hull {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 970px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-size: 15px;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #hullContent {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 985px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-size: 22px;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #fuel {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 1030px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-size: 15px;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #fuelContent {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 1045px;";
    flyerbody += "        left: 40px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-size: 22px;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    if(typeof imgSrc === 'undefined') { //if image is empty
        flyerbody += "    #key {";
        flyerbody += "        position: absolute;";
        flyerbody += "        z-index: 10;";
        flyerbody += "        top: 180px;";
        flyerbody += "        left: 390px;";
        flyerbody += "        width: 680px;";
        flyerbody += "        font-size: 24px;";
        flyerbody += "        font-weight: bold;";
        flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
        flyerbody += "    }";
        flyerbody += "    ";
        flyerbody += "    #content {";
        flyerbody += "        position: absolute;";
        flyerbody += "        z-index: 10;";
        flyerbody += "        top: 230px;";
        flyerbody += "        left: 390px;";
        flyerbody += "        width: 680px;";
        flyerbody += "        font-size:" + fontsize + ";";
        flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
        flyerbody += "        word-wrap: break-word;";
        flyerbody += "        overflow-wrap: break-word;";
        flyerbody += "    }";
        flyerbody += "    ";
    } else {
        flyerbody += "    #key {";
        flyerbody += "        position: absolute;";
        flyerbody += "        z-index: 10;";
        flyerbody += "        top: 530px;";
        flyerbody += "        left: 390px;";
        flyerbody += "        width: 680px;";
        flyerbody += "        font-size: 18px;";
        flyerbody += "        font-weight: bold;";
        flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
        flyerbody += "    }";
        flyerbody += "    ";
        flyerbody += "    #content {";
        flyerbody += "        position: absolute;";
        flyerbody += "        z-index: 10;";
        flyerbody += "        top: 580px;";
        flyerbody += "        left: 390px;";
        flyerbody += "        width: 680px;";
        flyerbody += "        font-size:" + fontsize + ";";
        flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
        flyerbody += "        word-wrap: break-word;";
        flyerbody += "        overflow-wrap: break-word;";
        flyerbody += "    }";
        flyerbody += "    ";
    }
    flyerbody += "    #dealer {";
    flyerbody += "        position: absolute;";
    flyerbody += "        height: 100px;";
    flyerbody += "        width: 200px;";
    flyerbody += "        top: 1230px;";
    flyerbody += "        left: 835px;";
    flyerbody += "        z-index: 10;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #optionalMessage {";
    flyerbody += "        position: absolute;";
    flyerbody += "        height: 120px;";
    flyerbody += "        width: 620px;";
    flyerbody += "        top: 1250px;";
    flyerbody += "        left: 90px;";
    flyerbody += "        font-size:" + fontsize + ";";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "        word-break: break-word; ";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "<\/style>";
    flyerbody += "";
    flyerbody += "<body>";
    flyerbody += "    <img id = \"top\" src = \"https://s3.amazonaws.com/eosstatic/images/0/62431aa5d4ecb32b35ab0aa8/vert_cut.png\" alt = \"top not loaded properly\">";
    flyerbody += "    <img id = \"ribbon\" src =  " + ribbonColor + "  alt = \"ribbon failed to load\">";
    if(typeof imgSrc !== 'undefined') {
       flyerbody += "    <img id = \"image\" src = " + imgSrc + " alt = \"image failed to load\">";
    }
    if (typeof logoSrc !== 'undefined') {
        flyerbody += "<img id = \"perf\" src = " + logoSrc + " alt = \"perf logo failed to load\">";
    }
    flyerbody += "    <div id = \"border\"><\/div>";
    flyerbody += "    <div id = \"msrp\">MSRP<\/div>";
    flyerbody += "    <div id = \"msrpPrice\">$" + flyerMSRP + "<\/div>";
    flyerbody += "    <div id = \"savings\">SAVINGS<\/div>";
    // CPQ Fix: Don't show negative sign for $0 discount
    console.log('CPQ FLYER DEBUG - flyerDiscount before prefix:', flyerDiscount, 'Number:', Number(flyerDiscount), 'is > 0:', Number(flyerDiscount) > 0);
    var savingsPrefix = (flyerDiscount && Number(flyerDiscount) > 0) ? '$-' : '$';
    console.log('CPQ FLYER DEBUG - savingsPrefix:', savingsPrefix);
    flyerbody += "    <div id = \"savingsPrice\">" + savingsPrefix + flyerDiscount + "<\/div>";
    flyerbody += "    <div id = \"saleprice\">SALE PRICE<\/div>";
    flyerbody += "    <div id = \"saleMoney\">$" + flyerFinal + "<\/div>";
    flyerbody += "    <div id = \"optionalPricing\">" + escapeHtml(optionalPricing) + "<\/div>";
    flyerbody += "    <div id = \"title1\">20" + model_year + " BENNINGTON<\/div>";
    flyerbody += "    <div id = \"title2\">" + escapeHtml(document.getElementById('model') ? document.getElementById('model').value : '') + "<\/div>";
    flyerbody += "    <div id = \"power\">POWER<\/div>";
    flyerbody += "    <div id = \"powerContent\">" + escapeHtml(document.getElementById('engine') ? document.getElementById('engine').value : '') + "<\/div>";
    flyerbody += "    <div id = \"length\">LENGTH<\/div>";
    flyerbody += "    <div id = \"lengthContent\">" + escapeHtml(document.getElementById('loa') ? document.getElementById('loa').value : '') + "<\/div>";
    flyerbody += "    <div id = \"beam\">BEAM<\/div>";
    flyerbody += "    <div id = \"beamContent\">" + escapeHtml(document.getElementById('beam') ? document.getElementById('beam').value : '') + "<\/div>";
    flyerbody += "    <div id = \"dia\">PONTOON DIA<\/div>";
    flyerbody += "    <div id = \"diaContent\">" + escapeHtml(document.getElementById('diameter') ? document.getElementById('diameter').value : '') + "<\/div>";
    flyerbody += "    <div id = \"capacity\">CAPACITY<\/div>";
    flyerbody += "    <div id = \"capacityContent\">" + escapeHtml(document.getElementById('cap') ? document.getElementById('cap').value : '') + "<\/div>";
    flyerbody += "    <div id = \"hull\">HULL WEIGHT<\/div>";
    flyerbody += "    <div id = \"hullContent\">" + escapeHtml(document.getElementById('weight') ? document.getElementById('weight').value : '') + "<\/div>";
    flyerbody += "    <div id = \"fuel\">FUEL CAPACITY<\/div>";
    flyerbody += "    <div id = \"fuelContent\">" + escapeHtml(document.getElementById('fuel') ? document.getElementById('fuel').value : '') + "<\/div>";
    flyerbody += "    <div id = \"key\">KEY FEATURES AND OPTIONS<\/div>";
    flyerbody += "    <div id = \"content\">" + content + "<\/div>";
    if (dlrlogourl !== undefined) {
        flyerbody += "<img src=" + dlrlogourl + " alt=\"\" id=\"dealer\"\/>";
    }
    flyerbody += "    <div id = \"optionalMessage\">" + escapeHtml(optionalMessage) + "<\/div>";
    flyerbody += "    ";
    flyerbody += "<\/body>";
    flyerbody += "<\/html>";
    flyerbody += "";



    console.log(flyerbody);
}
if (hasAnswer('LAYOUT', 'LANDSCAPE')) {

    var content = "<ul id = \"descList\">";
    var extra = false;
    colNum = 2;
    var itemsPerPage = 45; // Approximate items per page
    var currentPage = 1;

    // Create lookup map from originalBoatTable to get full descriptions
    var fullDescMapLandscape = {};
    var sourceTableLandscape = (typeof window.originalBoatTable !== 'undefined' && window.originalBoatTable) 
        ? window.originalBoatTable 
        : ((typeof boattable !== 'undefined' && boattable) ? boattable : []);
    
    $.each(sourceTableLandscape, function(i) {
        var btItemNo = sourceTableLandscape[i].ItemNo;
        var btItemDesc = sourceTableLandscape[i].ItemDesc1;
        if (btItemNo && btItemDesc) {
            fullDescMapLandscape[btItemNo] = btItemDesc;
        }
    });

    $('#sortable li').each(function(index) {
        var part = $(this).attr('data-itemno') || '';
        // Find the input directly within this li element to avoid selector issues with special characters
        var desc = $(this).find('input[type="text"]').val() || '';
        var state = $(this).attr('class') || '';

        // Use full description from boattable if available
        if (part && fullDescMapLandscape[part] && fullDescMapLandscape[part].length > desc.length) {
            desc = fullDescMapLandscape[part];
        }

        if (desc && state.indexOf('ui-state-focus') !== -1) {
            hide = 0;
            
            // Check if we need a page break (every itemsPerPage items)
            if (contentSize > 0 && contentSize % itemsPerPage === 0) {
                content += '</ul>';
                content += '<div class="page-break" style="page-break-before: always; margin-top: 20px;">';
                content += '<div style="font-size: 20px; font-weight: bold; margin-bottom: 10px; font-family: Helvetica Neue, Helvetica, Arial, sans-serif;">KEY FEATURES AND OPTIONS</div>';
                content += '<ul>';
                currentPage++;
            }
            
            content += '<li>' + escapeHtml(desc) + '</li>';
            contentSize++;
            if (contentSize > 21) {
                content += "</ul><div id = \"column" + colNum + "\"><ul>";
                contentSize = 0;
                extra = true;
                colNum++;
            }
        } else {
            hide = 1;
        }

        i++;
    });

    content += '</ul>';
    if (extra === true) {
        content += '</div>';
    }


    var flyerbody = "";
    flyerbody += "<!doctype html>";
    flyerbody += "<html>";
    flyerbody += "<head>";
    flyerbody += "<meta charset=\"utf-8\">";
    flyerbody += "<title>Bennington Show Poster<\/title>";
    flyerbody += "<\/head>";
    flyerbody += "<style>";
    flyerbody += "#descList {";
    flyerbody += "}";
    flyerbody += "    #border {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 1;";
    flyerbody += "        width: 1375px;";
    flyerbody += "        height: 1063px;";
    flyerbody += "        border-style: solid;    ";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #ribbon {";
    flyerbody += "        position: absolute;";
    flyerbody += "        width: 310px;";
    flyerbody += "        height: 440px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        top: 25px;";
    flyerbody += "        z-index: 2;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #top {";
    flyerbody += "        position: absolute;";
    flyerbody += "        width: 1063px;";
    flyerbody += "        height: 160px;";
    flyerbody += "        width: 1070px;";
    flyerbody += "        z-index: 1;";
    flyerbody += "        left: 320px;";
    flyerbody += "        top: 0px;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #msrp {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 20px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        top: 65px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "        color:" + ribbonFont + ";";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #msrpContent {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 35px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 85px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "        color: " + ribbonFont + ";";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #savings {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 20px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 175px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "        color: " + ribbonFont + ";";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #savingsContent {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 40px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 195px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "        color: " + ribbonFont + ";";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #saleprice {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 30px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 290px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "        color: " + ribbonFont + ";";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #salepriceContent {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 60px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 320px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "        color: " + ribbonFont + ";";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #optionalPricing {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 18px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 390px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "        color: " + ribbonFont + ";";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #title1 {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 16px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 465px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #title2 {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 35px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 480px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #power {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 16px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 550px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #powerContent {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 23px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 565px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #length {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 16px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 610px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #lengthContent {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 23px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 625px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #beam {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 16px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 670px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #beamContent {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 23px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 685px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #dia {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 16px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 730px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #diaContent {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 23px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 745px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #capacity {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 16px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 790px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #capacityContent {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 23px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 805px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #hull {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 16px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 850px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #hullContent {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 23px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 865px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #fuel {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 16px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 910px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #fuelContent {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 23px;";
    flyerbody += "        width: 310px;";
    flyerbody += "        top: 925px;";
    flyerbody += "        left: 30px;";
    flyerbody += "        font-weight: bold;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #perf {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        top: 975px;";
    flyerbody += "        left: 110px;";
    flyerbody += "        height: 80px;";
    flyerbody += "        text-align: center;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #descList {";
    flyerbody += "        margin: auto;";
    flyerbody += "    }";
    flyerbody += "    ";
    if(typeof imgSrc === 'undefined') {
        flyerbody += "    #keyFeat {";
        flyerbody += "        position: absolute;";
        flyerbody += "        z-index: 10;";
        flyerbody += "        font-size: 24px;";
        flyerbody += "        width: 1010px;";
        flyerbody += "        top: 155px;";
        flyerbody += "        left: 365px;";
        flyerbody += "        font-weight: bold;";
        flyerbody += "        text-align: left;";
        flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
        flyerbody += "    }";
        flyerbody += "    ";
        flyerbody += "    #content {";
        flyerbody += "        position: absolute;";
        flyerbody += "        width: 505px;";
        flyerbody += "        height: 430px;";
        flyerbody += "        top: 195px;";
        flyerbody += "        left: 350px;";
        flyerbody += "        font-size:" + fontsize + ";";
        flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
        flyerbody += "        word-wrap: break-word;";
        flyerbody += "        overflow-wrap: break-word;";
        flyerbody += "    }";
        flyerbody += "    ";
    } else {
        flyerbody += "    #image {";
        flyerbody += "        position: absolute;";
        flyerbody += "        width: 1010px;";
        flyerbody += "        height: 300px;";
        flyerbody += "        top: 155px;";
        flyerbody += "        left: 350px;";
        flyerbody += "        z-index: 1;";
        flyerbody += "        overflow:hidden;";
        flyerbody += "        text-align: center;";
        flyerbody += "    }";
        flyerbody += "    ";
        flyerbody += "    #imageSrc {";
        flyerbody += "        position: absolute;";
        flyerbody += "        height: 550px;";
        flyerbody += "        bottom: "+underVal+";"; // Might need to change this based on picture for best results!
        flyerbody += "    }";
        flyerbody += "    ";
        flyerbody += "    #keyFeat {";
        flyerbody += "        position: absolute;";
        flyerbody += "        z-index: 10;";
        flyerbody += "        font-size: 18px;";
        flyerbody += "        width: 1010px;";
        flyerbody += "        top: 465px;";
        flyerbody += "        left: 365px;";
        flyerbody += "        font-weight: bold;";
        flyerbody += "        text-align: left;";
        flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
        flyerbody += "    }";
        flyerbody += "    ";
        flyerbody += "    #content {";
        flyerbody += "        position: absolute;";
        flyerbody += "        width: 505px;";
        flyerbody += "        height: 430px;";
        flyerbody += "        top: 505px;";
        flyerbody += "        left: 350px;";
        flyerbody += "        font-size:" + fontsize + ";";
        flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
        flyerbody += "        word-wrap: break-word;";
        flyerbody += "        overflow-wrap: break-word;";
        flyerbody += "    }";
        flyerbody += "    ";
    }
    flyerbody += "    #dealer {";
    flyerbody += "        position: absolute;";
    flyerbody += "        z-index: 10;";
    flyerbody += "        font-size: 15px;";
    flyerbody += "        height: 100px;";
    flyerbody += "        width: 200px;";
    flyerbody += "        top: 950px;";
    flyerbody += "        left: 1150px;";
    flyerbody += "        text-align: left;";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    flyerbody += "    #optionalMessage {";
    flyerbody += "        position: absolute;";
    flyerbody += "        word-break: break-word; ";
    flyerbody += "        width: 505px;";
    flyerbody += "        height: 100px;";
    flyerbody += "        top: 970px;";
    flyerbody += "        left: 350px;";
    flyerbody += "        text-align: left;";
    flyerbody += "        font-size:" + fontsize + ";";
    flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
    flyerbody += "    }";
    flyerbody += "    ";
    if (extra === true) {
        flyerbody += "    #column2 {";
        flyerbody += "        position: absolute;";
        flyerbody += "        width: 505px;";
        flyerbody += "        height: 430px;";
        flyerbody += "        top: -10px;";
        flyerbody += "        left: 505px;";
        flyerbody += "        font-size:" + fontsize + ";";
        flyerbody += "        font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;";
        flyerbody += "    }";
        flyerbody += "    ";
    }
    flyerbody += "<\/style>";
    flyerbody += "";
    flyerbody += "<body>";
    flyerbody += "    <img id = \"ribbon\" src = " + ribbonColor + " alt = \"ribbon failed to load\">";
    if(typeof imgSrc !== 'undefined') {
        flyerbody += "    <div id = \"image\">";
        flyerbody += "    <img id = \"imageSrc\" src = " + imgSrc + " alt = \"image failed to load\">";
        flyerbody += "    </div>";
    }
    flyerbody += "    <img id = \"top\" src = \"https://s3.amazonaws.com/eosstatic/images/0/62431aa5d4ecb32b35ab0aa8/vert_cut.png\" alt = \"top not loaded properly\">";
    if (typeof logoSrc !== 'undefined') {
        flyerbody += "<img id = \"perf\" src = " + logoSrc + " alt = \"perf logo failed to load\">";
    }
    flyerbody += "    <div id = \"msrp\">MSRP<\/div>";
    flyerbody += "    <div id = \"msrpContent\">$" + flyerMSRP + "<\/div>";
    flyerbody += "    <div id = \"savings\">SAVINGS<\/div>";
    // CPQ Fix: Don't show negative sign for $0 discount
    var savingsPrefixLandscape = (flyerDiscount && Number(flyerDiscount) > 0) ? '$-' : '$';
    flyerbody += "    <div id = \"savingsContent\">" + savingsPrefixLandscape + flyerDiscount + "<\/div>";
    flyerbody += "    <div id = \"saleprice\">SALE PRICE<\/div>";
    flyerbody += "    <div id = \"salepriceContent\">$" + flyerFinal + "<\/div>";
    flyerbody += "    <div id = \"optionalPricing\">" + escapeHtml(optionalPricing) + "<\/div>";
    flyerbody += "    <div id = \"title1\">20" + model_year + " BENNINGTON<\/div>";
    flyerbody += "    <div id = \"title2\">" + escapeHtml(document.getElementById('model') ? document.getElementById('model').value : '') + "<\/div>";
    flyerbody += "    <div id = \"power\">POWER<\/div>";
    flyerbody += "    <div id = \"powerContent\">" + escapeHtml(document.getElementById('engine') ? document.getElementById('engine').value : '') + "<\/div>";
    flyerbody += "    <div id = \"length\">LENGTH<\/div>";
    flyerbody += "    <div id = \"lengthContent\">" + escapeHtml(document.getElementById('loa') ? document.getElementById('loa').value : '') + "<\/div>";
    flyerbody += "    <div id = \"beam\">BEAM<\/div>";
    flyerbody += "    <div id = \"beamContent\">" + escapeHtml(document.getElementById('beam') ? document.getElementById('beam').value : '') + "<\/div>";
    flyerbody += "    <div id = \"dia\">PONTOON DIA<\/div>";
    flyerbody += "    <div id = \"diaContent\">" + escapeHtml(document.getElementById('diameter') ? document.getElementById('diameter').value : '') + "<\/div>";
    flyerbody += "    <div id = \"capacity\">CAPACITY<\/div>";
    flyerbody += "    <div id = \"capacityContent\">" + escapeHtml(document.getElementById('cap') ? document.getElementById('cap').value : '') + "<\/div>";
    flyerbody += "    <div id = \"hull\">HULL WEIGHT<\/div>";
    flyerbody += "    <div id = \"hullContent\">" + escapeHtml(document.getElementById('weight') ? document.getElementById('weight').value : '') + "<\/div>";
    flyerbody += "    <div id = \"fuel\">FUEL CAPACITY<\/div>";
    flyerbody += "    <div id = \"fuelContent\">" + escapeHtml(document.getElementById('fuel') ? document.getElementById('fuel').value : '') + "<\/div>";
    flyerbody += "    <div id = \"keyFeat\">KEY FEATURES AND OPTIONS<\/div>";
    flyerbody += "    <div id = \"content\">" + content + "<\/div>";
    flyerbody += "    <div id = \"optionalMessage\">" + escapeHtml(optionalMessage) + "<\/div>";
    if (dlrlogourl !== undefined) {
        flyerbody += "<img src=" + dlrlogourl + " alt=\"\" id=\"dealer\"\/>";
    }
    flyerbody += "    ";
    flyerbody += "<\/body>";
    flyerbody += "<\/html>";
    flyerbody += "";
    console.log(flyerbody);




}

if(typeof imgSrc === 'undefined') {
        console.log('AHBHABHDJWKBAKJWDhkAJHDW{AIHWfpoiujAJHNTgo');
    }


if (hasAnswer('LAYOUT', 'PORTRAIT')) {
    opt = {
        orientation: 'portrait', //try 'landscape'??
        pagesize: 'letter',
        pageheight: 280, //in mm?? If so, landscape would be 216 mm
        margins: {
            top: 0,
            left: 0,
            bottom: 0,
            right: 0
        }
    };
} else {
    opt = {
        orientation: 'landscape',
        pagesize: 'letter',
        pageheight: 216,
        margins: {
            top: 0,
            left: 0,
            bottom: 0,
            right: 0
        }
    };
}


// This is for logged users
// pdf = generatePDF('Flyer - ' + serial + ' - ' + (document.getElementById('model') ? document.getElementById('model').value : ''), flyerbody, false, opt);
console.log("CONTENT SIZE: " + contentSize);
// This one for all users, guests too
pdf = generatePDFGuest('Flyer - ' + serial + ' - ' + (document.getElementById('model') ? document.getElementById('model').value : ''), flyerbody, opt);
var url = pdf.url.replace(/\s/g, "%20");

//email keri the results for a while.
var user = getValue('EOS', 'USER');
// sendEmail(
//    'krimbaugh@benningtonmarine.com',
//    'Your flyer is here: '+
//    url,
//    'Flyer Generated by: ' + user
//);

//Save to local list so I can view some of the content they are creating.

var updtRec = [user, serial, url];
addByListName('Flyer_Links', updtRec);

window.open(url);
