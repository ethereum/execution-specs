// Click Event Listner for toggle button
window.addEventListener("load", (e) => {
    const btn = document.getElementById("diff-toggle")
    if (btn){
        btn.addEventListener("click", toggleElements);
    }
})

// All diffs will have one of the below classes
const changeClassList = ["change-replaced", "change-replacement", "change-added", "change-removed"];
const changeClassString = "." + changeClassList.join(", .");

// The list of components to be scanned for diffs - selected by ID
const componentsList = [
    '#module-details > *',
    '#module-contents > *',
    '#package-details > *',
    '#package-contents > *', 
    '#subpackages',
    '#submodules',
    '#table-of-contents',
    '#introduction'
];
const componentsString = componentsList.join(", ");

function toggleElements() {

    // Check if the entire page is replaced. If yes, do nothing
    var fullPageReplaced = false;
    const pageElement = document.querySelector('span.target');
    if (changeClassList.some(r => pageElement.classList.value.includes(r))){
        fullPageReplaced = true;
    }

    // Do nothing if the full page is replaced
    if (!fullPageReplaced){
        // Examine the contents of the individual sections
        // Hide sections that do not have diffs in any of the children
        const all = document.querySelectorAll(componentsString);

        for (i=0; i < all.length; i++){
    
            const hasDiffs = childrenHaveDiffs(all[i]);
            if (!hasDiffs){
                all[i].classList.toggle("hideElement");
            };
        }
    }

    // Toggle button text depending on what is currently displayed
    const btn = document.getElementById('diff-toggle');
    if (btn.innerHTML === "Only Show Diffs") {
        btn.innerHTML = "Show All";
    } else {
        btn.innerHTML = "Only Show Diffs";
    }
}

function childrenHaveDiffs(element){

    if (changeClassList.some(r => element.classList.value.includes(r))){
        return true;
    } else {
        const children = element.querySelectorAll(changeClassString);
        if (children.length > 0){
                return true;
        }
    }

    return false;
}
