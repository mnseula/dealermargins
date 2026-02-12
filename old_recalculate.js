/*-------  Metadata -----
   *** Please do not touch this header ***

ID: 5f244222d4ecb3158019fdcc
NAME: Recalculate
CODE: RECALCULATE
RULE: EOS/SELECTED_ANSWER[="CALC"]#(EOS/SELECTED_QUESTION[="HIDE_DIO"]&EOS/SELECTED_ANSWER[="YES"])#EOS/SELECTED_ANSWER[="PRINT"]#EOS/SELECTED_ANSWER[="APPLY_DLRSHP_STGS"]
DOWNLOAD DATE: 2025-10-03T14:04:23.372Z

-------------------------*/

//get margin values

baseboat = getValue('MARGINS', 'BASE_BOAT');
baseboatmargin = (100 - baseboat) / 100;
engine = getValue('MARGINS', 'ENGINE');
enginemargin = (100 - engine) / 100;
options = getValue('MARGINS', 'OPTIONS');
optionmargin = (100 - options) / 100;
freight = getValue('FREIGHTPREP', 'FREIGHT');
prep = getValue('FREIGHTPREP', 'PREP');

$('#included').remove(); //delete the included table if it exists so that removing the engine doesn't make 2.
boattable = [];

if (serialYear < 21) {
    Calculate();
} else {
    Calculate2021();
}


GenerateBoatTable(boattable);
