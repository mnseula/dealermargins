console.log("WARRANTY PARTS EXPORTED!");

// get all the data from the filter inputs
var warr_status = $('#warranty_status').val() !== '' ? '%' + $('#warranty_status').val() + '%' : '%%';
var warr_sn = hasAnswer('WARR_FILTER', 'SN') ? '%' + getValue('WARR_FILTER', 'SN') + '%' : '%%';
var warr_cust = hasAnswer('WARR_FILTER', 'CUST_NAME') ? '%' + getValue('WARR_FILTER', 'CUST_NAME') + '%' : '%%';
var warr_claimNo = hasAnswer('WARR_FILTER', 'CLAIM_NUM') ? '%' + getValue('WARR_FILTER', 'CLAIM_NUM') + '%' : '%%';
var warr_dealer_ref = hasAnswer('WARR_FILTER', 'DEALER_REF') ? '%' + getValue('WARR_FILTER', 'DEALER_REF') + '%' : '%%';
var warr_dName = hasAnswer('WARR_FILTER', 'D_NAME') ?  getValue('WARR_FILTER', 'D_NAME') : '%%';
var other_dname = '%%';
var date1 = hasAnswer('WARR_FILTER','DATE1') ? getValue('WARR_FILTER','DATE1').replace(/['/']/g,'-') : '01-01-1901';
var date2 = hasAnswer('WARR_FILTER','DATE2') ? getValue('WARR_FILTER','DATE2').replace(/['/']/g,'-') : '12-31-9999';
var invalidDates = (date1 == '01-01-1901' && date2 == '12-31-9999');
var oStatus = warr_status;

if (contains(warr_claimNo,'WW')) {
    warr_claimNo = '%' + Number(warr_claimNo.replace(/["WW","%"]/g,'')) + '%';
    other_dname = '%%';
    console.log(warr_claimNo);
}

if (!$.isNumeric(warr_dName) && warr_dName !== '%%') {
    warr_dName = '%' + warr_dName + '%';
    other_dname = '%%';
} else if ($.isNumeric(warr_dName)) {
    other_dname = Number(warr_dName);
    warr_dName = '%' + warr_dName.padStart(8,'0') + '%';
}

if (warr_status == '%processed%') {
    oStatus = '%completed%';
}

var params = [warr_status, warr_sn, warr_cust, warr_claimNo, warr_dealer_ref, warr_dName, other_dname, oStatus];
var paramsDate = [warr_status, warr_sn, warr_cust, warr_claimNo, warr_dealer_ref, warr_dName, other_dname, oStatus, date1, date2];

var warranty_data = [];

warranty_data = sStatement('GET_WARRANTY_CLAIMS', params);

//Need to generate the XML now that we have the conditional data. Generate both the header and line items for EACH row.
//Has been determined that only one file should be produced containing all the resulting parts orders 10/30/2023

//XML Static Header

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

for (const item of warranty_data) {

    if(last_processed == item.PartsOrderID) {
        continue;
    }

    var filter2 = "WHERE (t1.PartsOrderID = '";
    filter2 += item.PartsOrderID;
    filter2 += "')";


    //Get panel color and boat model from serial number
    var contentFilter = "WHERE Boat_SerialNo = '";
    contentFilter += item.OrdHdrBoatSerialNo;
    contentFilter += "'";

    //Use filter to get the panel color from the Serial Master
    if(item.OrdHdrBoatSerialNo !== "StockParts") {
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
        } catch(error) {
            console.error("BOAT MODEL DOES NOT EXIST FOR THIS SERIAL NO");
        }

    }

    //If a stock part, clear the panel color
    if(item.OrdHdrBoatSerialNo == "StockParts") {
        panel_color = "";
    }

    //Get international flags given serial number
     var international = "";
    var international_type = "";
    var dealernum_filter = "";

    //Only Charge parts can be international... need to leave no charge parts blank
    if(item.OrdHdrClaimType == "parts_order") {
        dealernum_filter = "WHERE DlrNo = '";
        dealernum_filter += item.OrdHdrDealerNo;
        dealernum_filter += "'";

        console.log("DEALER FILTER: "+dealernum_filter);

        var international_data = loadList("65a9786e09525761715bf2a6", dealernum_filter);

        console.log("INTERNATIONAL DATA: "+international_data[0]);

        try{
           international = international_data[0].International;
        } catch(error) {
            console.error("INTERNATIONAL DATA ERROR")
        }

        try{
           international_type = international_data[0].InternationalType;
        } catch(error) {
            console.error("INTERNATIONAL TYPE DATA ERROR")
        }

    }

    xmlContent += `<Test_Verenia_Boat>
                    <Test_Verenia_BoatHeader>
                        <AlternateDocumentID>
                            <ID>`+item.claim_number+`</ID>
                        </AlternateDocumentID>
                        <ShipToParty>
                            <PartyIDs>
                                <ID>`+item.OrdHdrDealerNo+`~0</ID>
                            </PartyIDs>
                        </ShipToParty>
                        <CarrierParty>
                            <PartyIDs>
                                <ID>WW</ID>
                            </PartyIDs>
                        </CarrierParty>
                        <PaymentTerm>
                            <Term>
                                <ID>WA</ID>
                            </Term>
                        </PaymentTerm>
                        <PurchaseOrderReference>
                            <DocumentID>
                                <ID>`+item.OrdHdrDealerRefNo+`</ID>
                            </DocumentID>
                        </PurchaseOrderReference>
                        <OrderDateTime>`+item.HdrCreateDate+`</OrderDateTime>
                        <ue_BennOrderType>WARRANTY</ue_BennOrderType>
                        <ue_EngineForBoat/>
                        <ue_PreSold/>
                        <ue_ShowBoat/>
                        <ue_RentalBoat/>
                        <PanelColor>`+panel_color+`</PanelColor>
                        <BaseVinyl/>
                        <BuildComments>`+item.OrdHdrSpecInstructions+`</BuildComments>
                        <DealerComments>`+item.OrdHdrDealerComments+`</DealerComments>
                        <BoatModel>`+boat_model+`</BoatModel>
                        <BoatSerialNo>`+item.OrdHdrBoatSerialNo+`</BoatSerialNo>
                        <ShippingMethod>WW</ShippingMethod>
                        <BennTermsCode>WA</BennTermsCode>
                        <ue_International></ue_International>
                        <ue_InternationalType></ue_InternationalType>
                        <ue_SpecialInstructions/>
                        <ue_Reason/>
                        <ue_LoadNumber/>
                        <ue_BennOwned></ue_BennOwned>
                        <ue_CustTrackingEmail></ue_CustTrackingEmail>
                    </Test_Verenia_BoatHeader>
                    `


                    //Need to loop through the claim line items

                    var claimlines = [];

                    var filterarray = [item.PartsOrderID];

                    console.log("ZACH PARTSORDERID: "+item.PartsOrderID);

                    //Set the header to Complete so it falls off the page

                    sStatement('PW_UPDATE_WARR_AFTER_EXPORT', [item.PartsOrderID, 'Completed','completed', getDate()]);
                    sStatement('PW_WARR_LAST_STATUS_U', [item.PartsOrderID, 'Completed','completed', getDate()]);
                    sStatement('PW_ADD_WARR_HEADER_STATUS', [item.PartsOrderID, item.PartsOrderID, '', '',
                    'PartsWarrantyOrder', 'Completed', 'completed', window[profile].USER_ID, getDate(), '']);

                    //Grab the warranty claim lines for the XML

                    claimlines = sStatement("WARRANTY_LINES", filterarray);

                    console.log("ZACH CLAIMS: "+claimlines.toString())

                    if(claimlines.length < 1) { //no line items for some reason
                        //close the header
                        xmlContent += '</Test_Verenia_Boat>';
                    }

                    for (var i = 0; i < claimlines.length; i++) {

                         var lastrecord = 0;
                         if (i == claimlines.length - 1 || claimlines.length == 1) { //to get the last line item out of the group
                             lastrecord = 1;
                         }

                         //Get the item number based on the type of claim
                         var lineitemnum = "";

                         if( claimlines[i].WCLI_LineType === 'parts') {
                             lineitemnum = "WWPARTS";
                         } else if(claimlines[i].WCLI_LineType === 'labor') {
                            lineitemnum = "WWLABOR";
                         } else if (claimlines[i].WCLI_LineType === 'sublet') {
                             lineitemnum = "WWSUBLET";
                         }

                         //Calculate Cost and Qty
                        var cost = 0;
                        var qty = 1;

                        if(claimlines[i].WCLI_LineType === 'labor'){
                            cost = + (claimlines[i].WCLI_AltLaborRate || claimlines[i].WCLI_LaborRate) * +(claimlines[i].WCLI_AdjLaborHours || claimlines[i].WCLI_LaborHours);
                        } else if (claimlines[i].WCLI_LineType === 'sublet') {
                            //cost = +claimlines[i].WCLI_SubletCost;
                            NumCost = claimlines[i].WCLI_SubletCost.replace(/,/g, ''); // Remove commas in case the cost is something like '13,999.00' otherwise it will read it as a string
                            cost = +NumCost; // Add the converted value to the cost.
                        } else if (claimlines[i].WCLI_LineType === 'parts') {
                            cost = +claimlines[i].WCLI_TotalCost;
                        }
                        if (!cost || !$.isNumeric(cost)) {
                            cost = 0;
                            qty = 0;
                        } else {
                            cost = (cost * -1).toFixed(2);
                        }

                        qty = 1; //Qty for a warranty claim should always be 1

                        var line_no = claimlines[i].WCLI_LineNo;

                        var line_no_full = item.claim_number + "-0" + line_no;


                        xmlContent += `<Test_Verenia_BoatLine>
                                            <Item>
                                                <ItemID>
                                                    <ID>${lineitemnum}</ID>
                                                </ItemID>
                                            </Item>
                                            <Quantity unitCode="EA">${qty}</Quantity>
                                            <WarrantyClaimNo>${line_no_full}</WarrantyClaimNo>
                                            <WarrantyClaimLineID>${claimlines[i].WCLItemID}</WarrantyClaimLineID>
                                            <UnitPrice>${cost}</UnitPrice>
                                            <ShippingInstructions/>
                                            <PartsWebOrderNo/>
                                            <ue_LastRecord>`+lastrecord+`</ue_LastRecord>
                                            <ue_Dealer_Comments>${item.OrdHdrDealerComments}</ue_Dealer_Comments>
                                            <ue_Details_Sublet_Comments>${claimlines[i].WCLI_SubletComments}</ue_Details_Sublet_Comments>
                                            <ue_Item_Desc></ue_Item_Desc>
                                            <ue_RGA></ue_RGA>
                                            <ue_RGA_Date></ue_RGA_Date>
                                            <ue_Estimated_Shipping_Date></ue_Estimated_Shipping_Date>
                                            <ue_TransactionId></ue_TransactionId>
                                            <ue_Alternate_Shipping_Location></ue_Alternate_Shipping_Location>
                                        </Test_Verenia_BoatLine>`
                        if(i == claimlines.length - 1) {
                            xmlContent += `</Test_Verenia_Boat>`;
                        }
                    }
                    last_processed = item.PartsOrderID;
                    xmlContent = xmlContent.replace(/&/g, '&amp;');

                    /*<Test_Verenia_BoatLine>
                        <Item>
                            <ItemID>
                                <ID>`+item_number+`</ID>
                            </ItemID>
                        </Item>
                        <Quantity unitCode="EA">1</Quantity>
                        <WarrantyClaimNo>`+item.claim_number+`</WarrantyClaimNo>
                        <WarrantyClaimLineID>`+item.WCLItemID+`</WarrantyClaimLineID>
                        <UnitPrice>`+cost+`</UnitPrice>
                        <ShippingInstructions/>
                        <PartsWebOrderNo/>
                        <ue_LastRecord></ue_LastRecord>

                    </Test_Verenia_BoatLine>
                </Test_Verenia_Boat>
                 */
}

var xmlFooter = `</DataArea>
                </ProcessTest_Verenia_Boat>
                `;

xmlContent += xmlFooter;

console.log(xmlContent);

var today = new Date();
var date = today.getFullYear()+'_'+(today.getMonth()+1)+'_'+today.getDate();
var time = today.getHours() + "_" + today.getMinutes();
var dateTime = date+' '+time;

saveXMLToFile(xmlContent, "sytelineExport_"+dateTime);

//Zach 10/31/2023 Happy Halloween! :)
function saveXMLToFile(xmlContent, filename) {
  try {
    var xmlBlob = new Blob([xmlContent], { type: 'application/xml' });
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

function allAreEqual(array){
    if(!array.length) return true;
    return array.reduce(function(a, b){return (a === b)?a:("false"+b);}) === array[0];
}

console.log(warranty_data);
