setTimeout(run, 10);

function run() {
    try {
        var dlrs = perm.data.dlrs.view()[0];
        var drop = [];
        drop.push('<select id="parts-rep" multiple>');
        var map = dlrs.reduce(function(acc, curr) {
            var rep = curr.SalesPerson;
            var repNo = curr.SalesPersonNo;
            if (!acc[repNo]) {
                drop.push('<option value="' + repNo + '">' + rep + '</option>');
                acc[repNo] = {
                    rep: rep,
                    repNo: repNo
                };
            }
            return acc;
        }, {});
        drop.push('</select>');
        $('input[data-ref="PART_INFO/SALES_REP"]').replaceWith(drop.join(''));
        $('#parts-rep')
        .css({display: 'none'})
        .multiselect({
            numberDisplayed: 0
        })
        .on('change', function() {
            var val = $(this).val();
            if (val) {
                setValue('PART_INFO','SALES_REP', val.join(','));
            } else {
                reset('PART_INFO','SALES_REP');
            }
        });
    } catch (e) {
        console.log('Dealers not ready', e.message);
        setTimeout(run, 100);
    }
}
