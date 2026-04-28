/*-------  Metadata -----
   *** Please do not touch this header ***

ID: 653ff36409525759ab0e5ff3
NAME: Syteline Parts Export
CODE: SYTELINE_PARTS
RULE: EOS/SELECTED_ANSWER[="SYTELINE"]
DOWNLOAD DATE: 2025-01-07T15:49:16.390Z

-------------------------*/


window.ExportSytelineParts = window.ExportSytelineParts || function (ordersIDs) {
    console.log("SYTELINE PARTS EXPORTED!");
    console.log(ordersIDs);

    var parts_data;
    var parts_status = $('#parts_order_status').val() !== '' ? $('#parts_order_status').val() : '%%';
    var parts_order_id = hasAnswer('PART_INFO', 'TRANS_ID') ? '%' + getValue('PART_INFO', 'TRANS_ID') + '%' : '%%';
    var serial_num = hasAnswer('PART_INFO', 'PARTS_SN') ? '%' + getValue('PART_INFO', 'PARTS_SN') + '%' : '%%';
    var part_num = hasAnswer('PART_INFO', 'PART_NO') ? '%' + Number(getValue('PART_INFO', 'PART_NO')) + '%' : '%%';
    var nc_code = hasAnswer('PART_INFO', 'NC_CODE') ? '%' + getValue('PART_INFO', 'NC_CODE') + '%' : '%%';
    var d_name = hasAnswer('PART_INFO', 'DEALER_NAME') ? getValue('PART_INFO', 'DEALER_NAME') : '%%';
    var date1 = hasAnswer('PART_INFO', 'DATE1') ? getValue('PART_INFO', 'DATE1').replace(/['/']/g, '-') : '01-01-1901';
    var date2 = hasAnswer('PART_INFO', 'DATE2') ? getValue('PART_INFO', 'DATE2').replace(/['/']/g, '-') : '12-31-9999';
    var rga_status = $('#rga_status_drop').val() !== '' ? $('#rga_status_drop').val() : '%%';
    var invalidDates = (date1 == '01-01-1901' && date2 == '12-31-9999');
    var other_rga_status = rga_status;
    var other_Dealer;

    if (contains(parts_order_id, 'WP') || contains(parts_order_id, 'WN') || contains(parts_order_id, 'wp') || contains(parts_order_id, 'wn')) {
        parts_order_id = Number(parts_order_id.replace(/['WN','WP','wn','wp','%']/g, ''));
    }
    if (!$.isNumeric(d_name) && d_name !== '%%') {
        d_name = '%' + d_name + '%';
        other_Dealer = '%%';
    } else if ($.isNumeric(d_name)) {
        other_Dealer = Number(d_name);
        d_name = pad(d_name, 8, 0);
    } else if (d_name == '%%') {
        other_Dealer = '%%';
    }

    if (perm.hasDropdown) {
        d_name = $('#setting_select').val();
        if (d_name)
            d_name = pad(d_name, 8, 0);
    }

    if (rga_status == 'returned') {
        other_rga_status = 'Completed';
    }

    //Add onto the filter if there are individual orders selected

    var selectedOrders = "";
    var counter = 0;
    if (ordersIDs.length > 0) {
        selectedOrders += "WHERE ";
        for (let i = 0; i < ordersIDs.length; i++) {

            if (counter === 0) {
                selectedOrders += "t2.PartsOrderID='" + ordersIDs[i] + "'";
            }
            if (counter > 0 && counter < ordersIDs.length) {
                selectedOrders += " OR t2.PartsOrderID='" + ordersIDs[i] + "'";
            }
            counter++;
        }
        //Added additional filter so cancelled lines don't get caught in this query
        selectedOrders += " AND t1.OrdLineStatus != 'cancelled'"
    }

    var part_desc = hasAnswer('PART_INFO', 'PART_DESC') ? '%' + getValue('PART_INFO', 'PART_DESC') + '%' : '%%';
    var dealer_ref = hasAnswer('PART_INFO', 'D_PO_REF') ? '%' + getValue('PART_INFO', 'D_PO_REF') + '%' : '%%';
    var rep = hasAnswer('PART_INFO', 'SALES_REP') ? '%' + getValue('PART_INFO', 'SALES_REP') + '%' : '%%';
    var oeNo = hasAnswer('PART_INFO', 'OE') ? '%' + getValue('PART_INFO', 'OE') + '%' : '%%';
    var params = [parts_status, parts_order_id, serial_num, part_num, nc_code, d_name, part_desc, dealer_ref, oeNo, date1, date2, rep];
    //^^^^^^^^^^^^^^^^^ IF YOU CHANGE ANYTHING IN THESE PARAMATERS/SQL STATEMENT PLEASE REFLECT THAT CHANGE ONTO THE SytelinePartsBreakdown LIST AS WELL
    var paramsDate = [
        parts_status, parts_order_id, serial_num, part_num,
        nc_code, d_name, part_desc, dealer_ref, oeNo, other_Dealer,
        date1, date2
    ];
    var paramsDate2 = [
        parts_status, parts_order_id, serial_num, part_num,
        nc_code, d_name, part_desc, dealer_ref, oeNo, other_Dealer,
        date1, date2, rga_status, other_rga_status
    ];

    var allEqual = allAreEqual(params);
    var useStatement = 'FILTER_ORDERS_TEST_DATES';

    if (ordersIDs.length === 0) {
        parts_data = sStatement("FILTER_ORDERS_SYTELINE", params);
        //^^^^^^^^^^^^^^^^^ IF YOU CHANGE ANYTHING IN THESE PARAMATERS/SQL STATEMENT PLEASE REFLECT THAT CHANGE ONTO THE SytelinePartsBreakdown LIST AS WELL
    } else {
        parts_data = loadByListName("SytelinePartsBreakdown", selectedOrders);
        console.log("PARTS ORDER FILTERED DOWN BASED ON SELECTIONS!");
        //console.log(parts_data[0].toString());
    }


    console.log("ZACH PARAMS " + params);


    //Need to generate the XML now that we have the conditional data. Generate both the header and line items for EACH row.
    //Has been determined that only one file should be produced containing all the resulting parts orders 10/30/2023

    //XML Statis Header

    var xmlContent = `<ProcessTest_Verenia_Boat xmlns='http://schema.infor.com/InforOAGIS/2' xmlns:xs='http://www.w3.org/2001/XMLSchema'>
                  <ApplicationArea>
                       <Sender>
                           <LogicalID>infor.file.test_verenia_boat_sftp</LogicalID>
                           <ComponentID>External</ComponentID>
                           <ConfirmationCode>OnError</ConfirmationCode>
                       </Sender>
                       <CreationDateTime>2023-09-07T16:34:51.379Z</CreationDateTime>
                       <BODID>infor.file.test_verenia_boat_sftp:1694104491379:ee1ccf40-6bcd-4c72-8b61-8709239345eb</BODID>
                   </ApplicationArea>
                   <DataArea>
                       <Process>
                       <AccountingEntityID xmlns=""/>
                       <LocationID xmlns=""/>
                       <ActionCriteria>
                           <ActionExpression actionCode='Add'/>
                       </ActionCriteria>
                       </Process>`;

    //Loop through all the parts orders

    var last_processed = "";

    for (const item of parts_data) {

        var rga = 0;
        var rga_Due = "";
        var formattedRGADate = "";

        try {
            if (item.RGAID == null) {
                rga = 0;
            } else {
                rga = 1;
            }
        } catch (error) {
            console.error("ERROR GRABBING RGAID");
        }

        try {
            if (item.RGAReturnDueDate === null || item.RGAReturnDueDate === "") {
                rga_Due = "";
            } else {
                rga_Due = item.RGAReturnDueDate;
                let rga_parts = rga_Due.split("/");
                let rga_year = rga_parts[2];
                let rga_month = rga_parts[0];
                let rga_day = rga_parts[1];

                formattedRGADate = `${rga_year}-${rga_month}-${rga_day}`
            }
        } catch (error) {
            console.error("ERROR GRABBING RGA DATE");
        }


        //pending orders do not have shipment assigned
        if (parts_status !== 'pending' && last_processed === item.ShipmentID) {
            console.error("DUPLICATE SHIPMENT");
            continue;
        }


        //Need to set some definitions for when a part is charge or no charge
        var id_header;
        var charge_nc;
        var charge_parts;
        if (item.OrdHdrClaimType == "n/c_parts") {
            id_header = "WN";
            charge_parts = "NO CHARGE PARTS";
            charge_nc = "No Charge";
        } else if (item.OrdHdrClaimType == "parts_order") {
            id_header = "WP";
            charge_parts = "CHARGE PARTS";
            charge_nc = "Charge";
        }

        //var contentFilter = constructStringUsingSearchBar(webOrderCSV, searchValue, id);
        var contentFilter = "WHERE Boat_SerialNo = '";
        contentFilter += item.OrdHdrBoatSerialNo;
        contentFilter += "'";
        console.log("ZACH FILTER: " + contentFilter);

        //Use filter to get the panel color from the Serial Master
        if (item.OrdHdrBoatSerialNo !== "StockParts") {
            var PanelColor = loadList('6596ce510952574cd335d1a3', contentFilter);

            var panel_color = "";
            try {
                panel_color = PanelColor[0].PanelColor;
            } catch (error) {
                console.error("PANEL COLOR DOES NOT EXIST FOR THIS SERIAL NO");
            }

            var boat_model = ""
            try {
                boat_model = PanelColor[0].BoatItemNo;
            } catch (error) {
                console.error("BOAT MODEL DOES NOT EXIST FOR THIS SERIAL NO");
            }


        }

        //If a stock part, clear the panel color
        if (item.OrdHdrBoatSerialNo == "StockParts") {
            panel_color = "";
        }

        //Need to get international data
        var international = "";
        var international_type = "";
        var dealernum_filter = "";

        //Only Charge parts can be international... need to leave no charge parts blank
        if (item.OrdHdrClaimType == "parts_order") {
            dealernum_filter = "WHERE DlrNo = '";
            dealernum_filter += item.OrdHdrDealerNo;
            dealernum_filter += "'";

            console.log("DEALER FILTER: " + dealernum_filter);

            var international_data = loadList("65a9786e09525761715bf2a6", dealernum_filter);

            console.log("INTERNATIONAL DATA: " + international_data[0]);

            try {
                international = international_data[0].International;
            } catch (error) {
                console.error("INTERNATIONAL DATA ERROR");
            }

            try {
                international_type = international_data[0].InternationalType;
            } catch (error) {
                console.error("INTERNATIONAL TYPE DATA ERROR");
            }

            //+id_header + pad(item.ShipmentID, 7, 0) + '-S' + item.ShipmentNo+
        }

        var ship_id = item.ShipmentID;
        console.log("SHIP ID TEST: " + ship_id);

        var trim_shipid = ship_id.slice(0, -2).padStart(7, '0');
        var trim_shipidnum = ship_id.slice(7);

        var shipmentid = id_header + trim_shipid + '-S' + trim_shipidnum;


        var ar_terms = "";

        if (item.OrdHdrClaimType == "n/c_parts") {
            ar_terms = item.NCPartsCode;
        }
        if (item.OrdHdrClaimType == "parts_order") {
            ar_terms = getTermsCode(item.Default_Terms_Code);
        }

        //Zach added 5/15/24 - ShipCode was coming in as null, causes XML import to fail
        var carrierParty = item.ShipMethShipCode;
        //console.log("ZACH SHIPMETHCODE: "+item.ShipMethShipCode);
        try {
            if (carrierParty === null || carrierParty === "null") {
                carrierParty = "";
            }
        } catch (error) {
            console.error(error);
        }

        //Zach added 10/7/2024 - Use order id to grab username of person that submitted order.
        //Use the audit table to grab user id from pending line.
        var orderLineID = item.OrdLineID;

        var userIDFilter = "WHERE (StateChg_ChgToState = 'Pending' or StateChg_ChgToState = 'pending') and OrdLineID = " + orderLineID;

        var userIDList = loadByListName("PW_GetUserIDOnOrder", userIDFilter);

    // Check if userID is not null before proceeding
        if (userIDList.length > 0 && userIDList[0].StateChg_UserID) {
            var userID = userIDList[0].StateChg_UserID;
            // Now I have the user ID, so I need to grab the username from the proper table
            var usernameFilter = "WHERE USER_ID = '" + userID.toString() + "'";
            var usernameList = loadByListName("PW_GetUsernameOnOrder", usernameFilter);
            var username = usernameList[0].USERNAME;
            console.log("ZACH USERNAME TEST: " + username);
            // console.log("USERNAME THAT IS ON THE ORDER: " + username.toString());
        } else {
            //The user ID is blank for who created the pending order...this might happen because the order was created straight to approved by someone on our team
            //instead get the default email from the dealer...bypasses the userID
            dealerno_filter = "WHERE DlrNo = '";
            dealerno_filter += item.OrdHdrDealerNo;
            dealerno_filter += "'";

            //List name dealers under Admin Tools >> System Maintenance >> Lists
            var dealer_data = loadList("550704ca8ff578635263ac94", dealerno_filter);

            try{
                //var username = dealer_data[0].Email_Address;
                if (dealer_data.length > 0) {
                    var username = dealer_data[0].Email_Address;
                    console.log("Dealer email: " + username);
                } else {
                    console.error("No dealer data found for the given dealer number.");
                }
            } catch(error) {
                console.error("Error getting the email address from the dealer record");
            }

        }


        // Temp fix: Wilson Marine (559236) has SelectedCustSeq='1' stored for their
        // primary Brighton address but ~1 does not exist in Syteline — force to ~0.
        // Remove once root cause (portal storing wrong seq at order creation) is fixed.
        var shipToCustSeq = (item.SelectedCustSeq?.trim() ? item.SelectedCustSeq : "0");
        if (item.OrdHdrDealerNo.replace(/^0+/, "") === "559236" && shipToCustSeq === "1") {
            shipToCustSeq = "0";
        }

        xmlContent += `<Test_Verenia_Boat>
                            <Test_Verenia_BoatHeader>
                                <AlternateDocumentID>
                                    <ID>` + shipmentid + `</ID>
                                </AlternateDocumentID>
                                <ShipToParty>
                                    <PartyIDs>
                                        <ID>` + item.OrdHdrDealerNo.replace(/^0+/, "") + `~` + shipToCustSeq + `</ID>
                                    </PartyIDs>
                                </ShipToParty>
                                <CarrierParty>
                                    <PartyIDs>
                                        <ID>` + carrierParty + `</ID>
                                    </PartyIDs>
                                </CarrierParty>
                                <PaymentTerm>
                                    <Term>
                                        <ID>` + ar_terms + `</ID>
                                    </Term>
                                </PaymentTerm>
                                <PurchaseOrderReference>
                                    <DocumentID>
                                        <ID>` + item.OrdHdrDealerRefNo + `</ID>
                                    </DocumentID>
                                </PurchaseOrderReference>
                                <OrderDateTime>` + item.HdrCreateDate + `</OrderDateTime>
                                <ue_BennOrderType>` + charge_parts + `</ue_BennOrderType>
                                <ue_EngineForBoat/>
                                <ue_PreSold/>
                                <ue_ShowBoat/>
                                <ue_RentalBoat/>
                                <PanelColor>` + panel_color + `</PanelColor>
                                <BaseVinyl/>
                                <BuildComments/>
                                <DealerComments/>
                                <BoatModel>` + boat_model + `</BoatModel>
                                <BoatSerialNo>` + item.OrdHdrBoatSerialNo + `</BoatSerialNo>
                                <ShippingMethod>` + item.ShipMethShipCode + `</ShippingMethod>
                                <BennTermsCode>` + item.NCPartsCode + `</BennTermsCode>
                                <ue_International>` + international + `</ue_International>
                                <ue_InternationalType>` + international_type + `</ue_InternationalType>
                                <ue_SpecialInstructions>` + item.OrdHdrSpecInstructions + `</ue_SpecialInstructions>
                                <ue_Reason>` + item.OrdHdrRequestReason + `</ue_Reason>
                                <ue_LoadNumber/>
                                <ue_BennOwned></ue_BennOwned>
                                <ue_CustTrackingEmail>` + username + `</ue_CustTrackingEmail>
                            </Test_Verenia_BoatHeader>
                             `
        //Need to get a data source that has all the lines associated with the given shipment ID
        //Loop through the lines and create an XML line for each one.
        var parts_shipped = [];

        console.log("SHIP ID: " + ship_id)
        var shipid_array = [ship_id];

        parts_shipped = sStatement("PW_SCHEDULE_LINES", shipid_array);

        var date = new Date();
        var param_date = date.toLocaleString();

        for (var i = 0; i < parts_shipped.length; i++) {

            let shipdate = parts_shipped[i].OrdLineEstShipDate;
            // Parse the date string manually
            let parts = shipdate.split("/");
            let year = parts[2];
            let month = parts[0];
            let day = parts[1];

            // Ensure month and day are in 'mm' and 'dd' format
            month = month.padStart(2, '0');
            day = day.padStart(2, '0');

            // Format to 'yyyy-MM-dd'
            let formattedShipDate = `${year}-${month}-${day}`;

            var lastrecord = 0;
            if (i == parts_shipped.length - 1 || parts_shipped.length == 1) { //to get the last line item out of the group
                lastrecord = 1;
            }

            var item_desc = !parts_shipped[i].OrdLineModDesc ? parts_shipped[i].OrdLinePartDesc : parts_shipped[i].OrdLineModDesc;

            var price_trimmed = parts_shipped[i].DealerPrice.replace(/\$/g, '');

            //ZS Added a Check for Item # on 5/15/24.
            //If item is blank then need to grab the modified part number in its place

            var itemno = "";
            try {
                if (parts_shipped[i].OrdLinePartNo === "" || parts_shipped[i].OrdLinePartNo === null) {
                    //If no item number is present - grab the modified item number
                    itemno = parts_shipped[i].OrdLineModPartNo;
                } else {
                    itemno = parts_shipped[i].OrdLinePartNo;
                }
            } catch (error) {
                console.error(error);
            }

            xmlContent += `<Test_Verenia_BoatLine>
                                                <Item>
                                                    <ItemID>
                                                        <ID>` + itemno + `</ID>
                                                    </ItemID>
                                                </Item>
                                                <Quantity unitCode="EA">${parts_shipped[i].Qty_Ordered}</Quantity>
                                                <WarrantyClaimNo/>
                                                <WarrantyClaimLineID/>
                                                <UnitPrice>` + price_trimmed + `</UnitPrice>
                                                <ShippingInstructions/>
                                                <PartsWebOrderNo>${id_header + parts_shipped[i].PartsOrderID.toString().padStart(7, '0') + '-0' + parts_shipped[i].OrdLineNo}</PartsWebOrderNo>
                                                <ue_LastRecord>` + lastrecord + `</ue_LastRecord>
                                                <ue_Dealer_Comments/>
                                                <ue_Details_Sublet_Comments/>
                                                <ue_Item_Desc>` + item_desc + `</ue_Item_Desc>
                                                <ue_RGA>` + rga + `</ue_RGA>
                                                <ue_RGA_Date>` + formattedRGADate + `</ue_RGA_Date>
                                                <ue_Estimated_Shipping_Date>${formattedShipDate}</ue_Estimated_Shipping_Date>
                                                <ue_TransactionId>${id_header + parts_shipped[i].PartsOrderID.toString().padStart(7, '0') + '-0' + parts_shipped[i].OrdLineNo}</ue_TransactionId>
                                                <ue_Alternate_Shipping_Location>${parts_shipped[i].OrdHdrAltShipLoc}</ue_Alternate_Shipping_Location>
                                            </Test_Verenia_BoatLine>`
            if (i == parts_shipped.length - 1) {
                xmlContent += `</Test_Verenia_Boat>`;
            }
            last_processed = ship_id;
            console.log("LAST PROCESSED: " + last_processed);
        }
    }


    // Empty terminator block — Syteline skips it (no AlternateDocumentID / no lines)
    // but prevents the real last shipment block from being silently dropped.
    xmlContent += `<Test_Verenia_Boat><Test_Verenia_BoatHeader><AlternateDocumentID><ID></ID></AlternateDocumentID></Test_Verenia_BoatHeader></Test_Verenia_Boat>`;

    var xmlFooter = `
                </DataArea>
                </ProcessTest_Verenia_Boat>
                `;

    xmlContent += xmlFooter;


    //& Symbol makes the XML fail... go through and replace each symbol with the proper way.
    xmlContent = xmlContent.replace(/&/g, '&amp;');


    //ADD STATUS SETTING RIGHT HERE ONCE FUNCTION IS COMPLETE
    setLinesToExported(parts_data, param_date);

    return xmlContent;
};

if (getValue('EOS', 'SELECTED_ANSWER') == 'SYTELINE') {

    let ordersIDs = [];
    //grab the parts orders that were manually selected using the checkbox
    $('input[name="transaction-to-export"]:checked').each((i, e) => {
        ordersIDs.push($(e).val());
    });

    xmlContent = window.ExportSytelineParts(ordersIDs);

    var today = new Date();
    var date = today.getFullYear() + '_' + (today.getMonth() + 1) + '_' + today.getDate();
    var time = today.getHours() + "_" + today.getMinutes();
    var dateTime = date + ' ' + time;

    saveXMLToFile(xmlContent, "sytelineExport_" + dateTime);

    panel_color = "";

}


//Zach 10/31/2023 Happy Halloween! :)
function saveXMLToFile(xmlContent, filename) {
    try {
        var xmlBlob = new Blob([xmlContent], {type: 'application/xml'});
        var xmlUrl = URL.createObjectURL(xmlBlob);

        // Create a download link for the XML file
        var element = document.createElement('a');
        element.setAttribute('href', xmlUrl);
        element.setAttribute('download', filename + '.xml');
        element.style.display = 'none';

        // Append the link to the document body, trigger a click event, and remove the link
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);

        // Clean up the object URL
        URL.revokeObjectURL(xmlUrl);
    } catch (error) {
        console.error(`Error saving XML content to ${filename}: ${error.message}`);
    }
}

//ZS ADDED 10/7/2024 - Need a function to set status of order lines to exported
//List of parts order lines will be passed from initial logic above - loop through and set all to exported if previous status was approved.
function setLinesToExported(orderList, param_date) {

    //loop through order lines, check current status, and set to exported if curstatus is approved
    for (let i = 0; i < orderList.length; i++) {
        //console.log(orderList[i]);

        var curStatus = "";
        console.log("NEW - ZACH PARTSORDERID TEST: " + orderList[i].PartsOrderID.toString());
        console.log("NEW - ZACH ORDLINENO TEST: " + orderList[i].OrdLineNo);
        //LIST THAT GRABS CURRENT STATUS OF THE LINE WE ARE ON

        partsOrderIDArray = [orderList[i].PartsOrderID.toString()];
        partsOrderLineNoArray = [orderList[i].OrdLineNo.toString()];

        var statusFilter = "WHERE PartsOrderID = " + orderList[i].PartsOrderID + " AND OrdLineNo = " + orderList[i].OrdLineNo
        curStatusList = loadByListName("PW_GetCurrentStatus", statusFilter);
        curStatus = curStatusList[0].OrdLineStatus;
        console.log("ZACH CURRENT STAT: " + curStatus);

        if (curStatus === 'approved' || curStatus === 'Approved') { //only flip approved status orders to exported.
            sStatement('PW_UPDATE_PART_LINES_EXPORT_SYTELINE', [
                orderList[i].PartsOrderID,
                param_date,
                'exported',
                'In Process',
                orderList[i].OrdLineNo
            ]);
            sStatement('PW_ADD_STATUS_TO_TRACKER_PARTS_SYTELINE', [
                    sStatement('PW_GET_PART_STATE_CHG_ID')[0].ID,
                    orderList[i].OrdLineID.toString(),
                    orderList[i].OrdLineID.toString(),
                    'PartOrderLineItem',
                    'In Process',
                    'exported',
                    window[profile].USER_ID, param_date,
                    ''
                ]
            );
            console.log("STATUS SET TO EXPORTED FOR ORDER " + orderList[i].PartsOrderID.toString());
        } else {
            console.error("STATUS IS NOT APPROVED - CANNOT FLIP TO EXPORTED " + orderList[i].PartsOrderID.toString());
        }
    }

}

function allAreEqual(array) {
    if (!array.length) return true;
    return array.reduce(function (a, b) {
        return (a === b) ? a : ("false" + b);
    }) === array[0];
}

function constructStringUsingSearchBar(poid, search_value, idVal) {
    var string;

    // Check if search_value starts with "WP" or "WN"
    if (search_value.startsWith("WP") || search_value.startsWith("WN")) {
        console.log("starts with WP");
        // If true, cut off the first 3 characters
        search_value = search_value.substring(3);
        search_value = search_value.slice(0, -2);
    }

    if (search_value === "") {
        string = 'where (t1.PartsOrderID = "';
        var poids = poid.split(',');
        for (var i in poids) {
            if (i < poids.length - 1) {
                string += poids[i] + '" and t1.OrdLineStatus != "cancelled") or (t1.PartsOrderID = "';
            } else {
                string += poids[i] + '"  and t1.OrdLineStatus != "cancelled")';
            }
        }
    }
    if (search_value != "") {
        console.log("searched value!: " + search_value);
        string = 'where (t1.NCPartsCode Like "%' + search_value + '%" or t1.OrdLineEstShipDate Like "%' + search_value + '%" or t1.OrdLinePartNo Like "%' + search_value + '%" or t1.OrdLineModPartNo Like "%' + search_value + '%" or t1.Qty_Ordered Like "%' + search_value + '%" or t1.OrdLinePartDesc Like "%' + search_value + '%" or t1.ShipmentID Like "%' + search_value + '%" or t1.PartsOrderID Like "%' + search_value + '%") and t7.id = "' + idVal + '"';
    }

    return string;
}

function padPartsOrderID(ID, type, lineNo, shipNo) {
    var orderID = ID;
    var sNum = !shipNo ? '' : '-S' + shipNo;
    var line = !lineNo || lineNo == '0' ? '' : lineNo;
    var end;
    if (line < 10 && line !== '') {
        line = '-' + pad(lineNo, 2, 0);
        end = line + sNum;
    } else {
        end = '-' + lineNo;
    }
    if (end == '-') end = '';
    switch (type) {
        case 'parts_order':
            orderID = 'WP' + pad(ID, 7, 0) + end;
            return orderID;
        case 'n/c_parts':
            orderID = 'WN' + pad(ID, 7, 0) + end;
            return orderID;
        default:
            return orderID;
    }
}

function getTermsCode(code) {
    var ret = code;
    if (code == 'A0') {
        ret = 'P2';
    } else if (code == 'CIA') {
        ret = 'P1';
    }
    return ret;
}
