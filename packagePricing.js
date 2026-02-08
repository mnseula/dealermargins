/*-------  Metadata -----
   *** Please do not touch this header ***

ID: 5f22d54ad4ecb33e9ed2ccad
NAME: Load Local Lists and Boat Variables
CODE: LOAD_VARIOUS_LISTS
RULE: EOS/CFGSTATUS[="STARTUP"]
DOWNLOAD DATE: 2025-10-06T19:13:25.076Z

-------------------------*/


window.loadPackagePricing = window.loadPackagePricing || function (serialYear, serial, snmInvoiceNo, engineERPNo) {
    console.log('Loading Variables');


    window.boatYear = serial.substring(serial.length - 2);
    window.serialYear = serialYear;

    //boat options
    if (serialYear > 4 && serialYear < 8)
    {
        window.boatoptions = loadByListName('boat_options_05_0', "Where BoatSerialNo = " + serial);
    }
    if (serialYear > 7 && serialYear < 11) {
        window.boatoptions = loadByListName('boat_options_08_10', "Where BoatSerialNo = " + serial);
    }
    if (serialYear > 10 && serialYear < 15) {
        window.boatoptions = loadByListName('boat_options11_14', "Where BoatSerialNo = " + serial);
    } else if (serialYear > 14) {
        debugger;
        //ZS 5.15.2024
        //Product Code is being imported as the MCT... need to adjust the filter to take both old and new "MCTs"
        //One below commented out because invoice number causing issues for old boats
        window.boatoptions = loadByListName('BoatOptions' + serialYear, "WHERE ItemMasterMCT <> 'DIC' AND ItemMasterMCT <> 'DIF' AND ItemMasterMCT <> 'DIP' AND ItemMasterMCT <> 'DIR' AND ItemMasterMCT <> 'DIA' AND ItemMasterMCT <> 'DIW' AND ItemMasterMCT <> 'LOY' AND ItemMasterMCT <> 'PRD' AND ItemMasterMCT <> 'VOD' AND (ItemMasterMCT <> 'DIS' OR (ItemMasterMCT = 'DIS' AND ItemNo = 'NPPNPRICE16S')) AND ItemMasterMCT <> 'DIV' AND ItemMasterMCT <> 'CAS' AND ItemMasterMCT <> 'DIW' AND (ItemMasterMCT <> 'ENZ' OR (ItemMasterMCT = 'ENZ' AND ItemDesc1 LIKE '%VALUE%')) AND ItemMasterMCT <> 'SHO' AND ItemMasterMCT <> 'GRO' AND ItemMasterMCT <> 'ZZZ' AND ItemMasterMCT <> 'FRE' AND ItemMasterMCT <> 'WAR' AND ItemMasterMCT <> 'DLR' AND ItemMasterMCT <> 'FRT' AND ItemMasterProdCat <> '111' AND (InvoiceNo = '" + snmInvoiceNo + "' OR (ERP_OrderNo = '" + engineERPNo + "' AND (MCTDesc = 'ENGINES' OR MCTDesc = 'Engine' OR MCTDesc = 'ENGINES IO' OR ItemMasterMCT= 'ELU' OR ItemMasterProdCatDesc = 'EngineLowerUnit'))) AND BoatSerialNo= '" + serial + "' ORDER BY  CASE `MCTDesc` WHEN 'PONTOONS' THEN 1 WHEN 'Pontoon Boats OB' THEN 1 WHEN 'Pontoon Boats IO' THEN 1 WHEN 'Lower Unit Eng' THEN 2 WHEN 'ENGINES' THEN 3 WHEN 'Engine' THEN 3 WHEN 'Engine IO' THEN 3 WHEN 'PRE-RIG' THEN 4 WHEN 'Prerig' THEN 4 ELSE 5 END,  LineNo ASC");
        //This new one below has invoice number filter taken out.
        // window.boatoptions2 = loadByListName('BoatOptions' + serialYear, "WHERE ItemMasterMCT <> 'DIC' AND ItemMasterMCT <> 'DIF' AND ItemMasterMCT <> 'DIP' AND ItemMasterMCT <> 'DIR' AND ItemMasterMCT <> 'DIA' AND ItemMasterMCT <> 'DIW' AND ItemMasterMCT <> 'LOY' AND ItemMasterMCT <> 'PRD' AND ItemMasterMCT <> 'VOD' AND (ItemMasterMCT <> 'DIS' OR (ItemMasterMCT = 'DIS' AND ItemNo = 'NPPNPRICE16S')) AND ItemMasterMCT <> 'DIV' AND ItemMasterMCT <> 'DIW' AND (ItemMasterMCT <> 'ENZ' OR (ItemMasterMCT = 'ENZ' AND ItemDesc1 LIKE '%VALUE%')) AND ItemMasterMCT <> 'SHO' AND ItemMasterMCT <> 'GRO' AND ItemMasterMCT <> 'ZZZ' AND ItemMasterMCT <> 'FRE' AND ItemMasterMCT <> 'WAR' AND ItemMasterMCT <> 'DLR' AND ItemMasterMCT <> 'FRT' AND ItemMasterProdCat <> '111' AND QuantitySold > 0 AND BoatSerialNo= '" + serial + "' ORDER BY  CASE `MCTDesc` WHEN 'PONTOONS' THEN 1 WHEN 'Pontoon Boats OB' THEN 1 WHEN 'Pontoon Boats IO' THEN 1 WHEN 'Lower Unit Eng' THEN 2 WHEN 'ENGINES' THEN 3 WHEN 'Engine' THEN 3 WHEN 'Engine IO' THEN 3 WHEN 'PRE-RIG' THEN 4 WHEN 'Prerig' THEN 4 ELSE 5 END,  LineNo ASC");

    }

    // MAP EXTSALESAMOUNT TO MSRP - Added 2026-02-06
    // Window sticker expects MSRP field, but BoatOptions26 has ExtSalesAmount
    if (window.boatoptions && window.boatoptions.length > 0) {
        console.log('Mapping ExtSalesAmount to MSRP for ' + window.boatoptions.length + ' items');
        for (var i = 0; i < window.boatoptions.length; i++) {
            window.boatoptions[i].MSRP = window.boatoptions[i].ExtSalesAmount || 0;
        }
    }

    console.log("BEFORE fAILURE");
    window.productids = loadByListName('Product List');

    var boatproductidrec = $.grep(productids, function (z) {
        if (serialYear === 25) {
            return (z.MODEL_YEAR === '2024' && z.PRODUCT_NAME == 'MASTER');             //GET RID OF THIS AT MODEL YEAR CUTOVER!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            console.log("MODEL YEAR 25 BOAT LOADING 24 PRODUCT MASTER!");
        } else if (serialYear === 26) {
            return (z.MODEL_YEAR === '2025' + boatYear && z.PRODUCT_NAME == 'MASTER'); //Added for fakies 6.17.2025 delete at cutover
            console.log("HITTINg THE 26 STATEMENT!");
        } else {
            return (z.MODEL_YEAR === '20' + boatYear && z.PRODUCT_NAME == 'MASTER');
            console.log("HITTINg THE ELSE STATEMENT!");
        }
    });

    if (boatproductidrec.length > 0) {
        window.boatproductid = boatproductidrec[0].PRODUCT_ID;
    }
    console.log("AFTER fAILURE");
    //window.boatmodel = $.grep(boatoptions, function (rec) { return rec.MCTDesc === 'PONTOONS'; });
    //MCT Descriptions changed with Syteline boats... use the actual MCT
    //ZACH ADDED 5/15/2024 FOR SYTELINE INTEGRATION - CHECKING FOR NORMAL AND IO BOATS
    window.boatmodel = $.grep(boatoptions, function (rec) {
        return rec.ItemMasterMCT === 'BOA' || rec.ItemMasterMCT === 'BOI';
    });
    window.fullmodel = boatmodel[0].ItemDesc1;
    window.model = boatmodel[0].ItemNo;
    window.realmodel = boatmodel[0].BoatModelNo;

    // Map SFC to SS for both model and realmodel variables early
    // The existing SF->SE logic below will then transform *SSF to *SSE
    if (model.indexOf('SFC') >= 0) {
        console.log('SFC detected in model, original:', model);
        model = model.replace('SFC', 'SS');
        console.log('Model changed to:', model);
    }

    if (realmodel.indexOf('SFC') >= 0) {
        console.log('SFC detected in realmodel, original:', realmodel);
        realmodel = realmodel.replace('SFC', 'SS');
        console.log('Realmodel changed to:', realmodel);
    }
    // Map MFC to MS for both model and realmodel variables early
    if (model.indexOf('MFC') >= 0) {
        console.log('MFC detected in model, original:', model);
        model = model.replace('MFC', 'MS');
        console.log('Model changed to:', model);
    }

    if (realmodel.indexOf('MFC') >= 0) {
        console.log('MFC detected in realmodel, original:', realmodel);
        realmodel = realmodel.replace('MFC', 'MS');
        console.log('Realmodel changed to:', realmodel);
    }

    console.log(model);
    console.log(realmodel);
    console.log(serialYear);
    console.log(model_year);
    CleanserialYear = Number(serialYear.toString().trim());
    if (model_year > 14) {
        if (serialYear === 25) {
            window.optionsMatrix = loadByListName('options_matrix_2024', "WHERE MODEL ='" + realmodel + "'");       //TAKE THIS OUT FOR MODEL YEAR CUTOVER~!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        } else if (CleanserialYear === 26) {
            window.optionsMatrix = loadByListName('options_matrix_2025', "WHERE MODEL ='" + realmodel + "'");        // Added for fakies 6.17.2025 delete at cutover
        } else {
            window.optionsMatrix = loadByListName('options_matrix_20' + boatYear, "WHERE MODEL ='" + realmodel + "'");
        }
    }

    console.log('Get last two of boat and engine');


    window.lasttwoletters = realmodel.substring(realmodel.length - 2);
    window.boatlasttwo = serial.substring(serial.length - 2);

    console.log('lasttwoletters', lasttwoletters);

    //window.twoLetters = model.substring(model.length - 2);

    window.isWindscreen = 'N'; //wind screens use side mount prerigs by default.

    if (model.indexOf('WW') > 0 || model.indexOf('SBW') > 0 || model.indexOf('FBW') > 0 || model.indexOf('SRW') > 0 || model.indexOf('QXS') > 0) {
        isWindscreen = 'Y';
        ben.log('This boat is a windscreen?', isWindscreen);
    }

    window.two = '0';

    if (lasttwoletters === 'DR') {
        two = '14';
    } else if (lasttwoletters === 'DE') {
        two = '15';
    } else if (lasttwoletters === 'DF') {
        two = '16';
    } else if (lasttwoletters === 'DL') {
        two = '17';
    } else if (lasttwoletters === 'DI') {
        two = '18';
    } else if (lasttwoletters === 'DN') {
        two = '19';
    } else if (lasttwoletters === 'SG') {
        two = '20';
    } else if (lasttwoletters === 'SD') {
        two = '21';
    } else if (lasttwoletters === 'ST') {
        two = '22';
    } else if (lasttwoletters === 'SP') {
        two = '23';
    } else if (lasttwoletters === 'SR') {
        two = '24';
    } else if (lasttwoletters === 'SE') {
        two = '25';
    } else if (lasttwoletters === 'SF') {
        // Check if this is an SFC-derived boat (contains 'SS' from SFC->SS transformation)
    //    if (realmodel.indexOf('SS') >= 0) {
            // SFC boat: convert SF to SE and use 2025 lists (e.g., 188SSSF -> 188SSSE)
            two = '25';
            realmodel = realmodel.substring(0, realmodel.length - 2) + 'SE';
          //  console.log('SFC-derived SF boat converted to SE:', realmodel);
        //} else {
            // Regular 2026 SF boat: keep SF and use 2026 lists
            //two = '26';
        //}
    }

    // CPQ CATCHALL - Added 2026-02-06
    // CPQ boats use floorplan codes (ML, QB, etc.) not year codes
    // If no year code matched (two still '0'), use serialYear to determine year
    var isCPQBoat = false;  // Flag to track if this is a CPQ boat
    if (two === '0') {
        isCPQBoat = true;  // Mark as CPQ boat
        console.log('CPQ boat detected (no year code match) - using serialYear:', serialYear);
        if (serialYear === 26) {
            two = '25';  // 2026 boats use 2025 model year lists
        } else if (serialYear === 25) {
            two = '24';
        } else if (serialYear === 24) {
            two = '23';
        } else if (serialYear === 23) {
            two = '22';
        } else if (serialYear >= 14) {
            // General formula for other years
            two = String(serialYear - 1);
            if (two.length === 1) {
                two = '0' + two;  // Pad single digit (e.g., '9' -> '09')
            }
        } else {
            console.warn('Unable to determine year for model:', realmodel, 'serialYear:', serialYear);
            two = String(serialYear);
            if (two.length === 1) {
                two = '0' + two;
            }
        }
        console.log('CPQ boat year calculated: two =', two);
    }

    console.log('two', two);
    console.log('RealModel', realmodel)
    //Completed: SFC substitution - 188SFCSF is changed to 188SSSF, then SF->SE logic makes it 188SSSE
    window.currentmodelyear = '20' + two;


    window.blo = loadByListName('Boats_ListOrder_20' + two, "WHERE REALMODELNAME = '" + realmodel + "'");
    console.log(blo);

    // CPQ FALLBACK - ONLY for CPQ boats (isCPQBoat = true)
    // If Boats_ListOrder is empty for a CPQ boat, get SERIES from boatoptions
    // blo might be an empty object {} instead of an array, so check if blo[0] is undefined
    if ((!blo || !blo[0] || blo.length === 0) && isCPQBoat && boatoptions && boatoptions.length > 0) {
        console.log('CPQ boat detected and Boats_ListOrder query failed - using CPQ fallback');
        // Extract SERIES from the boat record (already loaded in boatoptions)
        var boatRecord = $.grep(boatoptions, function (rec) {
            return rec.ItemMasterMCT === 'BOA' || rec.ItemMasterMCT === 'BOI';
        });

        if (boatRecord.length > 0 && boatRecord[0].Series) {
            console.log('CPQ boat: Using SERIES from boatoptions:', boatRecord[0].Series);
            window.series = boatRecord[0].Series;
            window.boatpricingtype = 'reg';  // CPQ boats use regular pricing
        } else {
            console.log('ERROR: Could not find boat record in boatoptions for CPQ boat');
            alert('Model was not found! Contact your administrator to report about this error.');
            window.series = '';
            window.boatpricingtype = '';
        }
    } else if (!blo || !blo[0] || blo.length === 0) {
        // For non-CPQ boats, if Boats_ListOrder fails, show error (original behavior)
        alert('Model was not found! Contact your administrator to report about this error.');
        window.series = '';
        window.boatpricingtype = '';
    } else {
        // Normal path: Boats_ListOrder query succeeded
        window.boatpricingtype = blo[0].PRICING || ''; //pp, ppd or reg
        window.series = blo[0].SERIES || '';
    }


    if (serialYear > 13) {
        window.stndsMtrx = loadByListName('standards_matrix' + '_20' + two, "WHERE (MODEL ='" + realmodel + "')");
    }

    if (serialYear < 21) {
        window.priceDesc = loadByListName('Price Descriptions');
    } else {
        window.priceDesc = loadByListName('Price Descriptions 2021 - New');
    }

    if (serialYear === 25) {                                                         //TAKE THIS OUT AT MODEL YEAR CUTOVER!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        window.bpp = loadByListName('Boat_Package_Pricing_2024');
    } else {
        window.bpp = loadByListName('Boat_Package_Pricing_20' + two);
    }


};
