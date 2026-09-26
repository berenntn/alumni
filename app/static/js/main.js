/**
 * Istanbul University Alumni Tracking System
 * Client-side Interactivity & Live Endpoint Testing
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. Mobile Menu Toggle
  const mobileToggle = document.getElementById("mobileToggle");
  const navLinks = document.getElementById("navLinks");

  if (mobileToggle && navLinks) {
    mobileToggle.addEventListener("click", () => {
      navLinks.classList.toggle("active");
    });
  }

  // 2. Interactive API Sandbox Tester
  const endpointCards = document.querySelectorAll(".endpoint-card");
  const inputUrl = document.getElementById("terminalInputUrl");
  const runBtn = document.getElementById("terminalRunBtn");
  const outputBox = document.getElementById("terminalOutputBox");
  const statusBadge = document.getElementById("responseStatusBadge");

  // Initial selection
  if (endpointCards.length > 0 && inputUrl && runBtn && outputBox) {
    endpointCards.forEach((card) => {
      card.addEventListener("click", () => {
        endpointCards.forEach((c) => c.classList.remove("selected"));
        card.classList.add("selected");

        const targetUrl = card.getAttribute("data-url");
        if (targetUrl) {
          inputUrl.value = targetUrl;
          executeRequest(targetUrl);
        }
      });
    });

    runBtn.addEventListener("click", () => {
      if (inputUrl.value) {
        executeRequest(inputUrl.value);
      }
    });

    inputUrl.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        executeRequest(inputUrl.value);
      }
    });

    // Execute first endpoint on page load
    const initialCard = document.querySelector(".endpoint-card.selected");
    if (initialCard) {
      const url = initialCard.getAttribute("data-url");
      if (url) {
        inputUrl.value = url;
        executeRequest(url);
      }
    }
  }

  async function executeRequest(url) {
    if (!outputBox) return;

    outputBox.textContent = `İstek gönderiliyor: GET ${url} ...`;
    if (statusBadge) {
      statusBadge.textContent = "Gönderiliyor...";
      statusBadge.style.color = "#fbbf24";
    }

    try {
      const startTime = performance.now();
      const response = await fetch(url);
      const elapsed = Math.round(performance.now() - startTime);

      const statusText = `${response.status} ${response.statusText}`;
      if (statusBadge) {
        statusBadge.textContent = `${statusText} (${elapsed}ms)`;
        statusBadge.style.color = response.ok ? "#34d399" : "#f87171";
      }

      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        const data = await response.json();
        outputBox.textContent = JSON.stringify(data, null, 2);
      } else {
        const text = await response.text();
        outputBox.textContent = text.slice(0, 500) + (text.length > 500 ? "\n... (kısaltıldı)" : "");
      }
    } catch (err) {
      if (statusBadge) {
        statusBadge.textContent = "Bağlantı Hatası";
        statusBadge.style.color = "#f87171";
      }
      outputBox.textContent = `Hata: ${err.message}\nSunucunun çalıştığından emin olun.`;
    }
  }
});
