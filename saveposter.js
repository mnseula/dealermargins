console.log('Saving Poster');

var previouslySaved = sStatement('SEL_ONE_BOAT_FLYER',[serial]).length;
var hasPreviousPrices = sStatement('SEL_ONE_BOAT_FLYER_PRICING',[serial]).length;

var data = [];

var i = 1; //order

$('#sortable li').each(function (index) {
    var part = $(this).context.lastChild.id;
    var descTB = 'tb' + $(this).context.lastChild.id;
    var desc = $('input:text[name="' + descTB  + '"]').val();
    var state = $(this).context.className;
    var hide = 0;

    console.log(state);

     if(state.substring(0,14) == 'ui-state-focus'){
        hide = 0;
    }
    else if(state.substring(0,14) == 'ui-state-error'){
        hide = 1;
    }
    else if(desc = 'Limited time value series discount') {
        hide = 1;
    }

    data = [serial, part, desc, i, hide];

    if(previouslySaved === 0){
         sStatement('INS_FLYER_OPTIONS',data);
    }

    else{
        console.log('Updating');
        sStatement('UPD_FLYER_OPTIONS',data);
    }
    i++;
});

//Save Pricing, Title and Font Size

var title = getValue('PRICING','FLYER_TITLE');
var msrp = getValue('PRICING','FLYER_MSRP');
var discount = getValue('PRICING','FLYER_DISCOUNT');
var final = getValue('PRICING','FLYER_FINAL_PRICE');
var font = getValue('PRICING','FONT_SIZE');

var power = document.getElementById('engine').value;
var cap = document.getElementById('cap').value;
var fuel = document.getElementById('fuel').value;

if(!isAnswered('PERF_LOGOS')){
    setAnswer('PERF_LOGOS','NONE');
}

if(isAnswered('POSTER_IMG')){
var poster = getAnswer('POSTER_IMG').split('/')[1];
}
else{
    var poster = "";
}

if(!isAnswered('PERF_LOGOS')){
    setAnswer('PERF_LOGOS','NONE');
}
var perfLogoAnswer = getAnswer('PERF_LOGOS');
var perflogo = (perfLogoAnswer && perfLogoAnswer.includes('/')) ? perfLogoAnswer.split('/')[1] : '';
var printoptions = getAnswer('COLOR');  // Store full answer path, not just the part after '/'
//var printoptions = ""; !!!!!!!!!!!!! CHANGE TO THIS ONCE THE PORTRAIT AND LANDSCAPE CHANGE COMES OUT!

var dlr_img_url = getValue('DLR_IMG','DLR_IMG_URL');

var pricingdata = [serial,msrp,discount,final,dlr_img_url,title,font,perflogo,printoptions,power,cap,fuel,poster];
console.log(pricingdata);

 if(previouslySaved === 0 || hasPreviousPrices === 0){
         console.log('Insert Into Prices');
         sStatement('INS_FLYER_PRICING',pricingdata);
    }

    else{
        console.log('Updating');
        sStatement('UPD_FLYER_PRICING',pricingdata);
    }
