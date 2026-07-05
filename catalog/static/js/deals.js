/* Deals browser.

   Calls the paginated /api/deals/ endpoint and renders the results table.
   The API returns {count, next, previous, results}; Previous/Next just
   follow the URLs the API hands back.
*/

let nextUrl = null;
let prevUrl = null;

function filtersUrl() {
  const minDiscount = document.getElementById("min-discount").value || "0";
  const category = document.getElementById("category").value;
  let url = "/api/deals/?min_discount=" + encodeURIComponent(minDiscount);
  if (category) {
    url += "&category=" + encodeURIComponent(category);
  }
  return url;
}

function renderTable(products) {
  const results = document.getElementById("results");
  results.innerHTML = "";

  if (products.length === 0) {
    results.textContent = "No deals match these filters.";
    return;
  }

  const table = document.createElement("table");
  const headerRow = document.createElement("tr");
  ["Product", "Category", "Brand", "Retail", "Sale", "Discount"].forEach(function (text) {
    const th = document.createElement("th");
    th.textContent = text;
    headerRow.appendChild(th);
  });
  table.appendChild(headerRow);

  products.forEach(function (product) {
    const row = document.createElement("tr");

    const nameCell = document.createElement("td");
    const link = document.createElement("a");
    link.href = "/api/product/" + product.id + "/";
    link.textContent = product.name;
    nameCell.appendChild(link);
    row.appendChild(nameCell);

    [
      product.category.name,
      product.brand ? product.brand.name : "-",
      product.retail_price,
      product.sale_price,
      product.discount_pct + "%",
    ].forEach(function (value) {
      const td = document.createElement("td");
      td.textContent = value;
      row.appendChild(td);
    });

    table.appendChild(row);
  });
  results.appendChild(table);
}

function loadDeals(url) {
  document.getElementById("status").textContent = "Loading...";
  fetch(url)
    .then(function (response) {
      return response.json();
    })
    .then(function (data) {
      nextUrl = data.next;
      prevUrl = data.previous;
      document.getElementById("next").disabled = !nextUrl;
      document.getElementById("prev").disabled = !prevUrl;
      document.getElementById("status").textContent =
        "Showing " + data.results.length + " of " + data.count + " deals";
      renderTable(data.results);
    })
    .catch(function (error) {
      document.getElementById("status").textContent = "Request failed: " + error;
    });
}

document.getElementById("filters").addEventListener("submit", function (event) {
  event.preventDefault();
  loadDeals(filtersUrl());
});
document.getElementById("next").addEventListener("click", function () {
  if (nextUrl) loadDeals(nextUrl);
});
document.getElementById("prev").addEventListener("click", function () {
  if (prevUrl) loadDeals(prevUrl);
});

/* initial load with the default filters */
loadDeals(filtersUrl());
