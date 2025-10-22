// Config
const FILTER_INPUT_SELECTOR = ".custom_dt_filter";
const FILTER_SEARCH_SELECTOR = "#custom_dt_search";
let table;
const ICON_COLUMN_FILTER =
  '<span class="twemoji"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M17 16.88c.56 0 1 .44 1 1s-.44 1-1 1-1-.45-1-1 .44-1 1-1m0-3c2.73 0 5.06 1.66 6 4-.94 2.34-3.27 4-6 4s-5.06-1.66-6-4c.94-2.34 3.27-4 6-4m0 1.5a2.5 2.5 0 0 0 0 5 2.5 2.5 0 0 0 0-5M18 3H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h5.42c-.16-.32-.3-.66-.42-1 .12-.34.26-.68.42-1H4v-4h6v2.97c.55-.86 1.23-1.6 2-2.21V13h1.15c1.16-.64 2.47-1 3.85-1 1.06 0 2.07.21 3 .59V5c0-1.1-.9-2-2-2m-8 8H4V7h6v4m8 0h-6V7h6v4Z"></path></svg></span>';

// This script is used both within mkdocs and in standalone html files.
// As such, a uniform listener to page load event is required.
// The snippet below uses mkdocs subscription if present otherwise jquery is used
// as a fallback.
// see: https://github.com/squidfunk/mkdocs-material/issues/5816#issuecomment-1667654560

if (typeof document$ == "undefined") {
  document$ = {};
  document$.subscribe = $(document).ready;
}

document$.subscribe(() => {
  initDataTable();

  if (table) {
    // Listen for changes to filters
    $(FILTER_INPUT_SELECTOR).on("change", filterRows);

    $(FILTER_SEARCH_SELECTOR).on("input", filterRows);

    // Apply preselected filters (if present) on page load
    filterRows();

    // Listen for copy event
    listenForClipboardCopy();

    // Style native dataTable buttons
    $(".dt-buttons").detach().appendTo(".panel_row.filters");
    $(".buttons-collection").prepend(ICON_COLUMN_FILTER);
  }

  // Setup up select 2
  $(`select${FILTER_INPUT_SELECTOR}`).select2();
});

const initDataTable = () => {
  // Only pages where a table is present.
  if (!$("#test_table").length) return false;

  // Setup DataTable plugin
  // https://datatables.net/reference/api/
  table = new DataTable("#test_table", {
    pageLength: -1,
    scrollX: true,
    autoWidth: false,
    layout: {
      topStart: {
        buttons: ["colvis"],
      },
    },
  });
};

// A custom DataTable filter is implemented using a <select> tag with the following requirements:
// - It must have the `FILTER_INPUT_SELECTOR` class.
// - It must include a `data-criteria` attribute that specifies the criteria this filter looks for.
//
// Example:
// <select class="<FILTER_INPUT_SELECTOR>" data-criteria="fork"></select>
//
// The value of the `data-criteria' attribute must match the corresponding data attribute in the <tr> elements.
// For instance, rows containing <tr data-fork="..."> will be filtered based on this selection.
const filterRows = () => {
  table
    .rows()
    .search(function (rowContent, b, index) {
      const row = $(table.row(index).node());
      let match = true;

      const searchKeyword = $(FILTER_SEARCH_SELECTOR).val();
      const searchHit = rowContent.includes(searchKeyword);

      for (let filter of $(FILTER_INPUT_SELECTOR)) {
        // Filter is ignored if set to all
        if ($(filter).val() == "all") continue;

        // Otherwise, the result of this filter applied to the previous match.
        match =
          match && row.data($(filter).data("criteria")) === $(filter).val();
      }

      return searchKeyword.length ? match && searchHit : match;
    })
    .draw();
};

const listenForClipboardCopy = () => {
  // Event delegation for copy-to-clipboard functionality
  document.addEventListener("click", function (event) {
    if (event.target && event.target.classList.contains("copy-id")) {
      const fullId = event.target.getAttribute("data-full-id");

      // Copy to clipboard
      navigator.clipboard
        .writeText(fullId)
        .then(() => {
          const originalContent = event.target.innerHTML;

          // Set the sliding message with animation
          event.target.innerHTML =
            '<span class="slide show">...full test id copied!</span>';

          // Delay the hiding of the slide-out message
          setTimeout(() => {
            const slideElement = event.target.querySelector(".slide");
            if (slideElement) {
              slideElement.classList.add("hide");
            }
          }, 1000);

          // Restore the original content after the animation
          setTimeout(() => {
            event.target.innerHTML = originalContent;
          }, 1500); // Total duration before restoring original content
        })
        .catch((err) => {
          console.error("Failed to copy text: ", err);
        });
    }
  });
};
