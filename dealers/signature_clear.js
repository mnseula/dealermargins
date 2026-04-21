// var year = loadByListName('Current_Model_Year')[0].MODEL_YEAR;
var year = '2023';

sigPanel = document.getElementById("sig_panel");

//$('#sig_panel').attr('data-clear','true');

$('#sig_panel').sketch().clear();
$('#sigimg').remove();  //keep the images from duplicating

deleteByListName('Dealer_Planner_Sig_Data', 'LIST/DEALER_NO[="' + eosNoTrimmed + '"] & LIST/FORECAST_MY[="'+ year +'"]');

reset('SIG', 'CLR');
