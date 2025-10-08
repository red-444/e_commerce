const otpSection = document.getElementById("otpSection");
const otpForm = document.getElementById("otpForm");
const resendOtp = document.getElementById("resendOtp");
const msgBox = document.getElementById("otpMessage");
let currentOrderId = null;
let userPhone = "";
let userEmail = "";

// ---------------- Send OTP ----------------
document.getElementById("sendOtpBtn").addEventListener("click", async function () {
  const phone = document.getElementById("phoneInput").value.trim();
  const email = document.getElementById("emailInput").value.trim();

  if (!phone && !email) {
    alert("Please provide a phone number or email to receive OTP.");
    return;
  }

  userPhone = phone;
  userEmail = email;

  try {
    const response = await fetch("/resend-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone: phone, email: email }),
      credentials: "include"
    });

    if (!response.ok) throw new Error(response.statusText);
    const data = await response.json();

    if (data.status === "success") {
      otpSection.classList.remove("d-none"); // show OTP box
      msgBox.innerHTML = `<span class="text-success">📩 OTP sent successfully!</span>`;
    } else {
      msgBox.innerHTML = `<span class="text-danger">❌ ${data.message}</span>`;
    }
  } catch (err) {
    msgBox.innerHTML = `<span class="text-danger">⚠️ Error sending OTP: ${err.message}</span>`;
  }
});

// ---------------- Verify OTP ----------------
otpForm.addEventListener("submit", async function (e) {
  e.preventDefault();
  const otp = document.getElementById("otp").value.trim();

  try {
    const response = await fetch("/verify-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ otp: otp, phone: userPhone, email: userEmail }),
      credentials: "include"
    });

    if (!response.ok) throw new Error(response.statusText);
    const data = await response.json();

    if (data.status === "success") {
      msgBox.innerHTML = `<span class="text-success">✅ OTP Verified! You can now proceed to payment.</span>`;
      otpSection.style.display = "none";
      document.getElementById("paymentSection").style.display = "block";
    } else {
      msgBox.innerHTML = `<span class="text-danger">❌ Invalid OTP: ${data.message}</span>`;
    }
  } catch (err) {
    msgBox.innerHTML = `<span class="text-danger">⚠️ Error verifying OTP: ${err.message}</span>`;
  }
});

// ---------------- Resend OTP ----------------
resendOtp.addEventListener("click", async function (e) {
  e.preventDefault();
  try {
    const response = await fetch("/resend-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone: userPhone, email: userEmail }),
      credentials: "include"
    });

    if (!response.ok) throw new Error(response.statusText);
    const data = await response.json();

    if (data.status === "success") {
      msgBox.innerHTML = `<span class="text-success">📩 OTP resent successfully!</span>`;
    } else {
      msgBox.innerHTML = `<span class="text-danger">❌ Failed to resend OTP: ${data.message}</span>`;
    }
  } catch (err) {
    msgBox.innerHTML = `<span class="text-danger">⚠️ Error resending OTP: ${err.message}</span>`;
  }
});

// ---------------- Pay Now ----------------
document.getElementById("payBtn").addEventListener("click", async function () {
  const address = document.getElementById("addressInput").value;

  try {
const response = await fetch("/payment/create-order", {    // ✅ dash
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ shipping_address: address }),
      credentials: "include"
    });

    if (!response.ok) throw new Error(response.statusText);
    const data = await response.json();

    if (data.status === "success") {
      currentOrderId = data.order_id;

      const options = {
        key: data.key,
        amount: data.amount,
        currency: data.currency,
        name: "My E-Commerce",
        description: "Order Payment",
        order_id: data.razorpay_order_id,
        handler: async function (response) {
          const verifyRes = await fetch("/payment/verify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(response),
            credentials: "include"
          });

          if (!verifyRes.ok) throw new Error(verifyRes.statusText);
          const verifyData = await verifyRes.json();

          if (verifyData.status === "success") {
            alert("✅ Payment successful!");
            window.location.href = "/";
          } else {
            alert("❌ Payment verification failed: " + verifyData.message);
          }
        },
        prefill: {
          name: document.getElementById("nameInput").value,
          contact: document.getElementById("phoneInput").value,
        },
        theme: { color: "#3399cc" },
      };

      const rzp = new Razorpay(options);
      rzp.open();
    } else {
      alert("Order creation failed: " + data.message);
    }
  } catch (err) {
    alert("⚠️ Error creating order: " + err.message);
  }
});


