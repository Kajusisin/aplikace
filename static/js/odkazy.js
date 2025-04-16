document.addEventListener("DOMContentLoaded", function() {
    console.log("📢 Inicializace modálních oken v odkazy_a_informace.html");
    
    // Reference na modální okna
    const odkazModal = document.getElementById("odkazModal");
    const infoModal = document.getElementById("infoModal");
    const souborModal = document.getElementById("souborModal");
    
    // Reference na tlačítka pro otevření modálních oken
    const pridatOdkazBtn = document.getElementById("pridatOdkazBtn");
    const pridatInfoBtn = document.getElementById("pridatInfoBtn");
    const nahratSouborBtn = document.getElementById("nahratSouborBtn");
    
    // Reference na tlačítka pro zavření modálních oken
    const zavritOdkaz = document.getElementById("zavritOdkaz");
    const zavritInfo = document.getElementById("zavritInfo");
    const zavritSoubor = document.getElementById("zavritSoubor");
    
    // Logování stavu prvků pro diagnostiku
    console.log("📢 Modální okna:", 
        odkazModal ? "✅ odkazModal OK" : "❌ odkazModal chybí", 
        infoModal ? "✅ infoModal OK" : "❌ infoModal chybí",
        souborModal ? "✅ souborModal OK" : "❌ souborModal chybí");
    
    console.log("📢 Tlačítka:", 
        pridatOdkazBtn ? "✅ pridatOdkazBtn OK" : "❌ pridatOdkazBtn chybí",
        pridatInfoBtn ? "✅ pridatInfoBtn OK" : "❌ pridatInfoBtn chybí",
        nahratSouborBtn ? "✅ nahratSouborBtn OK" : "❌ nahratSouborBtn chybí");
    
    // Funkce pro otevření modálního okna
    function openModal(modal) {
        if (modal) {
            modal.style.display = "block";
            document.body.classList.add("modal-open");
            console.log("📢 Modal otevřen:", modal.id);
        } else {
            console.error("❌ Nelze otevřít modální okno - neexistuje!");
        }
    }
    
    // Funkce pro zavření modálního okna
    function closeModal(modal) {
        if (modal) {
            modal.style.display = "none";
            document.body.classList.remove("modal-open");
            console.log("📢 Modal zavřen:", modal.id);
        }
    }
    
    // Přidání událostí pro otevření modálních oken
    if (pridatOdkazBtn) {
        pridatOdkazBtn.addEventListener("click", function(e) {
            e.preventDefault();
            console.log("📢 Kliknuto na tlačítko přidat odkaz");
            openModal(odkazModal);
        });
    }
    
    if (pridatInfoBtn) {
        pridatInfoBtn.addEventListener("click", function(e) {
            e.preventDefault();
            console.log("📢 Kliknuto na tlačítko přidat informaci");
            openModal(infoModal);
        });
    }
    
    if (nahratSouborBtn) {
        nahratSouborBtn.addEventListener("click", function(e) {
            e.preventDefault();
            console.log("📢 Kliknuto na tlačítko nahrát soubor");
            openModal(souborModal);
        });
    }
    
    // Zavření modálních oken
    if (zavritOdkaz) {
        zavritOdkaz.addEventListener("click", function() {
            closeModal(odkazModal);
        });
    }
    
    if (zavritInfo) {
        zavritInfo.addEventListener("click", function() {
            closeModal(infoModal);
        });
    }
    
    if (zavritSoubor) {
        zavritSoubor.addEventListener("click", function() {
            closeModal(souborModal);
        });
    }
    
    // Zavření modálních oken kliknutím mimo obsah
    window.onclick = function(event) {
        if (event.target === odkazModal) {
            closeModal(odkazModal);
        }
        if (event.target === infoModal) {
            closeModal(infoModal);
        }
        if (event.target === souborModal) {
            closeModal(souborModal);
        }
    };
    
    // Přidání kategorie "nová" do výběru
    const kategorieSelect = document.getElementById("kategorie");
    const novaKategorieInput = document.getElementById("nova-kategorie");
    
    if (kategorieSelect && novaKategorieInput) {
        kategorieSelect.addEventListener("change", function() {
            if (this.value === "nová") {
                novaKategorieInput.style.display = "block";
            } else {
                novaKategorieInput.style.display = "none";
            }
        });
    }
    
    // Globální testovací funkce pro snadné debugování
    window.testOpenModal = function(modalName) {
        console.log("📢 Testovací funkce volána pro:", modalName);
        if (modalName === 'odkaz') {
            openModal(odkazModal);
        } else if (modalName === 'info') {
            openModal(infoModal);
        } else if (modalName === 'soubor') {
            openModal(souborModal);
        } else {
            console.error('❌ Neznámý modal:', modalName);
        }
    };
});
