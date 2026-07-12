document.getElementById("waitlistForm").addEventListener("submit", async function(event) {
  event.preventDefault();
  const response = await fetch("/join-waitlist", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      name: document.getElementById("name").value,
      email: document.getElementById("email").value,
      phone: document.getElementById("phone").value
    })
  });
  const data = await response.json();
  alert(data.message);
  this.reset();
});
