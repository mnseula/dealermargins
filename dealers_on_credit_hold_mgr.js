window.pwDlrsOnCreditHold = Object.freeze((function () {
    var allowedRoles = ['CustServiceMgr', 'WarrantyMgr', 'Maint', 'Admin', 'SuperUser'];
    var canManage = allowedRoles.indexOf(eos.user.role) !== -1;
    var imported = false;
    var dlrData = [];
    var dlrListData = [];
    function add(dlrNo) {
        sStatement('DLRS_ADD_ON_HOLD', [dlrNo, eos.user.username, eos.user.username]);
        pwDlrsOnCreditHold.refresh();
    }
    function remove(dlrNo) {
        sStatement('DLRS_REMOVE_ON_HOLD', [dlrNo]);
        pwDlrsOnCreditHold.refresh();
    }
    return {
        provideModal : function () {
            if (!dlrListData.length) {
                dlrListData = sStatement('DLRS_GET_ALL');
            }
            var options = dlrListData.map(function (d) {
                return '<option value="' + d.DlrNo + '">(' + d.DlrNo + ') ' + d.DealerName + '</option>';
            });
            var select = '<select id="dlr-on-hold-add"><option value=""> -- </option>' + options.join('') + '</select>';
            var question = [];
            question.push('<p>Below, select the dealer from the dropdown to add to On Hold list.  Then click <span style="font-weight:bold;">Add</span> to finish.</p>');
            question.push('<div style="display:block;">' + select + '</div>');
            question.push('<div style="display:none;" id="add-choice-err"><p style="color:red;">Please select a dealer from the list to continue</p></div>');
            var dlg = _two_option(
                'Add Dealer to On Hold List',
                question.join(''),
                function () {
                    var choice = $('#dlr-on-hold-add').val();
                    if (!choice) {
                        $('#add-choice-err').show();
                        setTimeout(function () {
                            $('#add-choice-err').fadeOut(300);
                        }, 2000);
                    } else {
                        pwDlrsOnCreditHold.add(choice);
                        dlg.hide();
                    }
                },
                null,
                'Add',
                'Cancel'
            );
            function _two_option(title, question, yes, no, yesTitle, noTitle) {
                yesTitle = yesTitle || 'Yes';
                noTitle = noTitle || 'No';
                var dlg = modal_dialog(
                    title,
                    question,
                    [{
                        name : 'yes',
                        title : yesTitle,
                        handler : function () {
                            yes();
                        },
                        classes : ['btn btn-eos-flat-primary']
                    }, {
                        name : 'cancel',
                        title : noTitle,
                        handler : function () {
                            dlg.modal('hide');
                            no instanceof Function ? no() : null;
                        },
                        classes : ['btn btn-eos-flat-plain']
                    }]
                );
                return dlg;
            }
        },
        add : function (dlrNo) {
            if (!canManage) { return; }
            return add(dlrNo);
        },
        remove : function (dlrNo) {
            if (!canManage) { return; }
            var confirmDelete = two_option(
                'Confirm Deletion',
                '<p style="margin:25px;">Click <span style="font-weight:bold;">OK</span> to confirm removing the On Hold status for Dealer Number ' + dlrNo + '</p>',
                function () { remove(dlrNo); },
                null,
                'OK',
                'Cancel'
            );
        },
        refresh : function () {
            dlrData = sStatement('DLRS_GET_ALL_ON_HOLD');
            this.drawTable();
        },
        import : function (data) {
            if (imported) {
                return;
            }
            dlrData = data.sort(function(a,b) {
                return a.DlrNo - b.DlrNo;
            });
            imported = true;
        },
        drawTable : function () {
            var table = [];
            table.push('<table class="table" id="on-hold-dlrs">');
            table.push('<caption><h4>Current List of On Hold Dealers</h4></caption>');
            table.push('<thead>');
            table.push('<tr>');
            table.push('<th>Dealer #</th>');
            table.push('<th>Dealer Name</th>');
            table.push('<th>Address</th>');
            table.push('<th>Date Added</th>');
            table.push('<th>Added By</th>');
            table.push('<th>Action</th>');
            table.push('</tr>');
            table.push('</thead>');
            table.push('<tbody>');
            dlrData.forEach(function (dlr) {
                var checked = dlr.isOnHold == '1';
                var id = 'chg-onhold-' + dlr.DlrNo;
                table.push('<tr data-dlrno="' + dlr.DlrNo + '">');
                table.push('<td>' + dlr.DlrNo + '</td>');
                table.push('<td>' + dlr.DealerName + '</td>');
                table.push('<td>' + dlr.Address + '</td>');
                table.push('<td>' + dlr.Date_added + '</td>');
                table.push('<td>' + dlr.Added_by + '</td>');
                table.push('<td>');
                table.push('<button class="btn btn-warning" id="' + id + '" name="chg-on-hold" type="button">Remove</button>');
                table.push('</td>');
                table.push('</tr>');
            });
            table.push('</tbody>');
            table.push('</table>');
            $('div[data-ref="CREDIT_HOLD_DLRS/TABLE"]').empty().append(table.join(''));
            this.setupEvents();
        },
        setupEvents : function () {
            $('button[name="chg-on-hold"]').on('click', function () {
                var el = $(this);
                var row = el.closest('tr');
                var dlrNo = row.data('dlrno');
                pwDlrsOnCreditHold.remove(dlrNo);
            });
        },
        isOnHold: function(dlrNo) {
            var re = /^0+/g;
            if (dlrNo) {
                dlrNo = dlrNo.toString().replace(re, '');
            }
            return dlrData.find(e => e.DlrNo.replace(re, '') == dlrNo);
        }
    };
})());

perm.funcs.sStatementAsync('DLRS_GET_ALL_ON_HOLD').done(function (dealers) {
    pwDlrsOnCreditHold.import(dealers);
    pwDlrsOnCreditHold.drawTable();
});
