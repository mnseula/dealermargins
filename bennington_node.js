functions = {
    CHECK_PRINT_SHOP: function () {
        // console.log('RUN CHECK_PRINT_SHOP', new Date());
        var d = new Date();
        eos.ben.addByListName('Scheduler_Log', [d.getDate() + '/' + (d.getMonth() + 1) + '/' + d.getFullYear() + ' @ ' + d.getHours() + ':' + d.getMinutes() + ':' + d.getSeconds(), 'CHECK_PRINT_SHOP']);
        require('ben/print_shop_check')().then(function (result) {
            console.log('RUN CHECK_PRINT_SHOP', result, new Date());
        });
    }
,
    VALIDATE: function () {
        console.log('RUN VALIDATE', new Date());
        var d = new Date();
        eos.ben.addByListName('Scheduler_Log', [d.getDate() + '/' + (d.getMonth() + 1) + '/' + d.getFullYear() + ' @ ' + d.getHours() + ':' + d.getMinutes() + ':' + d.getSeconds(), 'VALIDATE'])

        require('ben/sweep')('VALIDATE').done(function (result) {
            console.log(result);
        });
    }
,
    BOAT_LOG: function () {
        console.log('RUN BOAT_LOG', new Date());
        var d = new Date();
        eos.ben.addByListName('Scheduler_Log', [d.getDate() + '/' + (d.getMonth() + 1) + '/' + d.getFullYear() + ' @ ' + d.getHours() + ':' + d.getMinutes() + ':' + d.getSeconds(), 'BOAT_LOG'])
        require('ben/sweep')('BOAT_LOG').done(function (result) {
            console.log(result);
        });
    }
,
    REPORT: function () {
        var d = new Date();
        eos.ben.addByListName('Scheduler_Log', [d.getDate() + '/' + (d.getMonth() + 1) + '/' + d.getFullYear() + ' @ ' + d.getHours() + ':' + d.getMinutes() + ':' + d.getSeconds(), 'REPORT'])
        console.log('RUN REPORT', new Date());
        require('ben/sweep')('REPORT').done(function (result) {
            console.log(result);
        });
    }
,
    UPDATE_PRICING: function () {
    }
,
    TEST: function () {
        console.log('TEST from library', Date());
    }
,
    RUN_SERIAL_MASTER: function () {
        var d = new Date();
        eos.ben.addByListName('Scheduler_Log', [d.getDate() + '/' + (d.getMonth() + 1) + '/' + d.getFullYear() + ' @ ' + d.getHours() + ':' + d.getMinutes() + ':' + d.getSeconds(), 'RUN_SERIAL_MASTER'])
        console.log('RUN_SERIAL_MASTER', Date());
        //Update Serial Number Master
        //var serialNumberMaster = loadByListName('PW_SerialNumberMaster');
        //var serialNumberMaster = sStatement('ALL_SER_NO_MST');//, [('12')]);
        //console.log('Serial Number Master',serialNumberMaster);
        eos.sStatement('SER_MAST_UPDT').then(function (serialMasterUpdate) {
            console.log('Serial Master Update', serialMasterUpdate.length);
            var prodNo;
            var newrecordswritten = 0;
            if (serialMasterUpdate.length === 0) {
                eos.sendEmail('max.zaicev@benningtonmarine.com', 'Serial # Master has 0 Records.');
                // eos.sendEmail('akuzmin@verenia.com', 'Serial Master finished at ' + d + '. Total is ' + serialMasterUpdate.length);
                return;
            }

            var proccess = function (i) {

                if (serialMasterUpdate.length == i) {
                    var d = new Date();
                    console.log('RUN_SERIAL_MASTER FINISHED', d);
                    // eos.sendEmail('akuzmin@verenia.com', 'Serial Master finished at ' + d + '. Total is ' + serialMasterUpdate.length);
                    return;
                }

                // console.log('Proccess serial number: ', (i + 1) + '/' + serialMasterUpdate.length);

                var sn = serialMasterUpdate[i].Boat_SerialNo;
                var yearCheck = Number(sn.substring(sn.length - 2));
                var selectStatement = 'SEL_ONE_SER_NO_MST';
                var insertStatement = 'INS_PW_SERIAL_MASTER';
                var updateStatement = 'UPD_PW_SERIAL_MASTER';
                var updateAll = 'UPD_PW_MASTER_ALL';
                if (yearCheck < 7 || yearCheck > 97) {
                    selectStatement += '_OLD';
                    insertStatement += '_OLD';
                    updateStatement += '_OLD';
                    updateAll += '_OLD';
                }
                // console.log('serial number is ', sn);
                var active = serialMasterUpdate[i].Active
                var origOrdType = serialMasterUpdate[i].OrigOrderType;
                //console.log(serialMasterUpdate);
                eos.sStatement(selectStatement, [(sn)]).then(function (serialNumberMasterRecord) {
                    //console.log(serialNumberMasterRecord.length);
                    // console.log('SNMR = ', JSON.stringify(serialNumberMasterRecord));
                    if (serialNumberMasterRecord.length === 0) {
                        //doesn't exist, just write the record
                        // console.log('does not exist');
                        newrecordswritten = newrecordswritten + 1;
                        var tempSNMY = serialMasterUpdate[i].SN_MY;
                        var tempBoatSerialNo = serialMasterUpdate[i].Boat_SerialNo;
                        var tempBoatItemNo = serialMasterUpdate[i].BoatItemNo;
                        var tempSeries = serialMasterUpdate[i].Series;
                        var tempBoatDesc1 = serialMasterUpdate[i].BoatDesc1;
                        var tempBoatDesc2 = serialMasterUpdate[i].BoatDesc2;
                        var tempSerialModelYear = serialMasterUpdate[i].SerialModelYear;
                        var tempERPOrderNo = serialMasterUpdate[i].ERP_OrderNo;
                        var tempProdNo = serialMasterUpdate[i].ProdNo;
                        var tempOrigOrdType = serialMasterUpdate[i].OrigOrderType;
                        var tempInvoiceNo = serialMasterUpdate[i].InvoiceNo;
                        var tempApplyToNo = serialMasterUpdate[i].ApplyToNo;
                        var tempInvoiceDate = serialMasterUpdate[i].InvoiceDateYYYYMMDD;
                        var tempDealerNumber = serialMasterUpdate[i].DealerNumber;
                        var tempDealerName = serialMasterUpdate[i].DealerName;
                        var tempDealerCity = serialMasterUpdate[i].DealerCity;
                        var tempDealerState = serialMasterUpdate[i].DealerState;
                        var tempDealerZip = serialMasterUpdate[i].DealerZip;
                        var tempDealerCountry = serialMasterUpdate[i].DealerCountry;
                        var tempParentRepName = serialMasterUpdate[i].ParentRepName;
                        var tempColorPackage = serialMasterUpdate[i].ColorPackage;
                        var tempPanelColor = serialMasterUpdate[i].PanelColor;
                        var tempAccentPanel = serialMasterUpdate[i].AccentPanel;
                        var tempTrimAccent = serialMasterUpdate[i].TrimAccent;
                        var tempBaseVinyl = serialMasterUpdate[i].BaseVinyl;
                        var tempWebOrderNo = serialMasterUpdate[i].WebOrderNo;
                        var tempPresold = serialMasterUpdate[i].Presold;
                        var tempActive = serialMasterUpdate[i].Active;
                        var tempSNID = serialMasterUpdate[i].SN_ID;
                        var tempQuantity = serialMasterUpdate[i].Quantity;
                        //boat serial has to be parameter 1
                        var tempData = ([tempBoatSerialNo, tempSNMY, tempBoatItemNo, tempSeries, tempBoatDesc1, tempBoatDesc2, tempSerialModelYear,
                            tempERPOrderNo, tempProdNo, tempOrigOrdType, tempInvoiceNo, tempApplyToNo, tempInvoiceDate,
                            tempDealerNumber, tempDealerName, tempDealerCity, tempDealerState, tempDealerZip, tempDealerCountry, tempParentRepName,
                            tempColorPackage, tempPanelColor, tempAccentPanel, tempTrimAccent, tempBaseVinyl, tempWebOrderNo, tempPresold,
                            tempActive, tempSNID, tempQuantity]);
                        // console.log('tempdata', tempData);
                        eos.sStatement(insertStatement, tempData).then(function () {
                            //add new lines to serial number registration status
                            // console.log('add new line to serial no registration status table');
                            var registered = '0';
                            var fieldinventory = '1';
                            var unknown = '0';
                            var snd = 0;
                            if (tempPresold === 'Y') {
                                snd = '1';
                            }
                            var snrsData = ([tempSNMY, tempBoatSerialNo, registered, fieldinventory, unknown, snd]);
                            eos.sStatement('INSERT_SN_REG_STATUS', snrsData).then(function () {
                                // console.log('boat reg status update');
                                // next record
                                proccess(i + 1);
                            });
                        });
                    } else { //exists
                        // console.log('does exist');
                        var masterSNMY = serialNumberMasterRecord[0].SN_MY;
                        var masterBoatSerialNo = serialNumberMasterRecord[0].Boat_SerialNo;
                        var masterBoatItemNo = serialNumberMasterRecord[0].BoatItemNo;
                        var masterSeries = serialNumberMasterRecord[0].Series;
                        var masterBoatDesc1 = serialNumberMasterRecord[0].BoatDesc1;
                        var masterBoatDesc2 = serialNumberMasterRecord[0].BoatDesc2;
                        var masterSerialModelYear = serialNumberMasterRecord[0].SerialModelYear;
                        var masterERPOrderNo = serialNumberMasterRecord[0].ERP_OrderNo;
                        var masterProdNo = serialNumberMasterRecord[0].ProdNo;
                        var masterOrigOrdType = serialNumberMasterRecord[0].OrigOrderType;
                        var masterInvoiceNo = serialNumberMasterRecord[0].InvoiceNo;
                        var masterApplyToNo = serialNumberMasterRecord[0].ApplyToNo;
                        var masterInvoiceDate = serialNumberMasterRecord[0].InvoiceDateYYYYMMDD;
                        var masterDealerNumber = serialNumberMasterRecord[0].DealerNumber;
                        var masterDealerName = serialNumberMasterRecord[0].DealerName;
                        var masterDealerCity = serialNumberMasterRecord[0].DealerCity;
                        var masterDealerState = serialNumberMasterRecord[0].DealerState;
                        var masterDealerZip = serialNumberMasterRecord[0].DealerZip;
                        var masterDealerCountry = serialNumberMasterRecord[0].DealerCountry;
                        var masterParentRepName = serialNumberMasterRecord[0].ParentRepName;
                        var masterColorPackage = serialNumberMasterRecord[0].ColorPackage;
                        var masterPanelColor = serialNumberMasterRecord[0].PanelColor;
                        var masterAccentPanel = serialNumberMasterRecord[0].AccentPanel;
                        var masterTrimAccent = serialNumberMasterRecord[0].TrimAccent;
                        var masterBaseVinyl = serialNumberMasterRecord[0].BaseVinyl;
                        var masterWebOrderNo = serialNumberMasterRecord[0].WebOrderNo;
                        var masterPresold = serialNumberMasterRecord[0].Presold;
                        var masterActive = serialNumberMasterRecord[0].Active;
                        var masterSNID = serialNumberMasterRecord[0].SN_ID;
                        var masterQuantity = serialNumberMasterRecord[0].Quantity;
                        var masterData = ([masterSNMY, masterBoatSerialNo, masterBoatItemNo, masterSeries, masterBoatDesc1, masterBoatDesc2,
                            masterSerialModelYear,
                            masterERPOrderNo, masterProdNo, masterOrigOrdType, masterInvoiceNo, masterApplyToNo, masterInvoiceDate,
                            masterDealerNumber, masterDealerName, masterDealerCity, masterDealerState, masterDealerZip, masterDealerCountry, masterParentRepName,
                            masterColorPackage, masterPanelColor, masterAccentPanel, masterTrimAccent, masterBaseVinyl, masterWebOrderNo, masterPresold,
                            masterActive, masterSNID, masterQuantity]);
                        //console.log(masterData);
                        tempSNMY = serialMasterUpdate[i].SN_MY;
                        tempBoatSerialNo = serialMasterUpdate[i].Boat_SerialNo;
                        tempBoatItemNo = serialMasterUpdate[i].BoatItemNo;
                        tempSeries = serialMasterUpdate[i].Series;
                        tempBoatDesc1 = serialMasterUpdate[i].BoatDesc1;
                        tempBoatDesc2 = serialMasterUpdate[i].BoatDesc2;
                        tempSerialModelYear = serialMasterUpdate[i].SerialModelYear;
                        tempERPOrderNo = serialMasterUpdate[i].ERP_OrderNo;
                        tempProdNo = masterProdNo; //get the prod no before you update the record to keep it.
                        tempOrigOrdType = serialMasterUpdate[i].OrigOrderType;
                        tempInvoiceNo = serialMasterUpdate[i].InvoiceNo;
                        tempApplyToNo = serialMasterUpdate[i].ApplyToNo;
                        tempInvoiceDate = serialMasterUpdate[i].InvoiceDateYYYYMMDD;
                        tempDealerNumber = serialMasterUpdate[i].DealerNumber;
                        tempDealerName = serialMasterUpdate[i].DealerName;
                        tempDealerCity = serialMasterUpdate[i].DealerCity;
                        tempDealerState = serialMasterUpdate[i].DealerState;
                        tempDealerZip = serialMasterUpdate[i].DealerZip;
                        tempDealerCountry = serialMasterUpdate[i].DealerCountry;
                        tempParentRepName = serialMasterUpdate[i].ParentRepName;
                        tempColorPackage = serialMasterUpdate[i].ColorPackage;
                        tempPanelColor = serialMasterUpdate[i].PanelColor;
                        tempAccentPanel = serialMasterUpdate[i].AccentPanel;
                        tempTrimAccent = serialMasterUpdate[i].TrimAccent;
                        tempBaseVinyl = serialMasterUpdate[i].BaseVinyl;
                        tempWebOrderNo = serialMasterUpdate[i].WebOrderNo;
                        tempPresold = serialMasterUpdate[i].Presold;
                        tempActive = serialMasterUpdate[i].Active;
                        tempSNID = serialMasterUpdate[i].SN_ID;
                        tempQuantity = serialMasterUpdate[i].Quantity;
                        tempData = ([tempBoatSerialNo, tempSNMY, tempBoatItemNo, tempSeries, tempBoatDesc1, tempBoatDesc2, tempSerialModelYear,
                            tempERPOrderNo, tempProdNo, tempOrigOrdType, tempInvoiceNo, tempApplyToNo, tempInvoiceDate,
                            tempDealerNumber, tempDealerName, tempDealerCity, tempDealerState, tempDealerZip, tempDealerCountry, tempParentRepName,
                            tempColorPackage, tempPanelColor, tempAccentPanel, tempTrimAccent, tempBaseVinyl, tempWebOrderNo, tempPresold,
                            tempActive, tempSNID, tempQuantity]);
                        //console.log(tempData);
                        if (origOrdType === 'C') {
                            eos.sStatement(updateStatement, [masterBoatSerialNo, '0']).then(function () {
                                console.log('Boat Processed is C ');
                                // next record
                                proccess(i + 1);
                            });
                        } else {
                            if (masterActive === '0') {
                                eos.sStatement(updateAll, tempData).then(function () {
                                    console.log('Boat Processed - All');
                                    // next record
                                    proccess(i + 1);
                                });
                            } else {
                                proccess(i + 1);
                            }
                        }
                    }
                });

            } // proccess

            proccess(0);

            //console.log('newrecordswritten',newrecordswritten);
        });
    }
,
    EXPORT_RESET: function () {
        console.log('EXPORT_RESET', Date());
        var d = new Date();
        eos.ben.addByListName('Scheduler_Log', [d.getDate() + '/' + (d.getMonth() + 1) + '/' + d.getFullYear() + ' @ ' + d.getHours() + ':' + d.getMinutes() + ':' + d.getSeconds(), 'EXPORT_RESET'])
        eos.ben.deleteByListName('PW_warranty_claim_export_counter', '*/*');
        eos.ben.addByListName('PW_warranty_claim_export_counter', [1]);
    }
,
    DLR_GEOCODE: function () {
        debug('DLR_GEOCODE: Works, but need live running yet.');
        var d = new Date();
        eos.ben.addByListName('Scheduler_Log', [d.getDate() + '/' + (d.getMonth() + 1) + '/' + d.getFullYear() + ' @ ' + d.getHours() + ':' + d.getMinutes() + ':' + d.getSeconds(), 'DLR_GEOCODE'])
        var delete_notshow = [];
        Q.all([eos.sStatement('ALL_DLR'), eos.ben.loadByListName('Dealer_Latitude_Longitude')]).spread(function (dlrList, latLongList) {
            _.each(dlrList, function (dlr, i) {
                //console.log(i, dlrList[i].DlrNo);
                var dlrNo = dlrList[i].DlrNo;
                var dlrName = dlrList[i].DealerName;
                var add1 = dlrList[i].Add1;
                var add2 = dlrList[i].Addr2;
                var city = dlrList[i].City;
                var state = dlrList[i].State;
                var zip = dlrList[i].Zip;
                var country = dlrList[i].Country;
                var status = dlrList[i].CustomerTypeDesc;
                var donotshowflag = dlrList[i].DoNotShowFlag;
                //console.log(dlrNo);
                var dlrNoTrimmed = dlrNo.replace(/^(0+)/g, '');
                //if a dealer changes from Active to Inactive, remove them.
                //console.log('dlrNo is ', dlrNo, 'trimmed is ', dlrNoTrimmed);
                var dlrLatLong = _.where(latLongList, {
                    DlrNo: dlrNoTrimmed
                });
                //console.log('dlrLatLong', dlrLatLong);
                if (donotshowflag === '1' && dlrNoTrimmed != 'ZZSTOCK') {
                    delete_notshow.push(dlrName + ' (' + dlrNoTrimmed + ')');
                    eos.ben.deleteByListName('Dealer_Latitude_Longitude', 'LIST/DlrNo[="' + dlrNoTrimmed + '"]');
                } else if (status === 'Active' && donotshowflag === '0') {
                    if (dlrLatLong.length == 0) { //not found
                        debug('Not Found or Add changed: ', dlrName + ' (' + dlrNoTrimmed + ')', add1, add2, city, state, zip, country, status);
                        if (dlrNoTrimmed != 'ZZSTOCK' && add1 != '-' && city != '-' && state != '-' && zip != '-' && country !== 'NORDIC') { //try to stop it from breaking at blank addresses or dashes.
                            debug('     Dealer address: ', add1, city, state, zip);
                            eos.getGeocode(add1 + ' ' + city + ' ' + state + ' ' + zip).then(function (coord) {
                                debug('         Coords', dlrNoTrimmed, coord);

                                eos.sendEmail('KRimbaugh@benningtonmarine.com, mkrohn@benningtonmarine.com, ', 'Dealer: ' + dlrName + '(' + dlrNoTrimmed + '). Coords: ' + JSON.stringify(coord), "GEOCODE: Dealer is not found in Dealer_Latitude_Longitude list.");

                                var lat = coord[0];
                                var long = coord[1];
                                var newRow = [dlrNoTrimmed, dlrName, add1, add2, country, status, lat, long, donotshowflag];
                                eos.ben.addByListName('Dealer_Latitude_Longitude', newRow); //Dealer Latitude Longitude Local List.
                            });
                        } else {
                            debug('     Bad address!');
                        }
                    } else if (dlrLatLong.length > 0) { //does exist in lat long
                        if (dlrLatLong[0].Add1 !== add1) {
                            debug('Not the same Address', dlrLatLong[0].Add1, add1);
                            eos.getGeocode(add1 + ' ' + city + ' ' + state + ' ' + zip).then(function (coord) {

                                debug('     New coordinates:', JSON.stringify(coord));
                                var lat = coord[0];
                                var long = coord[1];
                                var newRow = [dlrNoTrimmed, dlrName, add1, add2, country, status, lat, long, donotshowflag];
                                eos.ben.deleteByListName('Dealer_Latitude_Longitude', 'LIST/DlrNo[="' + dlrNoTrimmed + '"]').then(function () {
                                    debug('     New row:', JSON.stringify(newRow));
                                    eos.ben.addByListName('Dealer_Latitude_Longitude', newRow); //Dealer Latitude Longitude Local List.
                                });
                            });
                        }
                    }
                } else {
                    debug('BAD Dealer: ', dlrName + ' (' + dlrNoTrimmed + ')', status, donotshowflag);
                }
            });

            debug('Delete and Do Not Show: ', delete_notshow.join(', '));

        });
    }
,
    SHIP: function () {
        debug('SHIP');
        var d = new Date();
        eos.ben.addByListName('Scheduler_Log', [d.getDate() + '/' + (d.getMonth() + 1) + '/' + d.getFullYear() + ' @ ' + d.getHours() + ':' + d.getMinutes() + ':' + d.getSeconds(), 'SHIP'])
        var date = new Date();
        var status_date = date.toLocaleString().split(',')[0];
        var year = date.getFullYear();
        var month = (date.getMonth() + 1) < 10 ? '0' + (date.getMonth() + 1) : (date.getMonth() + 1);
        var day = date.getDate();
        day = (day - 1).toString();
        day = day[1] ? day : '0' + day;
        var use_date = year.toString() + month.toString() + day.toString();
        var sendtoEmail = '';
        let actualUpdateData = [];
        debug(use_date);
        Q.all([eos.sStatement('SHIP_UPDATE22', ['Y']), eos.sStatement('SHIP_UPDATE22', ['N'])]).spread(function (new_data_rga, new_data) {
            console.log('new_data_rga =>', new_data_rga.length);
            console.log('new_data =>', new_data.length);

            actualUpdateData = [...new_data];

            _.each(new_data_rga, function (r, k) {
                let _row = actualUpdateData.find(row => row.PartsOrderID == r.PartsOrderID && row.LineNo == r.LineNo);
                // -- row exists with a non RGA line, add additional tracking #
                if (_row) {
                    _row.UPSTrackingNo = _row.UPSTrackingNo + ',' + r.UPSTrackingNo;
                }

                // // -- RGA only order, add it in to the final data to be used
                else {
                    actualUpdateData.push(r);
                }
            });

            console.log('actualUpdateData.length =>', actualUpdateData.length);
            console.log('actualUpdateData => ', JSON.stringify(actualUpdateData));

            var done = Q.defer();
            processUpdate(0, sendtoEmail);
            done.promise.then(function (sendtoEmail) {
                //eos.sendEmail('akemp@verenia.com', sendtoEmail, 'ship update');
                eos.sendEmail('ZSpringman@benningtonmarine.com, DHartsough@benningtonmarine.com, spenick@benningtonmarine.com', sendtoEmail, 'ship update');
            });

            function prepareUpdate(new_data_row, StateChg_ID) {
                //console.log(new_data_row);
                var oe_number = new_data_row.ERP_OrderNo; // update the part order header with this.
                var track_no = new_data_row.UPSTrackingNo;
                var POID = new_data_row.PartsOrderID;
                var ship_ID = new_data_row.ShipmentID;
                var lineNo = new_data_row.LineNo;
                var OLID = new_data_row.OrdLineID;
                var ship_date = new_data_row.date;
                //console.log([StateChg_ID, OLID, OLID, 'PartOrderLineItem', 'completed','Completed', '', ship_date, '']);
                return {
                    array: [StateChg_ID, OLID, OLID, 'PartOrderLineItem', 'completed', 'Completed', '', ship_date, ''],
                    POID: POID,
                    lineNo: lineNo,
                    track_no: track_no,
                    ship_date: ship_date,
                    oe_number: oe_number
                }
            }

            function processUpdate(index, sendtoEmail) {
                if (index == actualUpdateData.length) {
                    done.resolve(sendtoEmail);
                    console.log('SHIP: we are done');
                    return;
                }
                // console.log('processing shipping update ' + (index + 1) + '/' + new_data.length /*,process.memoryUsage()*/ );
                eos.sStatement('PW_GET_PART_STATE_CHG_ID').then(function (res) {
                    var StateChg_ID = res[0].ID;
                    var statusTracker = prepareUpdate(actualUpdateData[index], StateChg_ID);
                    sendtoEmail += 'Now updating PartOrder ID: ' + statusTracker.POID + ' with line#: ' + statusTracker.lineNo + ' with tracking number: ' +
                        statusTracker.track_no + '<br>' + ' and marking this line completed with the date ' + statusTracker.ship_date + '<br><br>';
                    eos.sStatement('SHIP_UPDATE_PARTS', [statusTracker.POID, statusTracker.track_no, statusTracker.ship_date, 'completed', 'Completed', eos
                        .getDate(), statusTracker.lineNo, statusTracker.oe_number
                    ])
                    eos.ben.syncStatement('PW_ADD_STATUS_TO_TRACKER_PARTS', statusTracker.array, function (err, res, body) {
                        if (err) throw 'error';
                        processUpdate(index + 1, sendtoEmail);
                    });
                });
            }
        });

        function addPartLineStatusToTracker(i, ordLineID, public_status, ordStatus, mdy) {
            console.log('addPartLineStatusToTracker', i);
            eos.sStatement('PW_GET_PART_STATE_CHG_ID').then(function (res) {
                console.log('finished addPartLineStatusToTracker', i, StateChg_ID);
                var StateChg_ID = res[0].ID;
                var statusTracker = [StateChg_ID, ordLineID, ordLineID, 'PartOrderLineItem', public_status, ordStatus, '', mdy, ''];
                eos.sStatement('PW_ADD_STATUS_TO_TRACKER_PARTS', statusTracker);
            });
        }

        function logDate() {
            var ok = getDate().split("/");
            --ok[1];
            return ok.join("/");
        }
    }
,
    DLR_UPDATE: function () {
        console.log('DLR_UPDATE', Date());
        var d = new Date();
        eos.ben.addByListName('Scheduler_Log', [d.getDate() + '/' + (d.getMonth() + 1) + '/' + d.getFullYear() + ' @ ' + d.getHours() + ':' + d.getMinutes() + ':' + d.getSeconds(), 'DLR_UPDATE'])
        Q.all([eos.sStatement('DLR_UPDT_TBL'), eos.sStatement('ALL_DLR')]).spread(function (dlrtemplist, dlrlist) {
            var done = Q.defer();
            console.log('Total dealer update ' + dlrtemplist.length);
            processDealerUpdate(0);
            done.promise.then(function () {
                console.log('DLR_UPDATE complete');
            });

            function prepDealerUpdate(dlrtemprow) {
                var DlrNo = dlrtemprow.DlrNo;
                var SalesPerson = dlrtemprow.SalesPerson;
                var SalesPersonNo = dlrtemprow.SalesPersonNo;
                var DealerName = dlrtemprow.DealerName;
                var DealerDBA = dlrtemprow.DealerDBA;
                var Contact = dlrtemprow.Contact;
                var Add1 = dlrtemprow.Add1;
                var Addr2 = dlrtemprow.Addr2;
                var City = dlrtemprow.City;
                var State = dlrtemprow.State;
                var Zip = dlrtemprow.Zip;
                var County = dlrtemprow.County;
                var FIPSCode = dlrtemprow.FIPSCode;
                var Country = dlrtemprow.Country;
                var PhoneNo = dlrtemprow.PhoneNo;
                var Email_Address = dlrtemprow.Email_Address;
                var cus_type_cd = dlrtemprow.cus_type_cd;
                var CustomerTypeDesc = dlrtemprow.CustomerTypeDesc;
                var cr_rating = dlrtemprow.cr_rating;
                var prdline_no = dlrtemprow.prdline_no;
                var Date_Active = dlrtemprow.Date_Active;
                var Date_Inactive = dlrtemprow.Date_Inactive;
                var Inactive_Reason = dlrtemprow.Inactive_Reason;
                var Warranty_Labor_Rate = dlrtemprow.Warranty_Labor_Rate;
                var Default_Terms_Code = dlrtemprow.Default_Terms_Code;
                var Terms_Desc = dlrtemprow.Terms_Desc;
                var Fax = dlrtemprow.Fax;
                var Phone2 = dlrtemprow.Phone2;
                var ParentCustNo = dlrtemprow.ParentCustNo;
                var Web_URL = dlrtemprow.Web_URL;
                var DoNotShowFlag = dlrtemprow.DoNotShowFlag;

                var dlrRec = _.where(dlrlist, {
                    DlrNo: DlrNo
                });
                if (dlrRec.length > 0) {
                    return {
                        STATEMENT: 'UPD_DLR_LIST_SCH',
                        ARRAY: [DlrNo, SalesPerson, SalesPersonNo, FIPSCode, cus_type_cd, CustomerTypeDesc, cr_rating, prdline_no, Date_Active,
                            Date_Inactive, Inactive_Reason, Warranty_Labor_Rate, Default_Terms_Code, Terms_Desc, DoNotShowFlag, DealerDBA, DealerName]
                    }
                } else {
                    return {
                        STATEMENT: 'INS_DLR_LIST',
                        ARRAY: [SalesPerson, SalesPersonNo, DealerName, DealerDBA, DlrNo, Contact, Add1, Addr2, City, State, Zip, County,
                            FIPSCode, Country, PhoneNo, Email_Address, cus_type_cd, CustomerTypeDesc, cr_rating, prdline_no, Date_Active,
                            Date_Inactive, Inactive_Reason, Warranty_Labor_Rate, Default_Terms_Code, Terms_Desc, Fax, Phone2, ParentCustNo, Web_URL,
                            DoNotShowFlag]
                    }
                }
            }

            function processDealerUpdate(index) {
                if (index == dlrtemplist.length) {
                    done.resolve();
                    console.log('DLR_UPDATE: we are done');
                    return;
                }
                // console.log('processing dealer update ' + (index + 1) + '/' + dlrtemplist.length);
                var output = prepDealerUpdate(dlrtemplist[index]);
                //console.log(output.STATEMENT);
                eos.ben.syncStatement(output.STATEMENT, output.ARRAY, function (err, res, body) {
                    if (err) throw 'error';
                    processDealerUpdate(index + 1);
                });
            }
        });
    }
,
    WARR_CLAIMS: function () {
        console.log('WARR_CLAIMS', Date());
        var d = new Date();
        eos.ben.addByListName('Scheduler_Log', [d.getDate() + '/' + (d.getMonth() + 1) + '/' + d.getFullYear() + ' @ ' + d.getHours() + ':' + d.getMinutes() + ':' + d.getSeconds(), 'WARR_CLAIMS'])
        eos.sStatement('CLUB_B_UPDATES_TO_OWNERS').then(function (newRegs) {
            //Then just step through these and update the record with the ClubID, and email, using the OwnerID
            for (var i in newRegs) {
                var ownerID = newRegs[i].OwnerID;
                var clubID = newRegs[i].ClubID;
                var email = newRegs[i].OwnerEmail;
                eos.sStatement('CLUB_B_ADD_ID_UPDATE', [ownerID, clubID, 1, email]);
                console.log('Adding clubID:', clubID, 'to ownerID:', ownerID);
            }
            eos.sendEmail('tunterfenger@verenia.com', 'Completed club bennington ID update', 'Club ID update');
        });
    }
,
    UPD_OE_PARTS: function () {
        var d = new Date();
        eos.ben.addByListName('Scheduler_Log', [d.getDate() + '/' + (d.getMonth() + 1) + '/' + d.getFullYear() + ' @ ' + d.getHours() + ':' + d.getMinutes() + ':' + d.getSeconds(), 'UPD_OE_PARTS'])
        console.log('UPD_OE_PARTS', Date());
        eos.sStatement('UPDATE_ERP_ORDERNO');
    }
,
    SPECS_COMPILE_OPTIONS: function () {
        console.log('SPECS_COMPILE_OPTIONS', Date());
        console.log('Clear stored compiled options');
        var d = new Date();
        eos.ben.addByListName('Scheduler_Log', [d.getDate() + '/' + (d.getMonth() + 1) + '/' + d.getFullYear() + ' @ ' + d.getHours() + ':' + d.getMinutes() + ':' + d.getSeconds(), 'SPECS_COMPILE_OPTIONS'])
        eos.sStatement('SPECS_DEL_COMPILED_OPTIONS').then(function () {
            //make sure all the boats in the system have compiled options.
            //that way you can figure out how to let them change the # of boats to show
            eos.sStatement('SEL_DISCTINT_PRODNOS_IN_OPTIONS').then(function (allboats) {
                var specUpdate = Q.defer();
                console.log('records to process', allboats.length);
                processOption(0, allboats, specUpdate);
                specUpdate.promise.then(function () {
                    debug('SPECS_COMPILE_OPTIONS: Done');
                });
            });
        });

        function processOption(index, allboats, specUpdate) {
            if (index == allboats.length) {
                specUpdate.resolve();
                return;
            }
            // console.log('SPECS processOption', index);
            var prod = allboats[index].ProdNo;
            //console.log(prod);
            eos.sStatement('SEL_SPECS_ALL_LIVE_BOAT_OPTIONS', [prod]).then(function (alloptions) {
                //console.log(alloptions);
                var options = '';
                for (var j in alloptions) {
                    var wc = alloptions[j].Workcenter;
                    options += alloptions[j].Option_Desc + '</br>';
                }
                options = options.substring(0, options.length - 5);
                //console.log(prod, options);
                var insData = ([prod, options, wc]);
                // console.log('Insert');
                eos.ben.syncStatement('INS_SPECS_OPTIONS_COMPILED', insData, function (err, res, body) {
                    if (err) throw 'error';
                    processOption(index + 1, allboats, specUpdate);
                });
            });
        }
    }
,
    BOAT_REGISTRATION: function () {
        "use strict";
        debug('> BOAT_REGISTRATION: Start');

        function sendRegistration(data) {
            var d = Q.defer();
            request({
                url: 'https://node.eoscpq.com/bennington/pwregistration',
                method: 'POST',
                json: true,
                body: {
                    key: clients[client].publicKey,
                    data: data
                },
            }, function (err, res, body) {
                if (err) {
                    console.log('pwregistration error:', err);
                    d.reject(err);
                } else {
                    d.resolve(body);
                }
            });
            return d.promise;
        }

        var report = {
            success: [],
            failure: [],
        };
        eos.sStatement('LOAD_BOAT_REG_UPDATE_TABLE').then(function (allboats) {
            debug('> BOAT_REGISTRATION: Total numbers: ' + allboats.length);

            function processSN(boatindex) {
                if (allboats.length == boatindex) {
                    // Completed
                    debug('> BOAT_REGISTRATION: Done');

                    eos.sendEmail(
                        'spenick@benningtonmarine.com',
                        (report.failure.length > 0 ? ("The following Serial Numbers were NOT registered into the system:<br>" + report.failure.join("<br>") + "<br><br>") : '') +
                        (report.success.length > 0 ? ("The following Serial Numbers were registered into the system:<br>" + report.success.join("<br>") + "<br><br>") : ''),
                        "Boat Registration Import Report");

                    return true;
                }

                var boat = allboats[boatindex];
                sendRegistration(boat).then(function (result) {

                    if (result.result) {
                        eos.ben.addByListName('Auto Registration Log', [new Date(), boat.SerialNo, "OK"]);
                        eos.ben.syncStatement('UPDATE_BOAT_REG_UPDATE_TABLE', [boat.SerialNo], function () {
                            report.success.push(boat.SerialNo);
                            processSN(boatindex + 1);
                        });
                    } else {
                        eos.ben.addByListName('Auto Registration Log', [new Date(), boat.SerialNo, result.error]);
                        report.failure.push(boat.SerialNo);
                        processSN(boatindex + 1);
                    }

                });

            }

            processSN(0);

        });
    }
}
