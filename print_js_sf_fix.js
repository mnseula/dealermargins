// MODIFIED SECTION FOR print.js
// Replace lines 640-651 with this code

    wsContents += "    <\/div>";
} else if (perfpkgid.length !== 0 && perfpkgid.length < 3 && perfpkgid !== undefined) {
    // Legacy boats: Use prfPkgs from EOS list
    
    // SF BOAT FIX: Match performance package to actual engine HP
    // For SF boats (2026 model using 2025 matrix), find package matching actual engine
    if (model && model.endsWith('SF') && window.boatoptions && window.boatoptions.length > 0) {
        console.log('SF Boat detected - checking for correct performance package match');
        
        // Find engine in boatoptions
        var engineItem = null;
        for (var i = 0; i < window.boatoptions.length; i++) {
            if (window.boatoptions[i].ItemMasterProdCat === 'EN7') {
                engineItem = window.boatoptions[i];
                break;
            }
        }
        
        if (engineItem && prfPkgs && prfPkgs.length > 0) {
            // Extract HP from engine description
            var engineHP = null;
            var engineDesc = engineItem.ItemDesc1 || '';
            console.log('SF Boat Fix: Engine description:', engineDesc);
            
            // Try "200HP" format first
            var hpMatch = engineDesc.match(/(\d+)\s*HP/i);
            if (hpMatch) {
                engineHP = parseInt(hpMatch[1]);
            } else {
                // Fallback: look for standalone numbers (100-600)
                var numMatch = engineDesc.match(/\b(1\d{2}|2\d{2}|3\d{2}|4\d{2}|5\d{2}|600)\b/);
                if (numMatch) {
                    engineHP = parseInt(numMatch[1]);
                }
            }
            
            // Find matching performance package
            if (engineHP) {
                console.log('SF Boat Fix: Looking for package with HP matching', engineHP);
                var matchingIndex = -1;
                for (var j = 0; j < prfPkgs.length; j++) {
                    var pkgHP = prfPkgs[j].MAX_HP;
                    if (pkgHP) {
                        var hpNumMatch = String(pkgHP).match(/\d+/);
                        if (hpNumMatch) {
                            var pkgHPNum = parseInt(hpNumMatch[0]);
                            if (pkgHPNum === engineHP) {
                                console.log('SF Boat Fix: Found matching package', prfPkgs[j].PKG_NAME, 'with HP', pkgHP);
                                matchingIndex = j;
                                break;
                            }
                        }
                    }
                }
                
                // Fallback: if no exact match, find lowest package whose MaxHP >= engineHP
                // e.g. 350HP engine on 25QXSBA maps to ESP at 500HP (no 350HP package exists)
                if (matchingIndex === -1) {
                    var bestIndex = -1;
                    var bestHP = Infinity;
                    for (var k = 0; k < prfPkgs.length; k++) {
                        var fbHP = prfPkgs[k].MAX_HP;
                        if (fbHP) {
                            var fbHPNum = parseInt(String(fbHP).match(/\d+/)[0]);
                            if (fbHPNum >= engineHP && fbHPNum < bestHP) {
                                bestHP = fbHPNum;
                                bestIndex = k;
                            }
                        }
                    }
                    if (bestIndex !== -1) {
                        console.log('SF Boat Fix: No exact match, using closest package', prfPkgs[bestIndex].PKG_NAME, 'with HP', prfPkgs[bestIndex].MAX_HP);
                        matchingIndex = bestIndex;
                    }
                }

                // Swap first package with matching one
                if (matchingIndex > 0) {
                    console.log('SF Boat Fix: Swapping package index 0 with index', matchingIndex);
                    var temp = prfPkgs[0];
                    prfPkgs[0] = prfPkgs[matchingIndex];
                    prfPkgs[matchingIndex] = temp;
                } else if (matchingIndex === 0) {
                    console.log('SF Boat Fix: First package already matches - no swap needed');
                } else {
                    console.log('SF Boat Fix: No suitable package found for HP', engineHP);
                }
            } else {
                console.log('SF Boat Fix: Could not extract HP from engine description');
            }
        } else {
            console.log('SF Boat Fix: No engine item found in boatoptions');
        }
    }
    // END SF BOAT FIX
    
    wsContents += "    <div class=\"title\">PERFORMANCE PACKAGE SPECS<\/div>";
    wsContents += "    <div id=\"perfpkgtbl\">";
    wsContents += "    <table width=\"355\" border=\"1\"><tbody><tr>";
    wsContents += "            <td colspan=\"4\" align=\"center\">" + prfPkgs[0].PKG_NAME + "<\/td><\/tr>";
    wsContents += "          <tr><td>Person Capacity<\/td><td>Hull Weight<\/td><td>Max HP<\/td><td>Pontoon Gauge<\/td><\/tr>";
    wsContents += "          <tr><td>" + prfPkgs[0].CAP + "<\/td><td>" + prfPkgs[0].WEIGHT + "<\/td><td>" + prfPkgs[0].MAX_HP + "<\/td><td>" + prfPkgs[0].PONT_GAUGE + "<\/td><\/tr>";
    wsContents += "        <\/tbody><\/table>";
    wsContents += "    <\/div>";
}
