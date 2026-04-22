const API = "https://your-app.onrender.com";

let transactions = [];

// LOAD
async function loadTransactions() {
  const res = await fetch(`${API}/transactions`);
  transactions = await res.json();

  renderTransactions();
}

// RENDER INTO YOUR UI TABLE
function renderTransactions() {
  const table = document.getElementById("txBody");

  if (!table) {
    console.error("txBody not found");
    return;
  }

  table.innerHTML = transactions.map(t => `
    <tr>
      <td>${t.date}</td>
      <td>${t.description}</td>
      <td>${t.category}</td>
      <td>${t.type}</td>
      <td>₹${t.amount}</td>
      <td>
        <button onclick="deleteTx(${t.id})">❌</button>
      </td>
    </tr>
  `).join("");
}

// ADD (connected to your popup/form)
async function addTransaction() {
  const data = {
    type: document.getElementById("txType").value,
    amount: parseFloat(document.getElementById("txAmount").value),
    description: document.getElementById("txDesc").value,
    category: document.getElementById("txCat").value,
    date: document.getElementById("txDate").value
  };

  await fetch(`${API}/transactions`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(data)
  });

  loadTransactions();
}

// DELETE
async function deleteTx(id) {
  await fetch(`${API}/transactions/${id}`, {
    method: "DELETE"
  });

  loadTransactions();
}

// START
window.onload = loadTransactions;