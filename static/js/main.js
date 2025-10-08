document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ Checkout page loaded");

    const checkoutForm = document.getElementById("checkoutForm");

    if (checkoutForm) {
        checkoutForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const formData = new FormData(checkoutForm);
            const payload = {
                name: formData.get("name"),
                address: formData.get("address"),
                phone: formData.get("phone"),
            };

            try {
                // Call backend to create order
                const res = await fetch("http://localhost:5000/api/orders/place", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });

                const data = await res.json();
                console.log("📦 Order response:", data);

                if (!data.razorpay_order_id) {
                    alert("⚠️ Order creation failed!");
                    return;
                }

                // Open Razorpay payment
                const options = {
                    key: "YOUR_RAZORPAY_KEY_ID", // replace with your real key
                    amount: data.total_amt * 100, // paise
                    currency: "INR",
                    name: "E-Commerce Store",
                    description: "Order Payment",
                    order_id: data.razorpay_order_id,
                    handler: async function (response) {
                        console.log("💳 Payment success:", response);

                        // Save success in backend
                        await fetch("http://localhost:5000/api/orders/success", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                                payment_id: response.razorpay_payment_id,
                                order_id: data.order_id,
                                name: payload.name,
                                address: payload.address,
                                phone: payload.phone,
                            }),
                        });

                        alert("🎉 Payment successful! Order placed.");
                        window.location.href = "/orders"; // redirect to orders page
                    },
                    prefill: {
                        name: payload.name,
                        email: "test@example.com",
                        contact: payload.phone,
                    },
                    theme: { color: "#3399cc" },
                };

                const rzp = new Razorpay(options);
                rzp.open();

            } catch (err) {
                console.error("❌ Checkout error:", err);
                alert("Something went wrong, please try again.");
            }
        });
    }
});
