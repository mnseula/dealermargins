window.Calculate = window.Calculate || function () {
    console.log('calculate');

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
    if (additionalCharge === "" || additionalCharge === false || additionalCharge === true) { additionalCharge = 0; }
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
        var qty = 1;

        if (mctType === 'DIS' || mctType === 'DIV') { EngineDiscountAdditions = Number(dealercost) + Number(EngineDiscountAdditions); }
        if (mctType === 'ENZ') { hasEngineDiscount = true; }
        console.log('hasEngineDiscount', hasEngineDiscount);

        if (mct === 'PONTOONS') {
            boatpackageprice = boatpackageprice + Number(dealercost); //dealer cost has no f & p
            //console.log('boat package price (+Pontoon) is now ', boatpackageprice);
            boatsp = (Number(dealercost) / baseboatmargin) * vol_disc + Number(additionalCharge);
            setValue('DLR2', 'BOAT_DC', dealercost);
            setValue('DLR2', 'BOAT_DESC', macoladesc);
            //add f & p to the boat, and the boat package so the math will be right if the remove the engine (no pkg).
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

            window.engineitemno = boatoptions[j].ItemNo;
            window.enginedesc = boatoptions[j].ItemDesc1;
            console.log('engine item no', engineitemno, 'boat product id', boatproductid);

            //sometimes a 16 boat has a 15 engine.  Get the engine from the 15 product.

            window.twoEngineLetters = engineitemno.substring(engineitemno.length - 2);

            console.log('Engine Letters Are', twoEngineLetters);
            var engproductidrec = $.grep(productids, function (y) { return (y.PRODUCT_NAME == 'MASTER' && y.SUFFIX == twoEngineLetters); });

            if (engproductidrec.length > 0) { window.engproductid = engproductidrec[0].PRODUCT_ID; }
            console.log('engprodid ', engproductid);

            window.defaultengineprice = getEngineInfo(engineitemno, engproductid);
            console.log('Default Engine Price', defaultengineprice);
            boatpackageprice = boatpackageprice + Number(defaultengineprice); // - Number(defaultengineprice);
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
                if (defaultprerigprice == false) { window.retryPrerig = 1; }
            }

            if ((defaultprerigprice === undefined || defaultprerigprice === false) & hasengine === '1') { window.defaultengineprice = getEngineInfo(engineitemno, engproductid) };
            window.prerigincrement = prerigonboatprice - defaultprerigprice;

            setValue('DLR2', 'PRERIG_FULL_W_MARGIN_SALE', Math.round(prerigonboatprice / optionmargin) * vol_disc);

            if (serialYear < 20) {
                setValue('DLR2', 'PRERIG_FULL_W_MARGIN_MSRP', Math.round(prerigonboatprice / msrpMargin));
            }
            else {
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
        var manualPreRig = $.grep(boatoptions, function (rec) { return rec.MCTDesc === 'PRE-RIG'; });
        //Replicate the vars above
        var dealercost = manualPreRig.ExtSalesAmount;

        hasprerig = '1';
        var prerigonboatprice = dealercost;
        if ((defaultprerigprice === undefined || defaultprerigprice === false)) {
            defaultprerigprice = getValue('DLR2', 'DEF_PRERIG_COST');
            if (defaultprerigprice == false) { window.retryPrerig = 1; }
        }

        if ((defaultprerigprice === undefined || defaultprerigprice === false) & hasengine === '1') { window.defaultengineprice = getEngineInfo(engineitemno, engproductid) };
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
    } else { var showpkgline = '0'; }
    console.log('hasengine', hasengine);

    boatpackageprice = Number(boatpackageprice);
    console.log('boat package price is now ', boatpackageprice);


    //start of MSRP for Packages
    console.log('pkgmsrp is ', pkgmsrp);

    if (pkgmsrp > 0) { //won't happen in 2021
        saleboatpackageprice = Number(pkgmsrp) + Number(additionalCharge);
        msrpboatpackageprice = Number(pkgmsrp) + Number(additionalCharge);
        console.log('saleboatpackageprice ', saleboatpackageprice);
    }

    else if (pkgmsrp == 0) {

        if (serialYear < 21) {
            msrpboatpackageprice = Number((boatpackageprice / msrpMargin) + additionalCharge);
        } else {
            msrpboatpackageprice = Number(((boatpackageprice * msrpVolume) / msrpMargin) + additionalCharge);
            console.log('Keri 186');
        }
        if (series === 'SV' && serialYear >= 21) {
            msrpboatpackageprice = Number(((boatpackageprice * msrpVolume * msrpLoyalty) / msrpMargin) + additionalCharge);
            console.log(Math.round(msrpboatpackageprice));
            salesaleboatpackageprice = Math.round(msrpboatpackageprice);
        }

    }
    if (hasengine === '1') {
        //Create boat package line
        boattable.push({
            'ItemDesc1': 'BOAT PACKAGE', 'ItemNo': 'BOAT, ENGINE, PRE-RIG', 'Qty': '', 'MCT': 'BOATPKG', 'PC': '',
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
                itemOmmLine = $.grep(optionsMatrix, function (i) { return i.PART === itemno; });

                //account for when a part is on the order, and not in the omm.
                if (itemOmmLine.length > 0 && itemOmmLine[0].OPT_NAME !== "") {
                    itemdesc = itemOmmLine[0].OPT_NAME.toUpperCase();
                } else { //sometimes it is in the omm but no long in the omm on this boat.
                    itemdescRec = sStatement('SLT_ONE_REC_OMM_2016', ([itemno]));
                    if (itemdescRec.length > 0 && itemdescRec[0].OPT_NAME != "") { itemdesc = itemdescRec[0].OPT_NAME.toUpperCase(); }
                    else { itemdesc = boatoptions[i].ItemDesc1.toUpperCase(); }
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
            //add F & P to the Boat Line in case they remove the engine (no pkg)
            if (pkgmsrp === '0') {
                if (serialYear < 21) {
                    msrpprice = ((Number(dealercost / msrpMargin)) + Number(additionalCharge)); //fixed freight and prep
                } else {
                    msrpprice = Number((dealercost * msrpVolume) / msrpMargin) + Number(additionalCharge); //fixed freight and prep
                }
            } else {
                msrpprice = Number(pkgmsrp) + Number(additionalCharge); //fixed freight and prep
            }

            saleprice = Number((dealercost * vol_disc) / baseboatmargin) + Number(freight) + Number(prep) + Number(additionalCharge);
            setValue('DLR2', 'BOAT_SP', Math.round(saleprice));
            setValue('DLR2', 'BOAT_MS', Math.round(msrpprice));
        }

        else if (mct !== 'ENGINES' && mct !== 'ENGINES I/O' && mct !== 'PONTOONS') {
            if (mctType === 'ENZ') {
                dealercost = Number(dealercost) + Number(EngineDiscountAdditions);
            }
                var msrpprice = Number(dealercost / msrpMargin);
                saleprice = (Number(dealercost / optionmargin) * vol_disc);


            if(series == 'SV'){
                saleprice = msrpprice;
            }
        }

        if (mct !== 'ENGINES' && mct !== 'ENGINES I/O' && mct != 'Lower Unit Eng' && mct != 'PRE-RIG') {
            if ((mctType === 'DIS' || mctType === 'DIV') && !hasEngineDiscount && discountsIncluded === 0) {
                discountsIncluded = 1;
                saleprice = Number((EngineDiscountAdditions * vol_disc) / baseboatmargin);

                if (serialYear < 21) {
                    msrpprice = Number(EngineDiscountAdditions / msrpMargin);
                } else {
                    msrpprice = Number((EngineDiscountAdditions * msrpVolume) / msrpMargin);
                }

                if (series == 'SV' && serialYear > 20) {
                    msrprice = msrpprice * msrpLoyalty;
                }

                boattable.push({
                    'ItemDesc1': 'Limited time value series discount',
                    'ItemNo': itemno, 'Qty': qty, 'MCT': mct, 'PC': pc,
                    'DealerCost': EngineDiscountAdditions,
                    'SalePrice': Math.round(saleprice).toFixed(2),
                    'MSRP': Math.round(msrpprice).toFixed(2)
                });
            }
            else if (mctType === 'DIS' || mctType === 'DIV') {
            } else {
                boattable.push({
                    'ItemDesc1': itemdesc, 'ItemNo': itemno, 'Qty': qty, 'MCT': mct, 'PC': pc, 'DealerCost': dealercost,
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
                if (serialYear < 21) {
                    msrpcost = Math.round(Number(dealercost / msrpMargin));
                } else {
                    msrpcost = Math.round(Number(dealercost * msrpVolume) / msrpMargin);
                }
                msrpcost = Number(msrpcost - Number(defaultengineprice));

                if (serialYear < 21) {
                    msrpboatpackageprice = Number(msrpboatpackageprice) - Math.round(Number(dealercost) / msrpMargin);
                }
                else {
                    msrpboatpackageprice = Number(msrpboatpackageprice) - Math.round(Number(dealercost * msrpVolume) / msrpMargin);
                }
                if (dealercost == 0) { saleprice = 0; }
                else { saleprice = Math.round(Number(dealercost / enginemargin) * vol_disc); }

                boattable.push({
                    'ItemDesc1': itemdesc, 'ItemNo': itemno, 'Qty': qty, 'MCT': mct, 'PC': pc, 'DealerCost': dealercost, 'SalePrice': saleprice.toFixed(2),
                    'MSRP': Math.round(Number(dealercost / msrpMargin)).toFixed(2),
                    'Increment': '1'
                });
            }
        }

        if (mct == 'PRE-RIG') { //if it is a package w a diff prerig, only show the prerig increment
            if (showpkgline == '1') {
                //&& (prodCategory != 'PL1' && prodCategory != 'PL2' && prodCategory != 'PL3' && prodCategory != 'PL4' && prodCategory != 'PL5' && prodCategory != 'PL6')
                defaultprerigprice = getValue('DLR2', 'DEF_PRERIG_COST');
                if (prodCategory != 'PL1' && prodCategory != 'PL2' && prodCategory != 'PL3' && prodCategory != 'PL4' && prodCategory != 'PL5' && prodCategory != 'PL6') { } else {
                    defaultprerigprice = Number(0);
                }
                dealercost = Number(dealercost - Number(defaultprerigprice));

                //msrp calcs
                if (serialYear < 21) {
                    msrpcost = Number(dealercost / msrpMargin);
                }
                else {
                    msrpcost = Number((dealercost * msrpVolume) / msrpMargin);
                }

                if (dealercost == 0) { saleprice = 0; }
                else { saleprice = (Number(dealercost / optionmargin) * vol_disc); }
                if (prodCategory != 'PL1' && prodCategory != 'PL2' && prodCategory != 'PL3' && prodCategory != 'PL4' && prodCategory != 'PL5' && prodCategory != 'PL6') {
                    boatpackageprice = Number(boatpackageprice) - Number(dealercost);
                    msrpboatpackageprice = Number(msrpboatpackageprice) - (Number(dealercost) / msrpMargin);
                    setValue('DLR2', 'PRERIG_INC', dealercost);
                }
                boattable.push({
                    'ItemDesc1': itemdesc, 'ItemNo': itemno, 'Qty': qty, 'MCT': mct, 'PC': pc, 'DealerCost': dealercost, 'SalePrice': Math.round(saleprice),
                    'MSRP': Math.round(Number(dealercost * msrpVolume) / msrpMargin).toFixed(2),
                    'Increment': '1'
                });
            }
        }

        if (mct == 'TUBE UPGRADES' && (pc == 'L2' || pc == 'L7') && (boatoptions[i].ItemNo !== '909184' && boatoptions[i].ItemNo !== '909181' && boatoptions[i].ItemNo !== '904601' && boatoptions[i].ItemNo !== '999020' && boatoptions[i].ItemNo !== '903184')) { //changed from & to || 10-18-16
            perfpkgpartno = boatoptions[i].ItemNo;
            if (serialYear < 21) {
                msrpcost = Number(dealercost / msrpMargin);
            }
            else {
                msrpcost = Number((dealercost * msrpVolume) / msrpMargin);
            }
        }
        if (mct == 'PERFORMANCE PKG' && (pc == 'L2' || pc == 'L7')) { //changed from & to || 10-18-16
            perfpkgpartno = boatoptions[i].ItemNo;
            if (serialYear < 21) {
                msrpcost = Number(dealercost / msrpMargin);
            } else {
                msrpcost = Number((dealercost * msrpVolume) / msrpMargin);
            }
        }
        // console.table(boattable);
    });

    //set the pgk totals on the hidden tab
    var boatpkgmsrptotal = Number(getValue('DLR2', 'BOAT_MS')) + Number(getValue('DLR2', 'PRERIG_FULL_W_MARGIN_MSRP')) + Number(getValue('DLR2', 'ENG_FULL_W_MARGIN_MSRP'));
    setValue('DLR2', 'PKG_MSRP', boatpkgmsrptotal);

    var boatpkgsptotal = Number(getValue('DLR2', 'BOAT_SP')) + Number(getValue('DLR2', 'PRERIG_FULL_W_MARGIN_SALE')) + Number(getValue('DLR2', 'ENG_FULL_W_MARGIN_SALE'));
    setValue('DLR2', 'PKG_SALE', boatpkgsptotal);
};
