/* filepath: c:\Users\kajus\Desktop\hejbni_kostrou\static\js\components\modals.js */
document.addEventListener("DOMContentLoaded", function() {
    console.log("✅ Inicializace modálních oken");
    
    // Funkce pro otevření modálního okna
    window.openModal = function(modalId) {
        console.log("📢 Otevírám modální okno:", modalId);
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = "block";
            document.body.classList.add("modal-open");
            // Přidáme třídu show pro fade-in animaci
            setTimeout(() => {
                modal.classList.add("show");
            }, 10);
        } else {
            console.error("❌ Modální okno nenalezeno:", modalId);
        }
    };
    
    // Funkce pro zavření modálního okna
    window.closeModal = function(modalId) {
        console.log("📢 Zavírám modální okno:", modalId);
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove("show");
            setTimeout(() => {
                modal.style.display = "none";
                document.body.classList.remove("modal-open");
            }, 300); // Počkáme na dokončení animace
        }
    };
    
    // Najít všechny zavírací prvky
    const closeButtons = document.querySelectorAll(".close");
    closeButtons.forEach(button => {
        button.addEventListener("click", function() {
            // Najít nejbližší modální okno
            const modal = this.closest(".modal");
            if (modal) {
                window.closeModal(modal.id);
            }
        });
    });
    
    // Najít všechna tlačítka pro otevření modálních oken
    const openButtons = document.querySelectorAll("[data-open-modal]");
    openButtons.forEach(button => {
        button.addEventListener("click", function(e) {
            e.preventDefault();
            const modalId = this.getAttribute("data-open-modal");
            if (modalId) {
                window.openModal(modalId);
            }
        });
    });
    
    // Zavřít modální okno při kliknutí mimo obsah
    document.addEventListener("click", function(event) {
        if (event.target.classList.contains("modal") && event.target.style.display === "block") {
            window.closeModal(event.target.id);
        }
    });
    
    // Funkce pro přidání nové kategorie
    const kategorieSelects = document.querySelectorAll("select[name='kategorie']");
    kategorieSelects.forEach(select => {
        const novaKategorieInput = select.parentElement.querySelector(".nova-kategorie-input");
        if (novaKategorieInput) {
            select.addEventListener("change", function() {
                if (this.value === "nová") {
                    novaKategorieInput.style.display = "block";
                } else {
                    novaKategorieInput.style.display = "none";
                }
            });
        }
    });
    
    // Speciální zpracování pro stránku odkazy_a_informace.html
    if (document.querySelector(".odkazy-container")) {
        console.log("📢 Detekována stránka odkazy_a_informace.html, inicializuji speciální modální okna");
        
        // Zpracování tlačítek pro přidání odkazu/informace/souboru
        ["pridatOdkazBtn", "pridatInfoBtn", "nahratSouborBtn"].forEach(btnId => {
            const btn = document.getElementById(btnId);
            if (btn) {
                const modalId = btnId.replace("Btn", "Modal");
                btn.addEventListener("click", function(e) {
                    e.preventDefault();
                    window.openModal(modalId);
                });
                console.log(`✅ Přidán listener pro ${btnId} -> ${modalId}`);
            } else {
                console.warn(`⚠️ Tlačítko ${btnId} nebylo nalezeno`);
            }
        });
        
        // Zpracování mazacích tlačítek
        const deleteButtons = document.querySelectorAll(".delete-btn");
        deleteButtons.forEach(btn => {
            btn.addEventListener("click", function(e) {
                if (!confirm("Opravdu chcete smazat tuto položku?")) {
                    e.preventDefault();
                }
            });
        });
    }
});
