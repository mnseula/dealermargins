/*-------  Metadata -----
   *** Please do not touch this header ***

ID: 5f244222d4ecb3158019fdcc
NAME: Recalculate
CODE: RECALCULATE
RULE: EOS/SELECTED_ANSWER[="CALC"]#(EOS/SELECTED_QUESTION[="HIDE_DIO"]&EOS/SELECTED_ANSWER[="YES"])#EOS/SELECTED_ANSWER[="PRINT"]#EOS/SELECTED_ANSWER[="APPLY_DLRSHP_STGS"]
DOWNLOAD DATE: 2025-10-03T14:04:23.372Z

-------------------------*/

//get margin values and set as WINDOW variables (required by Calculate2021.js)

baseboat = getValue('MARGINS', 'BASE_BOAT');
window.baseboatmargin = (100 - baseboat) / 100;

engine = getValue('MARGINS', 'ENGINE');
window.enginemargin = (100 - engine) / 100;

options = getValue('MARGINS', 'OPTIONS');
window.optionmargin = (100 - options) / 100;

voldisc = getValue('MARGINS', 'VOL_DISC');
window.vol_disc = (100 - voldisc) / 100;

window.freight = getValue('FREIGHTPREP', 'FREIGHT');
window.prep = getValue('FREIGHTPREP', 'PREP');

// Also update MSRP-related variables for consistency
window.msrpMargin = (100 - baseboat) / 100;  // Typically uses base boat margin

// CPQ FIX: For CPQ boats, MSRP is a manufacturer price and must not collapse to dealer cost.
// When a dealer sets 0% margin, msrpMargin becomes 1.0, which makes MSRP = dealerCost.
// Protect against this by flooring msrpMargin at 0.78 (22%) for CPQ boats only.
// Legacy boats are unaffected.
if (window.isCPQBoat && window.msrpMargin >= 0.99) {
    window.msrpMargin = 0.78;
}

window.msrpVolume = 1.0;  // MSRP doesn't use volume discount
window.msrpLoyalty = 1.0; // Used for SV series special pricing

$('#included').remove(); //delete the included table if it exists so that removing the engine doesn't make 2.
boattable = [];

if (serialYear < 21) {
    Calculate();
} else {
    Calculate2021();
}


GenerateBoatTable(boattable);
