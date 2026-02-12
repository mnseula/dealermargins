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

    //quick loop thru to see if I'm supposed to have a boat package line in the table.
    //total it up as you go just in case.
    //if all 3 exist, hide Prerig and Boat line, Engine should show, but at incremental price. Sum them up as boat package.
    //sales reps never want to show the price of an engine on its own line without incremental pricing.
    //Change in plan, always add the boat, engine and prerig on a line... don't konw the default engine and prerig for boats older than 16.

    var additionalCharge = getValue('EXTRAS', 'ADD_CHARGE');
    if (additionalCharge === "" || additionalCharge === false || additionalCharge === true) {
        additionalCharge = 0;
    }
    var twinenginecost = 0;
    window.EngineDiscountAdditions = 0;
    window.hasEngineDiscount = false;
    window.hasEngineLowerUnit = false;
    window.EngineLowerUnitAdditions = 0;

    $.each(boatoptions, function (j) {
        var mct = boatoptions[j].MCTDesc;
        var mctType = boatoptions[j].ItemMasterMCT;
        var dealercost = boatoptions[j].ExtSalesAmount;
        var macoladesc = boatoptions[j].ItemDesc1;
        var prodCategory = boatoptions[j].ItemMasterProdCat;
        var itemNo = boatoptions[j].ItemNo;
        var boatModel = boatoptions[j].BoatModelNo;
        var qty = 1;
        var shownDealerCost = getValue('DLR2', 'BOAT_DC');

        if (mctType === 'DIS' || mctType === 'DIV') {
            EngineDiscountAdditions = Number(dealercost) + Number(EngineDiscountAdditions);
        }
        if (mctType === 'ENZ') {
            hasEngineDiscount = true;
        }
        console.log('hasEngineDiscount', hasEngineDiscount);

        if (mct === 'PONTOONS' || mct === 'Pontoon Boats OB') {
            boatpackageprice = boatpackageprice + Number(dealercost); //dealer cost has no f & p

            //PACKAGE DISCOUNTS WERE RECEIVED FROM MICHAEL BLANK
            //LOGIC IS BUILT USING SERIES AND LENGTH OF BOAT
            //LOGIC BUILT BY ZACH SPRINGMAN ON 1/17/2024

            //PACKAGE DISCOUNTS FOR SV SERIES
            if (series === "SV" && boatModel.match(/188.*/)) {
                boatpackageprice = boatpackageprice - 1650;
                console.log("18 FOOT SV BOAT DISCOUNT ADDED.");
            } else if (series === "SV" && boatModel.match(/20.*/)) {
                boatpackageprice = boatpackageprice - 1700;
                console.log("20 FOOT SV BOAT DISCOUNT ADDED.");
            } else if (series === "SV" && boatModel.match(/22.*/)) {
                boatpackageprice = boatpackageprice - 750;
                console.log("22 FOOT SV BOAT DISCOUNT ADDED.");
            }

            //PACKAGE DISCOUNTS FOR S SERIES
            if (series === "S" && boatModel.match(/20.*/)) {
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
            if (series === "S_23" && boatModel.match(/20.*/)) {
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
            if (series === "LT") {
                boatpackageprice = boatpackageprice - 750;
                console.log("LT PACKAGE DISCOUNT ADDED.")
            }

            //PACKAGE DISCOUNTS FOR LX SERIES
            if (series === "LX") {
                boatpackageprice = boatpackageprice - 750;
                console.log("LX PACKAGE DISCOUNT ADDED.")
            }

            console.log('boat package price (+Pontoon) is now ', boatpackageprice);
            boatsp = (Number(dealercost) / baseboatmargin) * vol_disc + Number(additionalCharge);
            setValue('DLR2', 'BOAT_DC', dealercost);
            setValue('DLR2', 'BOAT_DESC', macoladesc);
            //add f & p to the boat, and the boat package so the math will be right if the remove the engine (no pkg).
            console.log(freight);
            console.log(prep);
            console.log(additionalCharge);
            console.log(vol_disc);
            console.log('MSRP Margin: ', msrpMargin);

            saleboatpackageprice += ((dealercost * vol_disc) / baseboatmargin) + Number(freight) + Number(prep) + Number(additionalCharge);
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

            window.engineitemno = boatoptions[j].ItemNo;
            window.enginedesc = boatoptions[j].ItemDesc1;
            console.log('engine item no', engineitemno, 'boat product id', boatproductid);

            //sometimes a 16 boat has a 15 engine.  Get the engine from the 15 product.

            window.twoEngineLetters = engineitemno.substring(engineitemno.length - 2);

            if (twoEngineLetters == 'DE' || twoEngineLetters == 'DF' || twoEngineLetters == 'DR' || twoEngineLetters == 'DL' || twoEngineLetters == 'DI' || twoEngineLetters == 'DN' || twoEngineLetters == 'SG') {
                console.log('Has Engine Letter Designator');
            } else {
                window.twoEngineLetters = 'SD'; //removed letters in 2021
                window.twoEngineLetters = lasttwoletters;
            }


            console.log('Engine Letters Are', twoEngineLetters);

            var engproductidrec = $.grep(productids, function (y) {
                return (y.PRODUCT_NAME == 'MASTER' && y.SUFFIX == twoEngineLetters);
            });


            if (engproductidrec.length > 0) {
                window.engproductid = engproductidrec[0].PRODUCT_ID;
            }
            console.log('engprodid ', engproductid);

            window.defaultengineprice = getEngineInfo(engineitemno, engproductid);
            console.log('Default Engine Price', defaultengineprice);
            boatpackageprice = boatpackageprice + Number(defaultengineprice); // - Number(defaultengineprice);
            console.log('boat package price (+engine) is now ', boatpackageprice);

            engineonboatprice = dealercost;

            setValue('DLR2', 'ENG_FULL_W_MARGIN_SALE', Math.round(defaultengineprice / enginemargin) * vol_disc);

            if (serialYear < 20) {
                setValue('DLR2', 'ENG_FULL_W_MARGIN_MSRP', Math.round(defaultengineprice / msrpMargin));
            } else {
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

            saleboatpackageprice = saleboatpackageprice + defaultenginesp;// +enginesp;
            console.log('boat package SALE price (+engine) is now ', saleboatpackageprice);
            setValue('DLR2', 'ENGINE_INC', engineincrement);
        }
        //Without any kind of sorting to this boatoptions table pre rig is at least sometimes gone over BEFORE the engine... In these situation we have no way of figuring out default pre rigging
        if (mct === 'PRE-RIG') {
            hasprerig = '1';
            var prerigonboatprice = dealercost;

            if ((defaultprerigprice === undefined || defaultprerigprice === false)) {
                defaultprerigprice = getValue('DLR2', 'DEF_PRERIG_COST');
                if (defaultprerigprice == false) {
                    window.retryPrerig = 1;
                }
            }

            if ((defaultprerigprice === undefined || defaultprerigprice === false) & hasengine === '1') {
                window.defaultengineprice = getEngineInfo(engineitemno, engproductid)
            }
            ;window.prerigincrement = prerigonboatprice - defaultprerigprice;

            setValue('DLR2', 'PRERIG_FULL_W_MARGIN_SALE', Math.round(prerigonboatprice / optionmargin) * vol_disc);

            if (serialYear < 20) {
                setValue('DLR2', 'PRERIG_FULL_W_MARGIN_MSRP', Math.round(prerigonboatprice / msrpMargin));
            } else {
                setValue('DLR2', 'PRERIG_FULL_W_MARGIN_MSRP', Math.round(prerigonboatprice / msrpMargin) * vol_disc);
            }

            defaultprerigsp = (defaultprerigprice / optionmargin) * vol_disc;
            //boatpackageprice = boatpackageprice + Number(defaultprerigsp);
            defaultprerigprice = getValue('DLR2', 'DEF_PRERIG_COST');

            if (prodCategory != 'PL1' && prodCategory != 'PL2' && prodCategory != 'PL3' && prodCategory != 'PL4' && prodCategory != 'PL5' && prodCategory != 'PL6') {
                //TODO EXCLUDE CERTAIN PRERIGS FROM THE PACKAGE!
                boatpackageprice = boatpackageprice + Number(defaultprerigprice);
            }

            prerigsp = (Number(prerigincrement) / optionmargin) * vol_disc; //was prerigonboatcost

            if (prodCategory != 'PL1' && prodCategory != 'PL2' && prodCategory != 'PL3' && prodCategory != 'PL4' && prodCategory != 'PL5' && prodCategory != 'PL6') {
                saleboatpackageprice = saleboatpackageprice + defaultprerigsp;// - prerigsp;
            }
        }
    });


    //This is a manual correction for if the options order is wonky in the loop above hopefully the order has been fixed but keeping this code here just in case
    if (window.retryPrerig == 1 && window.hasengine == 1) {
        console.error('We need to retry pre rig if it now has an engine');
        var manualPreRig = $.grep(boatoptions, function (rec) {
            return rec.MCTDesc === 'PRE-RIG';
        });
        //Replicate the vars above
        var dealercost = manualPreRig.ExtSalesAmount;

        hasprerig = '1';
        var prerigonboatprice = dealercost;
        if ((defaultprerigprice === undefined || defaultprerigprice === false)) {
            defaultprerigprice = getValue('DLR2', 'DEF_PRERIG_COST');
            if (defaultprerigprice == false) {
                window.retryPrerig = 1;
            }
        }

        if ((defaultprerigprice === undefined || defaultprerigprice === false) & hasengine === '1') {
            window.defaultengineprice = getEngineInfo(engineitemno, engproductid)
        }
        console.debug('defaultprerigprice', defaultprerigprice);
        window.prerigincrement = prerigonboatprice - defaultprerigprice;

        defaultprerigsp = (defaultprerigprice / optionmargin) * vol_disc;
        defaultprerigprice = getValue('DLR2', 'DEF_PRERIG_COST');

        boatpackageprice = boatpackageprice + Number(defaultprerigprice);
        prerigsp = (Number(prerigincrement) / optionmargin) * vol_disc; //was prerigonboatcost
        saleboatpackageprice = saleboatpackageprice + defaultprerigsp;// - prerigsp;
    }
    //test to see if a boat package line should show first.

    if (hasengine == '0') { //if it doesn't have an engine, just set it to be removed
        removeengine = '1';
        setValue('DLR', 'HASENGINE', '0');
        setAnswer('RMV_ENG', 'YES');
        var defaultprerigprice = 0; //without this I was getting random undefined errors, forced it to be defined to start to avoid that.
    }


    if (hasengine === '1' && hasprerig === '1' && removeengine === '0') {
        var showpkgline = 1;
        setValue('DLR', 'HASENGINE', '1');
    } else {
        var showpkgline = '0';
    }
    console.log('hasengine', hasengine);


    boatpackageprice = Number(boatpackageprice);
    console.log('boat package price is now ', boatpackageprice);


    //start of MSRP for Packages
    console.log('pkgmsrp is ', pkgmsrp);

    if (pkgmsrp == 0) { //a third = sign breaks this
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
        //Create boat package line
        boattable.push({
            'ItemDesc1': 'BOAT PACKAGE',
            'ItemNo': 'BOAT, ENGINE, PRE-RIG',
            'Qty': '',
            'MCT': 'BOATPKG',
            'PC': '',
            'DealerCost': Math.round(boatpackageprice),
            'SalePrice': Math.round(saleboatpackageprice),
            'MSRP': Math.round(msrpboatpackageprice),
            'Increment': ''
        });
    }

    //msrp for options calcs

    var discountsIncluded = 0;
    //loop to create the options table
    $.each(boatoptions, function (i) {
        var itemno = boatoptions[i].ItemNo;
        var mct = boatoptions[i].ItemMasterMCT;
        var mctType = boatoptions[i].ItemMasterMCT;
        var prodCategory = boatoptions[i].ItemMasterProdCat;
        var qty = boatoptions[i].QuantitySold;
        if (mct === 'BOA') {
            var itemdesc = boatoptions[i].ItemDesc1.toUpperCase();
        } else {
            //get the desc from the OMM instead of the Boat Options (macola titles)
            if (optionsMatrix !== undefined && optionsMatrix.length > 0) {
                itemOmmLine = $.grep(optionsMatrix, function (i) {
                    return i.PART === itemno;
                });

                //account for when a part is on the order, and not in the omm.
                if (itemOmmLine.length > 0 && itemOmmLine[0].OPT_NAME !== "") {
                    itemdesc = itemOmmLine[0].OPT_NAME.toUpperCase();
                } else { //sometimes it is in the omm but no long in the omm on this boat.
                    itemdescRec = sStatement('SLT_ONE_REC_OMM_2016', ([itemno]));
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
        var itemNo = boatoptions[i].ItemNo;
        var saleprice = 0;

        if (mct == 'PONTOONS') {
            //add F & P to the Boat Line in case they remove the engine (no pkg)

            msrpprice = Number((dealercost) * vol_disc) / msrpMargin + Number(additionalCharge); //fixed freight and prep
            console.log("MSRP TEST ZACH: ", msrpprice);
            saleprice = Number((dealercost * vol_disc) / baseboatmargin) + Number(freight) + Number(prep) + Number(additionalCharge);

            if (series === 'SV') {
                saleprice = Number((dealercost * msrpVolume * msrpLoyalty) / baseboatmargin) + Number(freight) + Number(prep) + Number(additionalCharge);
                msrpprice = saleprice;
            }
            setValue('DLR2', 'BOAT_SP', Math.round(saleprice));
            setValue('DLR2', 'BOAT_MS', Math.round(msrpprice));
        } else if (mct !== 'ENGINES' && mct !== 'ENGINES I/O' && mct !== 'PONTOONS') {
            if (mctType === 'ENZ') {
                dealercost = Number(dealercost) + Number(EngineDiscountAdditions);
            }

            var msrpprice = Number((dealercost * msrpVolume) / msrpMargin);

            if (series == 'SV') {
                msrpprice = Number(msrpprice * msrpLoyalty);
                saleprice = msrpprice;

            } else {
                if (dealercost > 0) { //don't apply margins to negative costs unless series is sv
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
                msrpprice = Number((EngineDiscountAdditions * msrpVolume) / msrpMargin);

                if (series == 'SV') {
                    msrprice = msrpprice * msrpLoyalty;
                }

                boattable.push({
                    'ItemDesc1': 'Limited time value series discount',
                    'ItemNo': itemno,
                    'Qty': qty,
                    'MCT': mct,
                    'PC': pc,
                    'DealerCost': EngineDiscountAdditions,
                    'SalePrice': Math.round(saleprice).toFixed(2),
                    'MSRP': Math.round(msrpprice).toFixed(2)
                });
            } else if (mctType === 'DIS' || mctType === 'DIV') {
            } else {
                boattable.push({
                    'ItemDesc1': itemdesc,
                    'ItemNo': itemno,
                    'Qty': qty,
                    'MCT': mct,
                    'PC': pc,
                    'DealerCost': dealercost,
                    'SalePrice': Math.round(saleprice).toFixed(2),
                    'MSRP': Math.round(msrpprice).toFixed(2)
                });
            }
        }

        if (mct == 'ENGINES' || mct == 'ENGINES I/O') { //if it is a package w a diff engine, only show the engine increment
            engineinvoiceno = boatoptions[i].InvoiceNo;
            if (showpkgline == '1') {
                if (window.hasEngineLowerUnit) {
                    console.error('Has lower unit like 998');
                    dealercost = Number(dealercost) + Number(window.EngineLowerUnitAdditions);
                }
                dealercost = Number(dealercost - Number(defaultengineprice));
                boatpackageprice = Number(boatpackageprice) - Number(dealercost);
                //msrp calcs

                msrpboatpackageprice = Number(msrpboatpackageprice) - Math.round(Number(dealercost * msrpVolume) / msrpMargin);

                if (series === 'SV') {
                    msrpboatpackageprice = msrpboatpackageprice;
                }

                if (dealercost == 0) {
                    saleprice = 0;
                } else {
                    saleprice = Math.round(Number(dealercost / enginemargin) * vol_disc);
                }

                if (series === 'SV') {
                    msrp = Math.round(Number((dealercost * msrpVolume * msrpLoyalty) / msrpMargin)).toFixed(2)
                    saleprice = msrp;
                } else {
                    msrp = Math.round(Number((dealercost * msrpVolume) / msrpMargin)).toFixed(2)
                }

                boattable.push({
                    'ItemDesc1': itemdesc,
                    'ItemNo': itemno,
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

        if (mct == 'PRE-RIG') { //if it is a package w a diff prerig, only show the prerig increment
            if (showpkgline == '1') {
                //&& (prodCategory != 'PL1' && prodCategory != 'PL2' && prodCategory != 'PL3' && prodCategory != 'PL4' && prodCategory != 'PL5' && prodCategory != 'PL6')
                defaultprerigprice = getValue('DLR2', 'DEF_PRERIG_COST');
                if (prodCategory != 'PL1' && prodCategory != 'PL2' && prodCategory != 'PL3' && prodCategory != 'PL4' && prodCategory != 'PL5' && prodCategory != 'PL6') {
                } else {
                    defaultprerigprice = Number(0);
                }
                dealercost = Number(dealercost - Number(defaultprerigprice));

                //msrp calcs

                if (dealercost == 0) {
                    saleprice = 0;
                } else {
                    saleprice = (Number(dealercost / optionmargin) * vol_disc);
                }
                if (prodCategory != 'PL1' && prodCategory != 'PL2' && prodCategory != 'PL3' && prodCategory != 'PL4' && prodCategory != 'PL5' && prodCategory != 'PL6') {
                    boatpackageprice = Number(boatpackageprice) - Number(dealercost);
                    msrpboatpackageprice = Number(msrpboatpackageprice) - (Number(dealercost) / msrpMargin);
                    setValue('DLR2', 'PRERIG_INC', dealercost);
                }

                if (series === 'SV') {
                    msrp = Math.round(Number((dealercost * msrpVolume * msrpLoyalty) / msrpMargin)).toFixed(2)
                } else {
                    msrp = Math.round(Number((dealercost * msrpVolume) / msrpMargin)).toFixed(2)
                }

                boattable.push({
                    'ItemDesc1': itemdesc,
                    'ItemNo': itemno,
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

        if (mct == 'TUBE UPGRADES' && (pc == 'L2' || pc == 'L7') && (boatoptions[i].ItemNo !== '909184' && boatoptions[i].ItemNo !== '909181' && boatoptions[i].ItemNo !== '904601' && boatoptions[i].ItemNo !== '999020' && boatoptions[i].ItemNo !== '903184')) { //changed from & to || 10-18-16
            perfpkgpartno = boatoptions[i].ItemNo;
            if (serialYear < 21) {
                msrpcost = Number(dealercost / msrpMargin);
            } else {
                msrpcost = Number((dealercost * msrpVolume) / msrpMargin);
            }
        }
        if (mct == 'PERFORMANCE PKG' && (pc == 'L2' || pc == 'L7')) { //changed from & to || 10-18-16
            perfpkgpartno = boatoptions[i].ItemNo;
            console.log("Perf PKG found in Calculate 2021+");
        }
    });

    //set the pgk totals on the hidden tab
    var boatpkgmsrptotal = Number(getValue('DLR2', 'BOAT_MS')) + Number(getValue('DLR2', 'PRERIG_FULL_W_MARGIN_MSRP')) + Number(getValue('DLR2', 'ENG_FULL_W_MARGIN_MSRP'));
    setValue('DLR2', 'PKG_MSRP', boatpkgmsrptotal);

    var boatpkgsptotal = Number(getValue('DLR2', 'BOAT_SP')) + Number(getValue('DLR2', 'PRERIG_FULL_W_MARGIN_SALE')) + Number(getValue('DLR2', 'ENG_FULL_W_MARGIN_SALE'));
    setValue('DLR2', 'PKG_SALE', boatpkgsptotal);

    console.log("BOAT MSRP TOTAL: " + boatpkgmsrptotal);
    console.log("BOAT SP TOTAL: " + boatpkgsptotal);
};
