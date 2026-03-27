var esq = getValue('EOS','SELECTED_QUESTION');
var esa = getValue('EOS','SELECTED_ANSWER');

eos.Core.on('detail', ['FLAG_SN/SN'], function () {
    var sn = getValue('FLAG_SN', 'SN');
    var flags = getFlags(sn);
    if (!flags.length) {
        return false;
    }
    flags = flags[0];
    if (flags.custom == '1') {
        setAnswer('FLAGS', 'CUSTOM');
    }
    if (flags.warranty_transfer == '1') {
        setAnswer('FLAGS', 'TRANSFER');
        $('#trans_elg').val('1');
    }
    if (flags.as_is_sale == '1') {
        setAnswer('FLAGS', 'AS_IS');
        sStatement('PW_ADJUST_EXT_ELG', [ sn ]);
        $('[id="ext_elg"]').val('0');
    }
    if (flags.rental == '1') {
        setAnswer('FLAGS', 'COMMERCIAL');
        sStatement('PW_ADJUST_EXT_ELG', [ sn ]);
        $('[id="ext_elg"]').val('0');
    }
    if (flags.moved_boat == '1') {
        setAnswer('FLAGS', 'MOVED');
    }
    if (flags.stolen == '1') {
        setAnswer('FLAGS', 'STOLEN');
        sStatement('PW_ADJUST_EXT_ELG', [ sn ]);
        $('[id="ext_elg"]').val('0');
    }
    if (flags.repossessed == '1') {
        setAnswer('FLAGS', 'REPO');
    }
    if (flags.special_notes == '1') {
        setAnswer('FLAGS', 'SPEC_NOTES');
    }
    if (flags.credit_hold == '1') {
        setAnswer('FLAGS', 'C_HOLD');
    }
    if (flags.custom_3_section_tube == '1') {
        setAnswer('FLAGS', '3SECTION');
    }
    if (flags.extended_warranty == '1') {
        setAnswer('FLAGS', 'EXT_WARR');
    }
    if (flags.factory_repair_boat == '1') {
        setAnswer('FLAGS', 'FACTORY');
    }
    if (flags.certified_pre_owned == '1') {
        setAnswer('FLAGS', 'CPO');
    }
    perm.checkForFlags();
    setValue('F_MODEL', 'MODEL', getValue('BOAT_INFO', 'MOD_NUM'));
});


var serialNo = getValue('FLAG_SN','SN');
var custom = hasAnswer('FLAGS','CUSTOM') ? 1 : 0;
var warr_xfer = hasAnswer('FLAGS','TRANSFER') ? 1 : 0;
var ext_warr = hasAnswer('FLAGS','EXT_WARR') ? 1 : 0;
var as_is = hasAnswer('FLAGS','AS_IS') ? 1 : 0;
var rental = hasAnswer('FLAGS','COMMERCIAL') ? 1 : 0;
var moved_boat = hasAnswer('FLAGS','MOVED') ? 1 : 0;
var stolen = hasAnswer('FLAGS','STOLEN') ? 1 : 0;
var repo = hasAnswer('FLAGS','REPO') ? 1 : 0;
var special_notes = hasAnswer('FLAGS','SPEC_NOTES') ? 1 : 0;
var credit_hold = hasAnswer('FLAGS','C_HOLD') ? 1 : 0;
var custom_3 = hasAnswer('FLAGS','3SECTION') ? 1 : 0;
var factory_repair = hasAnswer('FLAGS','FACTORY') ? 1 : 0;
var certified_pre_owned = hasAnswer('FLAGS','CPO') ? 1 : 0;

var params= [serialNo, custom, warr_xfer, ext_warr, as_is, rental, moved_boat,
             stolen, repo, special_notes, credit_hold, custom_3, factory_repair,
             certified_pre_owned];

if (esq == 'FLAG_BUTTON' && (esa == 'Y' || esa == 'ADD')){
    console.log(params);
    // check if it already has a entry in flags.
    var flags = getFlags(serialNo);
    if (flags.length) {
        console.log('Updating the flags file for SN:', serialNo);
        sStatement('UPDATE_BOAT_FLAGS', params);
    } else {
        console.log('Adding an entry to the flags file for SN:', serialNo);
        sStatement('INSERT_BOAT_FLAGS', params);
    }
    if (Number(warr_xfer)) $('#trans_elg').val('1');
    perm.checkForFlags();
    reset('FLAG_BUTTON');
}

function getFlags(sn){
    var results = sStatement('GET_BOAT_FLAGS', [sn]);
    return results;
}
