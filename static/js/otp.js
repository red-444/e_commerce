const otpForm = document.getElementById("otpForm");
const otpSection = document.getElementById("otpSection");
const msgBox = document.getElementById("otpMessage");


if (data.status === "success") {
  otpSection.classList.remove("d-none");   // ✅ show OTP box
  msgBox.innerHTML = `<span class="text-success">📩 OTP sent successfully!</span>`;
} else {
  msgBox.innerHTML = `<span class="text-danger">❌ ${data.message}</span>`;
}

// Send OTP
document.getElementById("sendOtpBtn").addEventListener("click", async () => {
  const response = await fetch("/resend-otp", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
    credentials: "include"   // keep session
  });
  const data = await response.json();
  msgBox.innerHTML = data.status === "success"
    ? "📩 OTP sent!"
    : "❌ " + data.message;
});

// Verify OTP
otpForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const otp = document.getElementById("otp").value;

  const response = await fetch("/verify-otp", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ otp }),
    credentials: "include"
  });

  const data = await response.json();
  if (data.status === "success") {
    msgBox.innerHTML = "✅ OTP verified!";
    document.getElementById("otpSection").style.display = "none";
    document.getElementById("paymentSection").style.display = "block"; // 👈 show Pay Now
  } else {
    msgBox.innerHTML = "❌ " + data.message;
  }
});
