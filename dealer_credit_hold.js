// Admin tab — Dealer Credit Hold management
// EOS form needs:
//   Question: HOLD_DLR_NO  (text input — dealer number to look up / act on)
//   Question: HOLD_ACTION  (button group — answers: ADD, REMOVE, REFRESH)
//   Question: HOLD_STATUS  (display — shows current hold state for looked-up dealer)
//
// sStatements required (see dealer_credit_hold_statements.sql):
//   GET_DEALER_HOLD_STATUS, GET_ALL_HELD_DEALERS, SET_DEALER_ON_HOLD, REMOVE_DEALER_HOLD

var esq = getValue('EOS', 'SELECTED_QUESTION');
var esa = getValue('EOS', 'SELECTED_ANSWER');
var currentUser = getValue('EOS', 'USER');

// ─── When admin types a dealer number, look up hold status immediately ────────
eos.Core.on('detail', ['HOLD_DLR_NO/DLR_NO'], function () {
    var dlrNo = getValue('HOLD_DLR_NO', 'DLR_NO');
    if (!dlrNo) {
        reset('HOLD_STATUS');
        return;
    }

    var rows = sStatement('GET_DEALER_HOLD_STATUS', [dlrNo]);
    if (!rows || !rows.length) {
        reset('HOLD_STATUS');
        return;
    }

    var rec = rows[0];
    if (rec.Is_on_hold == '1') {
        setAnswer('HOLD_STATUS', 'ON_HOLD');
        console.log('Dealer', dlrNo, rec.DealerName, 'is ON HOLD — added by', rec.Added_by, 'on', rec.Date_added);
    } else {
        setAnswer('HOLD_STATUS', 'NOT_HELD');
        console.log('Dealer', dlrNo, rec.DealerName, 'hold was removed by', rec.Updated_by, 'on', rec.Date_updated);
    }
});

// ─── Add hold button ──────────────────────────────────────────────────────────
if (esq == 'HOLD_ACTION' && esa == 'ADD') {
    var dlrNo = getValue('HOLD_DLR_NO', 'DLR_NO');
    if (!dlrNo) {
        alert('Enter a dealer number first.');
    } else {
        var check = sStatement('GET_DEALER_HOLD_STATUS', [dlrNo]);
        if (check.length && check[0].Is_on_hold == '1') {
            alert('Dealer ' + dlrNo + ' is already on credit hold.');
        } else {
            sStatement('SET_DEALER_ON_HOLD', [dlrNo, currentUser]);
            setAnswer('HOLD_STATUS', 'ON_HOLD');
            console.log('Credit hold ADDED for dealer', dlrNo, 'by', currentUser);
        }
    }
    reset('HOLD_ACTION');
}

// ─── Remove hold button ───────────────────────────────────────────────────────
if (esq == 'HOLD_ACTION' && esa == 'REMOVE') {
    var dlrNo = getValue('HOLD_DLR_NO', 'DLR_NO');
    if (!dlrNo) {
        alert('Enter a dealer number first.');
    } else {
        var check = sStatement('GET_DEALER_HOLD_STATUS', [dlrNo]);
        if (!check.length || check[0].Is_on_hold != '1') {
            alert('Dealer ' + dlrNo + ' is not currently on credit hold.');
        } else {
            sStatement('REMOVE_DEALER_HOLD', [dlrNo, currentUser]);
            setAnswer('HOLD_STATUS', 'NOT_HELD');
            console.log('Credit hold REMOVED for dealer', dlrNo, 'by', currentUser);
        }
    }
    reset('HOLD_ACTION');
}

// ─── Refresh / load all held dealers ─────────────────────────────────────────
if (esq == 'HOLD_ACTION' && esa == 'REFRESH') {
    var held = sStatement('GET_ALL_HELD_DEALERS', []);
    console.log('All dealers currently on credit hold:', held.length);
    held.forEach(function (r) {
        console.log(' -', r.DlrNo, r.DealerName, '| added by', r.Added_by, 'on', r.Date_added);
    });
    reset('HOLD_ACTION');
}
