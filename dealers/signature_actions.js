//var year = loadByListName('Current_Model_Year')[0].MODEL_YEAR;
var year = '2024';

sigPanel = document.getElementById("sig_panel");
var sig = sigPanel.toDataURL("image/png");
setValue('HIDE', 'SIG_DATA', sig);

var sigdata = [eosNoTrimmed, year, sig];
// Remove existing record
deleteByListName('Dealer_Planner_Sig_Data', 'LIST/DEALER_NO[="' + eosNoTrimmed + '"] & LIST/FORECAST_MY[="'+ year +'"]');
addByListName('Dealer_Planner_Sig_Data', sigdata);

reset('SIG', 'SAVE');
