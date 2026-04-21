var selected_rep = getAnswer('REP');
console.log(selected_rep);

rep_rec = selected_rep.split('/');
rep_answer = rep_rec[1];

rep_name = getUdp('REP/' + rep_answer,'tree_text');

setValue('HIDE','REP_SELECTION',rep_name);

//var filterString = 'WHERE SALESPERSON = \'{HIDE/REP_SELECTION}\'';
//var filterString = "WHERE SALESPERSON = " + "'" + rep_name + "'";
var filterString = "WHERE SALESPERSON = " + "'" + rep_name + "' AND CustomerTypeDesc='Active' OR cus_type_cd='101'";
var emptyfilterString = "WHERE CustomerTypeDesc='Active'";

if(rep_name!== 'ALL REPS'){
    setValue('HIDE','FILTER',filterString);
}
else{
    reset('HIDE','FILTER');
    setValue('HIDE','FILTER',emptyfilterString);
}
