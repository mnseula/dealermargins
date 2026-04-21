var loggedinuser = getValue('EOS','EMAIL');
console.log(loggedinuser);
 $('div[data-ref="ALL_DLR_TBL/ALL_DLR_TBL"]').children('div').remove();
//Brandon Call

if(loggedinuser ==='brandoncall@msn.com' || loggedinuser === 'jonathanfizer@yahoo.com'){     setAnswer('REP','BRANDON_CALL');   }

//Dockside
if (loggedinuser === 'mspencer@nexicom.net' || loggedinuser === 'jim.lacey2@simpatico.ca'){ setAnswer('REP','DOCKSIDE_GROUP');   }

//Marine Distributors

if(loggedinuser ==='mdidanielh@gmail.com' || loggedinuser ==='dmartin041@gmail.com' || loggedinuser ==='ghawkinson7@gmail.com' || loggedinuser === 'robert@marinedealerssolutions.com'){
    setAnswer('REP','MARINE_DISTRIBUTORS');
}

//Pat Call

if(loggedinuser ==='jcall@benningtonmarine.com' || loggedinuser ==='pcall@benningtonmarine.com'  ){     setAnswer('REP','PAT_CALL');   }

//Tim Payne

if(loggedinuser ==='tpayne4m@gmail.com' ){     setAnswer('REP','TIM_PAYNE');   }

//Tom Cooper

if(loggedinuser ==='tcooper@benningtonmarine.com'){     setAnswer('REP','TOM_COOPER');   }

//Susan Buff

if(loggedinuser ==='nauticalbuff2@gmail.com' || loggedinuser ==='rgood@benningtonmarine.com'){     setAnswer('REP','NAUTICAL_BUFFS');   }

//Sam Girten

if(loggedinuser ==='sgirten@benningtonmarine.com'){     setAnswer('REP','SAM_GIRTEN');   }

//Mark Skeen

if(loggedinuser ==='mskeen@benningtonmarine.com'){     setAnswer('REP','MARK_SKEEN');   }
