/**
 * Z-Index Debugging Tools for Gradio Dropdowns
 * Run these commands in browser console to diagnose dropdown layering issues
 */

// 1. Find all dropdown elements and their computed z-index values
function debugDropdownElements() {
    console.log("=== DROPDOWN ELEMENTS DEBUG ===");

    const selectors = [
        '.gr-dropdown',
        '.gr-dropdown .dropdown',
        '.gr-dropdown .dropdown-menu',
        '.gr-dropdown .dropdown-content',
        'div[data-testid="dropdown"]',
        'div[role="listbox"]',
        'div[role="menu"]'
    ];

    selectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        console.log(`\n${selector}:`, elements.length);

        elements.forEach((el, index) => {
            const computed = window.getComputedStyle(el);
            console.log(`  [${index}] z-index: ${computed.zIndex}, position: ${computed.position}, display: ${computed.display}`);
            console.log(`      element:`, el);
        });
    });
}

// 2. Find elements with high z-index that might be blocking
function findHighZIndexElements() {
    console.log("\n=== HIGH Z-INDEX ELEMENTS ===");

    const allElements = document.querySelectorAll('*');
    const highZElements = [];

    allElements.forEach(el => {
        const computed = window.getComputedStyle(el);
        const zIndex = parseInt(computed.zIndex) || 0;

        if (zIndex > 100) {
            highZElements.push({
                element: el,
                zIndex: zIndex,
                position: computed.position,
                className: el.className,
                tagName: el.tagName
            });
        }
    });

    // Sort by z-index descending
    highZElements.sort((a, b) => b.zIndex - a.zIndex);

    console.log("Elements with z-index > 100:");
    highZElements.forEach(item => {
        console.log(`z-index: ${item.zIndex}, ${item.tagName}.${item.className}`, item.element);
    });
}

// 3. Highlight dropdown elements visually
function highlightDropdowns(color = 'red') {
    console.log(`\n=== HIGHLIGHTING DROPDOWNS (${color}) ===`);

    const dropdowns = document.querySelectorAll('.gr-dropdown, div[data-testid="dropdown"]');

    dropdowns.forEach(dropdown => {
        // Highlight the dropdown container
        dropdown.style.border = `3px solid ${color}`;
        dropdown.style.outline = `2px dashed ${color === 'red' ? 'blue' : 'red'}`;

        // Find and highlight dropdown menu
        const menu = dropdown.querySelector('.dropdown-menu, .dropdown-content, div[role="listbox"]');
        if (menu) {
            menu.style.border = `3px solid ${color === 'red' ? 'green' : 'orange'}`;
            menu.style.outline = `2px solid ${color === 'red' ? 'purple' : 'pink'}`;
        }
    });

    console.log(`Highlighted ${dropdowns.length} dropdown containers`);
}

// 4. Force fix z-index issues
function forceFixZIndex() {
    console.log("\n=== APPLYING EMERGENCY Z-INDEX FIXES ===");

    // Create high-priority style element
    const style = document.createElement('style');
    style.id = 'emergency-zindex-fix';

    style.textContent = `
        /* Emergency z-index fixes */
        .gr-dropdown,
        .gr-dropdown .dropdown,
        div[data-testid="dropdown"] {
            z-index: 999999 !important;
            position: relative !important;
        }

        .gr-dropdown .dropdown-menu,
        .gr-dropdown .dropdown-content,
        .gr-dropdown div[role="listbox"],
        div[data-testid="dropdown"] div[role="listbox"] {
            z-index: 999999 !important;
            position: absolute !important;
            background: white !important;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3) !important;
            border: 2px solid #007bff !important;
            border-radius: 8px !important;
            transform: translateZ(0) !important;
        }

        .gr-dropdown div[role="option"],
        div[data-testid="dropdown"] div[role="option"] {
            z-index: 999999 !important;
            background: white !important;
            color: black !important;
            padding: 8px 12px !important;
        }

        .gr-dropdown div[role="option"]:hover,
        div[data-testid="dropdown"] div[role="option"]:hover {
            background: #f0f0f0 !important;
        }
    `;

    // Remove existing fix if present
    const existing = document.getElementById('emergency-zindex-fix');
    if (existing) existing.remove();

    document.head.appendChild(style);
    console.log("Emergency z-index fixes applied!");
}

// 5. Test dropdown interaction
function testDropdownInteraction() {
    console.log("\n=== TESTING DROPDOWN INTERACTION ===");

    const dropdowns = document.querySelectorAll('.gr-dropdown select, .gr-dropdown button');

    dropdowns.forEach((dropdown, index) => {
        console.log(`Testing dropdown ${index}:`, dropdown);

        // Try to trigger dropdown open
        dropdown.click();

        setTimeout(() => {
            const menu = document.querySelector('.gr-dropdown .dropdown-menu:not([style*="display: none"]), .gr-dropdown div[role="listbox"]');
            if (menu) {
                const rect = menu.getBoundingClientRect();
                console.log(`  Dropdown menu visible: width=${rect.width}, height=${rect.height}, top=${rect.top}, left=${rect.left}`);

                // Check if it's being clipped
                if (rect.bottom > window.innerHeight || rect.right > window.innerWidth) {
                    console.warn(`  WARNING: Dropdown extends beyond viewport!`);
                }

                // Check for overlapping elements
                const elementBelow = document.elementFromPoint(rect.left + rect.width/2, rect.bottom + 10);
                if (elementBelow && !menu.contains(elementBelow)) {
                    console.warn(`  WARNING: Element below dropdown may be blocking:`, elementBelow);
                }
            } else {
                console.log(`  No visible dropdown menu found`);
            }
        }, 100);
    });
}

// 6. Run complete diagnostic
function runCompleteDropdownDiagnostic() {
    console.clear();
    console.log("🔍 GRADIO DROPDOWN Z-INDEX DIAGNOSTIC SUITE");
    console.log("============================================");

    debugDropdownElements();
    findHighZIndexElements();
    highlightDropdowns();
    testDropdownInteraction();

    console.log("\n💡 NEXT STEPS:");
    console.log("1. Run forceFixZIndex() if dropdowns still don't work");
    console.log("2. Check browser DevTools Elements tab for stacking context");
    console.log("3. Look for parent elements with 'overflow: hidden'");
    console.log("4. Try highlightDropdowns('blue') to change highlighting");
}

// Auto-run diagnostic when script loads
if (typeof window !== 'undefined') {
    console.log("🚀 Z-Index debugging tools loaded!");
    console.log("📋 Available functions:");
    console.log("   - runCompleteDropdownDiagnostic()");
    console.log("   - debugDropdownElements()");
    console.log("   - findHighZIndexElements()");
    console.log("   - highlightDropdowns(color)");
    console.log("   - forceFixZIndex()");
    console.log("   - testDropdownInteraction()");
    console.log("");
    console.log("🎯 Run runCompleteDropdownDiagnostic() to start debugging!");
}
