function planOlustur() {
    const ad = document.getElementById("ad").value.trim();
    const konularInput = document.getElementById("konular").value.trim();
    const emptyHours = Array.from(document.getElementById("empty_hours").selectedOptions)
                            .map(option => option.value);

    if (ad === "" || konularInput === "") {
        alert("Lütfen adınızı ve konuları girin!");
        return;
    }

    const konular = konularInput.split(",").map(k => k.trim());

    fetch("http://127.0.0.1:5000/calisma-onerisi", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ad, konular, empty_hours: emptyHours })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Sunucu Hatası: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        let html = `<h3>${data.ad} için öneriler:</h3><ul>`;
        data.oneriler.forEach(o => {
            html += `<li><b>${o.konu}</b>: ${o.sure} saat - ${o.yontem} (Saat: ${o.zaman})</li>`;
        });
        html += "</ul>";
        document.getElementById("sonuc").innerHTML = html;
    })
    .catch(error => {
        console.error("Hata:", error);
        document.getElementById("sonuc").innerHTML = "<p style='color:red;'>Sunucuya bağlanılamadı veya bir hata oluştu.</p>";
    });
}
