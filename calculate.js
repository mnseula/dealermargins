/*-------  Metadata -----
   *** Please do not touch this header ***

ID: 5f36a863d4ecb35f817bfee7
NAME: Calculate 2021 +
CODE: CALCULATE_2021
RULE:
DOWNLOAD DATE: 2025-10-06T18:56:44.213Z

-------------------------*/

window.Calculate2021 = window.Calculate2021 || function () {
    console.log('calculate 2021');

    var boatpackageprice = 0;
    var saleboatpackageprice = 0;
    var msrpboatpackageprice = 0;
    var saleboatpackageprice = 0;
    var msrptotal = 0;

    window.hasengine = 0; //use this to determine if there is a boat package or not.
    window.hasprerig = 0; //regular or special
    window.retryPrerig = 0; //We may need to go back over the prerig

    var additionalCharge = getValue('EXTRAS', 'ADD_CHARGE');
    if (additionalCharge === "" || additionalCharge === false || additionalCharge === true) { additionalCharge = 0; }
    var twinenginecost = 0;
    window.EngineDiscountAdditions = 0;
    window.hasEngineDiscount = false;
    window.hasEngineLowerUnit = false;
    window.EngineLowerUnitAdditions = 0;

    // USER AUTHORIZATION: Check if user is authorized to see CPQ boats
    var user = getValue('EOS','USER');
    var isCpqAuthorized = (user.includes('@BENNINGTONMARINE.COM') || user === 'BGIRTEN' || user === 'STHOROLD' || user === 'SFISH' || user === 'KBURCH' || user === 'BALLEN' || user === 'JROMERO' || user === 'BEN');

    $.each(boatoptions, function (j) {
        var mct = boatoptions[j].MCTDesc;
        var mctType = boatoptions[j].ItemMasterMCT;

        // SAFETY: For CPQ base boat, use extracted dealer cost from "Base Boat" line (if available and user authorized)
        // Falls back to ExtSalesAmount for legacy boats or if CPQ extraction failed or user not authorized
        var dealercost = (mct === 'PONTOONS' && isCpqAuthorized && window.cpqBaseBoatDealerCost && Number(window.cpqBaseBoatDealerCost) > 0)
            ? window.cpqBaseBoatDealerCost
            : boatoptions[j].ExtSalesAmount;

        // SAFETY: Log if using CPQ dealer cost vs standard
        if (mct === 'PONTOONS' && isCpqAuthorized && window.cpqBaseBoatDealerCost && Number(window.cpqBaseBoatDealerCost) > 0) {
            console.log('Using CPQ dealer cost: $' + dealercost);
        }

        var macoladesc = boatoptions[j].ItemDesc1;
        var prodCategory = boatoptions[j].ItemMasterProdCat;
        var itemNo = boatoptions[j].ItemNo; // Original numeric ItemNo
        var displayItemNo = boatoptions[j].ItemDesc1 || itemNo; // Use ItemDesc1 for display, fallback to ItemNo
        var boatModel = boatoptions[j].BoatModelNo;
        var qty = 1;
        var shownDealerCost = getValue('DLR2','BOAT_DC');

        // CPQ MSRP Support - Added 2026-02-08
        // Check if this item has real MSRP from CPQ system (instead of calculated from dealer cost)
        // SAFETY: First check if CPQ base boat pricing was extracted in packagePricing.js AND user is authorized
        // Falls back to boatoptions[j].MSRP for legacy boats (which is typically 0 or null)
        var realMSRP = (isCpqAuthorized && window.cpqBaseBoatMSRP && Number(window.cpqBaseBoatMSRP) > 0)
            ? window.cpqBaseBoatMSRP
            : boatoptions[j].MSRP;

        var hasRealMSRP = (realMSRP !== undefined && realMSRP !== null && Number(realMSRP) > 0);

        if (hasRealMSRP) {
            if (isCpqAuthorized && window.cpqBaseBoatMSRP && Number(window.cpqBaseBoatMSRP) > 0) {
                console.log('CPQ item with real MSRP from Base Boat: ' + displayItemNo + ' = $' + realMSRP);
            } else {
                console.log('Item with MSRP from record: ' + displayItemNo + ' = $' + realMSRP);
            }
        }

        if (mctType === 'DIS' || mctType === 'DIV') { EngineDiscountAdditions = Number(dealercost) + Number(EngineDiscountAdditions); }
        if (mctType === 'ENZ') { hasEngineDiscount = true; }
        console.log('hasEngineDiscount', hasEngineDiscount);

        if (mct === 'PONTOONS') {
            boatpackageprice = boatpackageprice + Number(dealercost); //dealer cost has no f & p

            //PACKAGE DISCOUNTS WERE RECEIVED FROM MICHAEL BLANK
            //LOGIC IS BUILT USING SERIES AND LENGTH OF BOAT
            //LOGIC BUILT BY ZACH SPRINGMAN ON 1/17/2024

            //PACKAGE DISCOUNTS FOR SV SERIES
            if(series === "SV" && boatModel.match(/188.*/)) {
                boatpackageprice = boatpackageprice - 1650;
                console.log("18 FOOT SV BOAT DISCOUNT ADDED.");
            } else if (series === "SV" && boatModel.match(/20.*/)) {
                boatpackageprice = boatpackageprice - 1700;
                console.log("20 FOOT SV BOAT DISCOUNT ADDED.");
            } else if (series === "SV" && boatModel.match(/22.*/)) {
                boatpackageprice = boatpackageprice - 750;
                console.log("22 FOOT SV BOAT DISCOUNT ADDED.");
            }

            // Store real MSRP for pontoon if available (used later in boattable)
            if (hasRealMSRP) {
                window.pontoonRealMSRP = Number(realMSRP);
                console.log('Stored pontoon real MSRP: $' + window.pontoonRealMSRP);
            } else {
                window.pontoonRealMSRP = null;
            }

            //PACKAGE DISCOUNTS FOR S SERIES
            if(series === "S" && boatModel.match(/20.*/)) {
                boatpackageprice = boatpackageprice - 1700;
                console.log("20 FOOT S BOAT DISCOUNT ADDED.");
            } else if (series === "S" && boatModel.match(/188.*/)) {
                boatpackageprice = boatpackageprice - 1650;
                console.log("18 FOOT S BOAT DISCOUNT ADDED.");
            } else if (series === "S" && boatModel.match(/22.*/)) {
                boatpackageprice = boatpackageprice - 750;
                console.log("22 FOOT S BOAT DISCOUNT ADDED.");
            }

            //PACKAGE DISCOUNTS FOR S CLASSIC SERIES
            if(series === "S_23" && boatModel.match(/20.*/)) {
                boatpackageprice = boatpackageprice - 1700;
                console.log("20 FOOT S_23 BOAT DISCOUNT ADDED.");
            } else if (series === "S_23" && boatModel.match(/16.*/)) {
                boatpackageprice = boatpackageprice - 1300;
                console.log("16 FOOT S_23 BOAT DISCOUNT ADDED.");
            } else if (series === "S_23" && boatModel.match(/18.*/)) {
                boatpackageprice = boatpackageprice - 1650;
                console.log("18 FOOT S_23 BOAT DISCOUNT ADDED.");
            } else if (series === "S_23" && boatModel.match(/19.*/)) {
                boatpackageprice = boatpackageprice - 1650;
                console.log("19 FOOT S_23 BOAT DISCOUNT ADDED.");
            } else if (series === "S_23" && boatModel.match(/21.*/)) {
                boatpackageprice = boatpackageprice - 1000;
                console.log("21 FOOT S_23 BOAT DISCOUNT ADDED.");
            } else if (series === "S_23" && boatModel.match(/22.*/)) {
                boatpackageprice = boatpackageprice - 750;
                console.log("22 FOOT S_23 BOAT DISCOUNT ADDED.");
            }

            //PACKAGE DISCOUNTS FOR SV CLASSIC SERIES
            if (series === "SV_23" && boatModel.match(/21.*/)) {
                boatpackageprice = boatpackageprice - 1000;
                console.log("21 FOOT SV_23 BOAT DISCOUNT ADDED.");
            } else if (series === "SV_23" && boatModel.match(/22.*/)) {
                boatpackageprice = boatpackageprice - 750;
                console.log("22 FOOT SV_23 BOAT DISCOUNT ADDED.");
            }

            //PACKAGE DISCOUNTS FOR SX SERIES
            if (series === "SX" && boatModel.match(/16.*/)) {
                boatpackageprice = boatpackageprice - 1300;
                console.log("16 FOOT SX BOAT DISCOUNT ADDED.");
            } else if (series === "SX" && boatModel.match(/18.*/)) {
                boatpackageprice = boatpackageprice - 1650;
                console.log("18 FOOT SX BOAT DISCOUNT ADDED.");
            } else if (series === "SX" && boatModel.match(/20.*/)) {
                boatpackageprice = boatpackageprice - 1700;
                console.log("20 FOOT SX BOAT DISCOUNT ADDED.");
            } else if (series === "SX" && boatModel.match(/21.*/)) {
                boatpackageprice = boatpackageprice - 1000;
                console.log("21 FOOT SX BOAT DISCOUNT ADDED.");
            } else if (series === "SX" && boatModel.match(/22.*/)) {
                boatpackageprice = boatpackageprice - 750;
                console.log("22 FOOT SX BOAT DISCOUNT ADDED.");
            } else if (series === "SX" && boatModel.match(/23.*/)) {
                boatpackageprice = boatpackageprice - 750;
                console.log("23 FOOT SX BOAT DISCOUNT ADDED.");
            } else if (series === "SX" && boatModel.match(/24.*/)) {
                boatpackageprice = boatpackageprice - 750;
                console.log("24 FOOT SX BOAT DISCOUNT ADDED.");
            } else if (series === "SX" && boatModel.match(/25.*/)) {
                boatpackageprice = boatpackageprice - 750;
                console.log("25 FOOT SX BOAT DISCOUNT ADDED.");
            } else if (series === "SX" && boatModel.match(/26.*/)) {
                boatpackageprice = boatpackageprice - 750;
                console.log("26 FOOT SX BOAT DISCOUNT ADDED.");
            }

            //PACKAGE DISCOUNTS FOR L SERIES
            if (series === "L" && boatModel.match(/18.*/)) {
                boatpackageprice = boatpackageprice - 1650;
                console.log("18 FOOT L BOAT DISCOUNT ADDED.");
            } else if (series === "L" && boatModel.match(/20.*/)) {
                boatpackageprice = boatpackageprice - 1700;
                console.log("20 FOOT L BOAT DISCOUNT ADDED.");
            } else if (series === "L" && boatModel.match(/21.*/)) {
                boatpackageprice = boatpackageprice - 1700;
                console.log("21 FOOT L BOAT DISCOUNT ADDED.");
            } else if (series === "L" && boatModel.match(/22.*/)) {
                boatpackageprice = boatpackageprice - 750;
                console.log("22 FOOT L BOAT DISCOUNT ADDED.");
            } else if (series === "L" && boatModel.match(/23.*/)) {
                boatpackageprice = boatpackageprice - 750;
                console.log("23 FOOT L BOAT DISCOUNT ADDED.");
            } else if (series === "L" && boatModel.match(/24.*/)) {
                boatpackageprice = boatpackageprice - 750;
                console.log("24 FOOT L BOAT DISCOUNT ADDED.");
            } else if (series === "L" && boatModel.match(/25.*/)) {
                boatpackageprice = boatpackageprice - 750;
                console.log("25 FOOT L BOAT DISCOUNT ADDED.");
            } else if (series === "L" && boatModel.match(/26.*/)) {
                boatpackageprice = boatpackageprice - 750;
                console.log("26 FOOT L BOAT DISCOUNT ADDED.");
            }

            //PACKAGE DISCOUNTS FOR LT SERIES
            if(series === "LT") {
                boatpackageprice = boatpackageprice - 750;
                console.log("LT PACKAGE DISCOUNT ADDED.")
            }

            //PACKAGE DISCOUNTS FOR LX SERIES
            if(series === "LX") {
                boatpackageprice = boatpackageprice - 750;
                console.log("LX PACKAGE DISCOUNT ADDED.")
            }

            console.log('boat package price (+Pontoon) is now ', boatpackageprice);
            boatsp = (Number(dealercost) / baseboatmargin) * vol_disc + Number(additionalCharge);
            setValue('DLR2', 'BOAT_DC', dealercost);
            setValue('DLR2', 'BOAT_DESC', macoladesc);
            console.log(freight);
            console.log(prep);
            console.log(additionalCharge);
            console.log(vol_disc);
            console.log('MSRP Margin: ', msrpMargin);

            saleboatpackageprice += ((dealercost * vol_disc) /baseboatmargin) + Number(freight) + Number(prep) + Number(additionalCharge);
            console.log('boat package SALE price (+Pontoon) is now ', saleboatpackageprice);
        }
        if (mct === 'Lower Unit Eng') {
            console.error('lower Unit found');
            window.hasEngineLowerUnit = true;
            window.EngineLowerUnitAdditions = Number(dealercost);
            console.error('Amount to Add for Lower Unit', window.EngineLowerUnitAdditions);
        }
        if (mct === 'ENGINES' || mct === 'ENGINES I/O') {
            hasengine = '1';
            if (realmodel.indexOf('X2') > 0 && (macoladesc.indexOf('CTR') > 0 || macoladesc.indexOf('COUNTER') > 0)) {
                twinenginesp = (Number(dealercost) / enginemargin) * vol_disc;
                saleboatpackageprice = boatpackageprice + twinenginesp;
            }

            window.engineitemno = itemNo; // Use original ItemNo for engine logic
            window.enginedesc = boatoptions[j].ItemDesc1;
            console.log('engine item no', window.engineitemno, 'boat product id', boatproductid);

            // Modified: Use itemNo for designator extraction to preserve numeric logic
            window.twoEngineLetters = itemNo && typeof itemNo === 'string' ?
                itemNo.substring(itemNo.length - 2) : 'SD';
            if (twoEngineLetters == 'DE' || twoEngineLetters == 'DF' || twoEngineLetters == 'DR' || twoEngineLetters == 'DL' || twoEngineLetters == 'DI' || twoEngineLetters == 'DN' || twoEngineLetters == 'SG') {
                console.log('Has Engine Letter Designator');
            } else {
                window.twoEngineLetters = 'SD'; // default
            }

            console.log('Engine Letters Are', window.twoEngineLetters);

            var engproductidrec = $.grep(productids, function (y) { return (y.PRODUCT_NAME == 'MASTER' && y.SUFFIX == twoEngineLetters); });

            if (engproductidrec.length > 0) { window.engproductid = engproductidrec[0].PRODUCT_ID; }
            console.log('engprodid ', engproductid);

            window.defaultengineprice = getEngineInfo(window.engineitemno, engproductid);
            console.log('Default Engine Price', defaultengineprice);
            boatpackageprice = boatpackageprice + Number(defaultengineprice);
            console.log('boat package price (+engine) is now ', boatpackageprice);

            engineonboatprice = dealercost;

            setValue('DLR2', 'ENG_FULL_W_MARGIN_SALE', Math.round(defaultengineprice / enginemargin) * vol_disc);

            if (serialYear < 20) {
                setValue('DLR2', 'ENG_FULL_W_MARGIN_MSRP', Math.round(defaultengineprice / msrpMargin));
            }
            else {
                setValue('DLR2', 'ENG_FULL_W_MARGIN_MSRP', Math.round(defaultengineprice / msrpMargin) * vol_disc);
            }

            if (window.hasEngineLowerUnit) {
                Newengineonboatprice = Number(engineonboatprice) + Number(window.EngineLowerUnitAdditions);
                engineonboatprice = Newengineonboatprice;
            }
            window.engineincrement = engineonboatprice - defaultengineprice;

            console.log('Engine Inc is', engineincrement);

            enginesp = (Number(engineincrement) / enginemargin) * vol_disc;
            defaultenginesp = (Number(defaultengineprice) / enginemargin) * vol_disc;

            saleboatpackageprice = saleboatpackageprice + defaultenginesp;
            console.log('boat package SALE price (+engine) is now ', saleboatpackageprice);
            setValue('DLR2', 'ENGINE_INC', engineincrement);
        }
        if (mct === 'PRE-RIG') {
            hasprerig = '1';
            var prerigonboatprice = dealercost;

            if ((defaultprerigprice === undefined || defaultprerigprice === false)) {
                defaultprerigprice = getValue('DLR2', 'DEF_PRERIG_COST');
                if (defaultprerigprice == false) { window.retryPrerig = 1; }
            }

            if ((defaultprerigprice === undefined || defaultprerigprice === false) && hasengine === '1') { window.defaultengineprice = getEngineInfo(window.engineitemno, engproductid) };
            window.prerigincrement = prerigonboatprice - defaultprerigprice;

            setValue('DLR2', 'PRERIG_FULL_W_MARGIN_SALE', Math.round(prerigonboatprice / optionmargin) * vol_disc);

            if (serialYear < 20) {
                setValue('DLR2', 'PRERIG_FULL_W_MARGIN_MSRP', Math.round(prerigonboatprice / msrpMargin));
            }
            else {
                setValue('DLR2', 'PRERIG_FULL_W_MARGIN_MSRP', Math.round(prerigonboatprice / msrpMargin) * vol_disc);
            }

            defaultprerigsp = (defaultprerigprice / optionmargin) * vol_disc;
            defaultprerigprice = getValue('DLR2', 'DEF_PRERIG_COST');

            if (prodCategory != 'PL1' && prodCategory != 'PL2' && prodCategory != 'PL3' && prodCategory != 'PL4' && prodCategory != 'PL5' && prodCategory != 'PL6') {
                boatpackageprice = boatpackageprice + Number(defaultprerigprice);
            }

            prerigsp = (Number(prerigincrement) / optionmargin) * vol_disc;

            if (prodCategory != 'PL1' && prodCategory != 'PL2' && prodCategory != 'PL3' && prodCategory != 'PL4' && prodCategory != 'PL5' && prodCategory != 'PL6') {
                saleboatpackageprice = saleboatpackageprice + defaultprerigsp;
            }
        }
    });

    if (window.retryPrerig == 1 && window.hasengine == 1) {
        console.error('We need to retry pre rig if it now has an engine');
        var manualPreRig = $.grep(boatoptions, function (rec) { return rec.MCTDesc === 'PRE-RIG'; });
        var dealercost = manualPreRig.ExtSalesAmount;

        hasprerig = '1';
        var prerigonboatprice = dealercost;
        if ((defaultprerigprice === undefined || defaultprerigprice === false)) {
            defaultprerigprice = getValue('DLR2', 'DEF_PRERIG_COST');
            if (defaultprerigprice == false) { window.retryPrerig = 1; }
        }

        if ((defaultprerigprice === undefined || defaultprerigprice === false) && hasengine === '1') { window.defaultengineprice = getEngineInfo(window.engineitemno, engproductid) };
        console.debug('defaultprerigprice', defaultprerigprice);
        window.prerigincrement = prerigonboatprice - defaultprerigprice;

        defaultprerigsp = (defaultprerigprice / optionmargin) * vol_disc;
        defaultprerigprice = getValue('DLR2', 'DEF_PRERIG_COST');

        boatpackageprice = boatpackageprice + Number(defaultprerigprice);
        prerigsp = (Number(prerigincrement) / optionmargin) * vol_disc;
        saleboatpackageprice = saleboatpackageprice + defaultprerigsp;
    }

    if (hasengine == '0') {
        removeengine = '1';
        setValue('DLR', 'HASENGINE', '0');
        setAnswer('RMV_ENG', 'YES');
        var defaultprerigprice = 0;
    }

    if (hasengine === '1' && hasprerig === '1' && removeengine === '0') {
        var showpkgline = 1;
        setValue('DLR', 'HASENGINE', '1');
    } else { var showpkgline = '0'; }
    console.log('hasengine', hasengine);

    boatpackageprice = Number(boatpackageprice);
    console.log('boat package price is now ', boatpackageprice);

    console.log('pkgmsrp is ', pkgmsrp);

    if (pkgmsrp == 0) {
        msrpboatpackageprice = Number(boatpackageprice * msrpVolume) / msrpMargin + additionalCharge;
        console.log('boatpackageprice 202', boatpackageprice);
        console.log('msrpvolume 202', msrpVolume);
        console.log('msrpMargin', msrpMargin);
        console.log('additionalCharge', additionalCharge);
        console.log('msrpboatpackageprice 202', msrpboatpackageprice);

        if (series == 'SV') {
            console.log('Keri Additional Charge', additionalCharge);
            msrpboatpackageprice = Number((boatpackageprice * msrpVolume * msrpLoyalty) / msrpMargin) + Number(additionalCharge);
            console.log('msrp package price', Math.round(msrpboatpackageprice));
            saleboatpackageprice = Math.round(msrpboatpackageprice);
        }
    }

    if (hasengine === '1') {
        boattable.push({
            'ItemDesc1': 'BOAT PACKAGE', 'ItemNo': 'BOAT, ENGINE, PRE-RIG', 'Qty': '', 'MCT': 'BOATPKG', 'PC': '',
            'DealerCost': Math.round(boatpackageprice),
            'SalePrice': Math.round(saleboatpackageprice),
            'MSRP': Math.round(msrpboatpackageprice),
            'Increment': ''
        });
    }

    var discountsIncluded = 0;
    $.each(boatoptions, function (i) {
        var itemno = boatoptions[i].ItemNo; // Original numeric ItemNo
        var displayItemNo = boatoptions[i].ItemDesc1 || itemno; // Use ItemDesc1 for display
        var mct = boatoptions[i].MCTDesc;
        var mctType = boatoptions[i].ItemMasterMCT;
        var prodCategory = boatoptions[i].ItemMasterProdCat;
        var qty = boatoptions[i].QuantitySold;
        if (mct === 'BOA') {
            var itemdesc = boatoptions[i].ItemDesc1.toUpperCase();
        } else {
            if (optionsMatrix !== undefined && optionsMatrix.length > 0) {
                itemOmmLine = $.grep(optionsMatrix, function (i) {
                    return i.PART === itemno; // Use original ItemNo for lookup
                });
                if (itemOmmLine.length > 0 && itemOmmLine[0].OPT_NAME !== "") {
                    itemdesc = itemOmmLine[0].OPT_NAME.toUpperCase();
                } else {
                    itemdescRec = sStatement('SLT_ONE_REC_OMM_2016', [itemno]); // Use original ItemNo
                    if (itemdescRec.length === 0) {
                        itemdescRec = sStatement('SLT_ONE_REC_OMM_2016', [displayItemNo]); // Try ItemDesc1
                    }
                    if (itemdescRec.length > 0 && itemdescRec[0].OPT_NAME != "") {
                        itemdesc = itemdescRec[0].OPT_NAME.toUpperCase();
                    } else {
                        itemdesc = boatoptions[i].ItemDesc1.toUpperCase();
                    }
                }
            } else {
                itemdesc = boatoptions[i].ItemDesc1.toUpperCase();
            }
        }
        var dealercost = boatoptions[i].ExtSalesAmount;
        var mct = boatoptions[i].MCTDesc;
        var qty = boatoptions[i].QuantitySold;
        var pc = boatoptions[i].ItemMasterProdCat;
        var saleprice = 0;

        if (mct == 'PONTOONS') {
            // CPQ MSRP Support: Use real MSRP if available, otherwise calculate
            if (window.pontoonRealMSRP !== null && window.pontoonRealMSRP !== undefined) {
                msrpprice = Number(window.pontoonRealMSRP);
                console.log("Using real MSRP from CPQ: $", msrpprice);
            } else {
                msrpprice = Number((dealercost) * vol_disc) / msrpMargin + Number(additionalCharge);
                console.log("Calculated MSRP from dealer cost: $", msrpprice);
            }

            saleprice = Number((dealercost * vol_disc) / baseboatmargin) + Number(freight) + Number(prep) + Number(additionalCharge);

            if(series === 'SV') {
                saleprice = Number((dealercost * msrpVolume * msrpLoyalty) / baseboatmargin) + Number(freight) + Number(prep) + Number(additionalCharge);
                // For SV series, only override MSRP with saleprice if we don't have real CPQ MSRP
                if (window.pontoonRealMSRP === null || window.pontoonRealMSRP === undefined) {
                    msrpprice = saleprice;
                }
            }
            setValue('DLR2', 'BOAT_SP', Math.round(saleprice));
            setValue('DLR2', 'BOAT_MS', Math.round(msrpprice));
        }

        else if (mct !== 'ENGINES' && mct !== 'ENGINES I/O' && mct != 'Lower Unit Eng' && mct != 'PRE-RIG') {
            if (mctType === 'ENZ') { dealercost = Number(dealercost) + Number(EngineDiscountAdditions); }

            // CPQ MSRP Support: Use real MSRP if available, otherwise calculate
            // Check boatoptions[i].MSRP directly in this loop (not from outer loop variable)
            var itemHasRealMSRP = (boatoptions[i].MSRP !== undefined && boatoptions[i].MSRP !== null && Number(boatoptions[i].MSRP) > 0);
            if (itemHasRealMSRP) {
                var msrpprice = Number(boatoptions[i].MSRP);
                console.log("Using real MSRP from CPQ for option: $", msrpprice);
            } else {
                var msrpprice = Number((dealercost * msrpVolume) / msrpMargin);
            }

            if (series == 'SV') {
                // For SV series, only apply loyalty multiplier if we're calculating (not using real MSRP)
                if (!itemHasRealMSRP) {
                    msrpprice = Number(msrpprice * msrpLoyalty);
                }
                saleprice = msrpprice;
            } else {
                if (dealercost > 0) {
                    saleprice = (Number(dealercost / optionmargin) * vol_disc);
                } else {
                    saleprice = Number(dealercost);
                    msrpprice = Number(dealercost);
                }
            }
        }

        if (mct !== 'ENGINES' && mct !== 'ENGINES I/O' && mct != 'Lower Unit Eng' && mct != 'PRE-RIG') {
            if ((mctType === 'DIS' || mctType === 'DIV') && !hasEngineDiscount && discountsIncluded === 0) {
                discountsIncluded = 1;
                saleprice = Number((EngineDiscountAdditions * vol_disc) / baseboatmargin);

                // CPQ MSRP Support: For discounts, use real MSRP if available
                var discountHasRealMSRP = (boatoptions[i].MSRP !== undefined && boatoptions[i].MSRP !== null && Number(boatoptions[i].MSRP) > 0);
                if (discountHasRealMSRP) {
                    msrpprice = Number(boatoptions[i].MSRP);
                } else {
                    msrpprice = Number((EngineDiscountAdditions * msrpVolume) / msrpMargin);
                }

                if (series == 'SV' && !discountHasRealMSRP) {
                    msrprice = msrpprice * msrpLoyalty;
                }

                boattable.push({
                    'ItemDesc1': 'Limited time value series discount',
                    'ItemNo': displayItemNo, // Use ItemDesc1 for display
                    'Qty': qty, 'MCT': mct, 'PC': pc,
                    'DealerCost': EngineDiscountAdditions,
                    'SalePrice': Math.round(saleprice).toFixed(2),
                    'MSRP': Math.round(msrpprice).toFixed(2)
                });
            }
            else if (mctType === 'DIS' || mctType === 'DIV') {
            } else {
                boattable.push({
                    'ItemDesc1': itemdesc,
                    'ItemNo': displayItemNo, // Use ItemDesc1 for display
                    'Qty': qty,
                    'MCT': mct,
                    'PC': pc,
                    'DealerCost': dealercost,
                    'SalePrice': Math.round(saleprice).toFixed(2),
                    'MSRP': Math.round(msrpprice).toFixed(2)
                });
            }
        }

        if (mct == 'ENGINES' || mct == 'ENGINES I/O') {
            engineinvoiceno = boatoptions[i].InvoiceNo;
            if (showpkgline == '1') {
                if (window.hasEngineLowerUnit) {
                    console.error('Has lower unit like 998');
                    dealercost = Number(dealercost) + Number(window.EngineLowerUnitAdditions);
                }
                dealercost = Number(dealercost - Number(defaultengineprice));
                boatpackageprice = Number(boatpackageprice) - Number(dealercost);

                msrpboatpackageprice = Number(msrpboatpackageprice) - Math.round(Number(dealercost * msrpVolume) / msrpMargin);

                if(series === 'SV') {
                    msrpboatpackageprice = msrpboatpackageprice;
                }

                if (dealercost == 0) { saleprice = 0; }
                else { saleprice = Math.round(Number(dealercost / enginemargin) * vol_disc); }

                // CPQ MSRP Support: Use real MSRP if available (for engine increment)
                // Note: hasRealMSRP and realMSRP are from the outer loop variable
                var engineHasRealMSRP = (boatoptions[i].MSRP !== undefined && boatoptions[i].MSRP !== null && Number(boatoptions[i].MSRP) > 0);
                if (engineHasRealMSRP) {
                    msrp = Number(boatoptions[i].MSRP).toFixed(2);
                    console.log("Using real MSRP from CPQ for engine: $", msrp);
                } else if(series === 'SV') {
                    msrp = Math.round(Number((dealercost * msrpVolume * msrpLoyalty)/ msrpMargin)).toFixed(2);
                    saleprice = msrp;
                } else {
                    msrp = Math.round(Number((dealercost * msrpVolume)/ msrpMargin)).toFixed(2);
                }

                boattable.push({
                    'ItemDesc1': itemdesc,
                    'ItemNo': displayItemNo, // Use ItemDesc1 for display
                    'Qty': qty,
                    'MCT': mct,
                    'PC': pc,
                    'DealerCost': dealercost,
                    'SalePrice': saleprice,
                    'MSRP': msrp,
                    'Increment': '1'
                });
            }
        }

        if (mct == 'PRE-RIG') {
            if (showpkgline == '1') { // Fixed syntax error: was show(pkgline == '1')
                defaultprerigprice = getValue('DLR2', 'DEF_PRERIG_COST');
                if (prodCategory != 'PL1' && prodCategory != 'PL2' && prodCategory != 'PL3' && prodCategory != 'PL4' && prodCategory != 'PL5' && prodCategory != 'PL6') { } else {
                    defaultprerigprice = Number(0);
                }
                dealercost = Number(dealercost - Number(defaultprerigprice));

                if (dealercost == 0) { saleprice = 0; }
                else { saleprice = (Number(dealercost / optionmargin) * vol_disc); }
                if (prodCategory != 'PL1' && prodCategory != 'PL2' && prodCategory != 'PL3' && prodCategory != 'PL4' && prodCategory != 'PL5' && prodCategory != 'PL6') {
                    boatpackageprice = Number(boatpackageprice) - Number(dealercost);
                    msrpboatpackageprice = Number(msrpboatpackageprice) - (Number(dealercost) / msrpMargin);
                    setValue('DLR2', 'PRERIG_INC', dealercost);
                }

                // CPQ MSRP Support: Use real MSRP if available (for prerig increment)
                var prerigHasRealMSRP = (boatoptions[i].MSRP !== undefined && boatoptions[i].MSRP !== null && Number(boatoptions[i].MSRP) > 0);
                if (prerigHasRealMSRP) {
                    msrp = Number(boatoptions[i].MSRP).toFixed(2);
                    console.log("Using real MSRP from CPQ for prerig: $", msrp);
                } else if(series === 'SV') {
                    msrp = Math.round(Number((dealercost * msrpVolume * msrpLoyalty )/ msrpMargin)).toFixed(2);
                } else {
                    msrp = Math.round(Number((dealercost * msrpVolume)/ msrpMargin)).toFixed(2);
                }

                boattable.push({
                    'ItemDesc1': itemdesc,
                    'ItemNo': displayItemNo, // Use ItemDesc1 for display
                    'Qty': qty,
                    'MCT': mct,
                    'PC': pc,
                    'DealerCost': dealercost,
                    'SalePrice': Math.round(saleprice),
                    'MSRP': msrp,
                    'Increment': '1'
                });
            }
        }

        if (mct == 'TUBE UPGRADES' && (pc == 'L2' || pc == 'L7') && (itemno !== '909184' && itemno !== '909181' && itemno !== '904601' && itemno !== '999020' && itemno !== '903184')) {
            perfpkgpartno = displayItemNo; // Use ItemDesc1 for descriptive display

            // CPQ MSRP Support: Use real MSRP if available
            var tubeHasRealMSRP = (boatoptions[i].MSRP !== undefined && boatoptions[i].MSRP !== null && Number(boatoptions[i].MSRP) > 0);
            if (tubeHasRealMSRP) {
                msrpcost = Number(boatoptions[i].MSRP);
            } else if (serialYear < 21) {
                msrpcost = Number(dealercost / msrpMargin);
            }
            else {
                msrpcost = Number((dealercost * msrpVolume) / msrpMargin);
            }
        }
        if (mct == 'PERFORMANCE PKG' && (pc == 'L2' || pc == 'L7')) {
            perfpkgpartno = displayItemNo; // Use ItemDesc1 for descriptive display
        }
    });

    var boatpkgmsrptotal = Number(getValue('DLR2', 'BOAT_MS')) + Number(getValue('DLR2', 'PRERIG_FULL_W_MARGIN_MSRP')) + Number(getValue('DLR2', 'ENG_FULL_W_MARGIN_MSRP'));
    setValue('DLR2', 'PKG_MSRP', boatpkgmsrptotal);

    var boatpkgsptotal = Number(getValue('DLR2', 'BOAT_SP')) + Number(getValue('DLR2', 'PRERIG_FULL_W_MARGIN_SALE')) + Number(getValue('DLR2', 'ENG_FULL_W_MARGIN_SALE'));
    setValue('DLR2', 'PKG_SALE', boatpkgsptotal);

    console.log("BOAT MSRP TOTAL: "+boatpkgmsrptotal);
    console.log("BOAT SP TOTAL: "+boatpkgsptotal);
};
