/**
 * Načte souhrn výkonů žáka ze serveru
 * @param {number} zakId - ID žáka
 * @param {number} rocnik - Ročník žáka
 * @param {number} skolniRok - Školní rok
 * @returns {Promise} Promise s daty souhrnu
 */
async function getStudentSummary(zakId, rocnik, skolniRok) {
    try {
        const response = await fetch(`/student_summary?zak_id=${zakId}&rocnik=${rocnik}&skolni_rok=${skolniRok}`);
        if (!response.ok) {
            throw new Error(`Server odpověděl s chybou: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("❌ Chyba při načítání souhrnu žáka:", error);
        return null;
    }
}

/**
 * Získá aktuální školní rok z DOM elementu body
 * @returns {number} První rok školního roku (např. 2025 pro školní rok 2025/2026)
 */
function getSkolniRokFromDOM() {
    // Nejprve zkus z data atributu v body
    const skolniRok = document.body.dataset.skolniRok;
    if (skolniRok) {
        return parseInt(skolniRok);
    }
    // Fallback na aktuální rok, pokud není v DOM
    return new Date().getFullYear();
}

/**
 * Aktualizuje UI elementy s daty žáka
 * @param {Object} summary - Data souhrnu ze serveru
 */
function updateStudentSummaryUI(summary) {
    // Aktualizace bodů
    const totalPointsEl = document.getElementById("totalPoints");
    if (totalPointsEl) {
        totalPointsEl.innerText = `Body: ${summary.total_with_bonus}`;
    }

    // Aktualizace průměru
    const averagePointsEl = document.getElementById("averagePoints");
    if (averagePointsEl) {
        averagePointsEl.innerText = `Průměr: ${summary.average}`;
    }

    // Aktualizace známky
    const finalGradeEl = document.getElementById("finalGrade");
    if (finalGradeEl) {
        finalGradeEl.innerText = `Známka: ${summary.grade || "-"}`;
    }

    // Aktualizace počtu disciplín
    const completedDisciplinesEl = document.getElementById("completedDisciplines");
    if (completedDisciplinesEl) {
        completedDisciplinesEl.innerText = `Počet zapsaných disciplín: ${summary.completed_disciplines}`;
    }
}

/**
 * Uloží výkon žáka na server
 * @param {number} zakId - ID žáka
 * @param {number} disciplineId - ID disciplíny
 * @param {string} vykon - Výkon
 * @param {number} rocnik - Ročník
 * @param {number} skolniRok - Školní rok
 */
function ulozVykon(zakId, disciplineId, vykon, rocnik, skolniRok) {
    fetch("/ulozit_vykon", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            zak_id: zakId,
            discipline_id: disciplineId,
            vykon: vykon,
            rocnik: rocnik,
            skolni_rok: skolniRok
        })
    })
        .then(res => res.json())
        .then(data => {
            console.log("✅ Výkon uložen:", data);
        })
        .catch(err => console.error("❌ Chyba při ukládání výkonu:", err));
}

/**
 * Vypočítá body na základě výkonu a uloží je na server
 * @param {HTMLInputElement} input - Vstupní pole výkonu
 * @param {number} disciplinaId - ID disciplíny
 */
function calculatePoints(input, disciplinaId) {
    let vykon = input.value.trim();
    if (!vykon || isNaN(vykon)) {
        console.error("❌ Neplatný výkon:", vykon);
        return;
    }

    // Pokračujeme pouze s platnými hodnotami
    fetch(`/ulozit_vykon`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            discipline_id: disciplinaId,
            vykon: vykon
        })
    })
        .then(response => response.json())
        .then(data => {
            console.log("✅ Výkon uložen:", data);
        })
        .catch(error => console.error("❌ Chyba při ukládání výkonu:", error));
}

function jeVykonValidni(vykon, typ) {
    if (typ === "int") {
        return /^-?\d+$/.test(vykon);  // celé číslo
    } else if (typ === "float") {
        return /^-?\d+([.,]\d+)?$/.test(vykon);  // desetinné číslo
    } else if (typ === "str") {
        return /^(\d{1,2}:)?\d{1,2}:\d{2}$|^\d{1,2}:\d{2}$/.test(vykon);  // MM:SS nebo H:MM:SS
    }
    return false;
}

/**
 * Zpracuje vstupní pole výkonu podle formátu disciplíny
 * @param {HTMLInputElement} input - Vstupní pole výkonu
 */
function handlePerformanceInput(input) {
    const formatType = input.dataset.formatType || 'float';
    const disciplinaId = input.dataset.disciplineId;
    let vykon = input.value.trim();

    if (!vykon) return; // Nic neděláme, pokud je prázdné

    // Validace podle formátu
    if (!jeVykonValidni(vykon, formatType)) {
        // Označíme vstup jako neplatný
        input.classList.add('error');
        input.title = `Neplatný formát výkonu pro typ ${formatType}`;
        return;
    }

    // Formátování hodnoty podle typu
    if (formatType === 'float') {
        // Převod na číslo s desetinnou čárkou
        vykon = vykon.replace(',', '.');
        input.value = vykon;
    } else if (formatType === 'int') {
        // Převod na celé číslo
        vykon = parseInt(parseFloat(vykon.replace(',', '.')));
        input.value = vykon;
    } else if (formatType === 'str' && vykon.includes(':')) {
        // Pro časové formáty - zajistíme správný formát MM:SS
        const parts = vykon.split(':');
        if (parts.length === 2) {
            input.value = `${parts[0]}:${parts[1].padStart(2, '0')}`;
        }
    }

    // Odstranění označení chyby, pokud existuje
    input.classList.remove('error');
    input.title = '';

    // Získání ostatních potřebných dat z UI
    const zakId = document.getElementById('zak-id').value;
    const rocnik = document.getElementById('selectedRocnik')?.value || 6;
    const skolniRok = getSkolniRokFromDOM();

    // Odeslání na server
    ulozVykon(zakId, disciplinaId, vykon, rocnik, skolniRok);
}

/**
 * Zpracuje stisknutí klávesy v inputu
 * @param {KeyboardEvent} event - Událost stisku klávesy
 * @param {HTMLInputElement} input - Vstupní pole
 */
function handleKeyPress(event, input) {
    if (event.key === 'Enter') {
        event.preventDefault();
        input.blur(); // Ztráta fokusu spustí onblur událost
    }
}

// Přidání funkcionality pro ukládání výkonů
document.addEventListener("DOMContentLoaded", function () {
    const rocnikElement = document.getElementById("selectedRocnik");
    // Bezpečnostní kontrola, zda element existuje
    if (rocnikElement) {
        const vybranyRocnik = rocnikElement.value;
        if (typeof nactiVykony === 'function') {
            nactiVykony(vybranyRocnik);
        }
    }

    const buttons = document.querySelectorAll(".ulozit-vykon-btn");

    buttons.forEach(button => {
        button.addEventListener("click", async () => {
            const zakId = button.dataset.zakId;
            const disciplineId = button.dataset.disciplineId;
            const rocnik = button.dataset.rocnik;
            const skolniRok = button.dataset.skolniRok || getSkolniRokFromDOM();

            const input = document.querySelector(`input[data-discipline-id="${disciplineId}"]`);
            const vykon = input.value;

            if (!vykon) {
                alert("Zadejte výkon!");
                return;
            }

            const data = {
                zak_id: parseInt(zakId),
                discipline_id: parseInt(disciplineId),
                rocnik: parseInt(rocnik),
                vykon: vykon,
                skolni_rok: parseInt(skolniRok)
            };

            try {
                const response = await fetch("/ulozit_vykon", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (result.message) {
                    alert(result.message);
                    input.classList.add("success");
                } else {
                    alert(result.error || "Chyba při ukládání.");
                }
            } catch (err) {
                console.error("❌ Chyba při volání API:", err);
                alert("Chyba při ukládání výkonu.");
            }
        });
    });

    // Přidání funkcionality pro automatické ukládání při změně vstupu
    document.querySelectorAll(".vykon-input").forEach(input => {
        input.addEventListener("change", function () {
            const zakId = this.dataset.zakId;
            const disciplineId = this.dataset.discId;
            const vykon = this.value;
            const rocnik = this.dataset.rocnik;
            const skolniRok = this.dataset.skolniRok || getSkolniRokFromDOM();

            fetch("/ulozit_vykon", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    zak_id: zakId,
                    discipline_id: disciplineId,
                    vykon: vykon,
                    rocnik: rocnik,
                    skolni_rok: skolniRok
                })
            })
                .then(res => res.json())
                .then(data => {
                    console.log("✅ Výkon uložen:", data);
                })
                .catch(err => console.error("❌ Chyba při ukládání výkonu:", err));
        });
    });

    const inputs = document.querySelectorAll(".vykon-input");

    inputs.forEach(input => {
        const saveHandler = async () => {
            const zakId = parseInt(input.dataset.zakId);
            const disciplineId = parseInt(input.dataset.disciplineId);
            const rocnik = parseInt(input.dataset.rocnik);
            const skolniRok = parseInt(input.dataset.skolniRok || getSkolniRokFromDOM());
            const vykon = input.value.trim();

            if (!vykon) return; // nic nezapisujeme, pokud je prázdné

            const data = {
                zak_id: zakId,
                discipline_id: disciplineId,
                rocnik: rocnik,
                vykon: vykon,
                skolni_rok: skolniRok
            };

            try {
                const response = await fetch("/ulozit_vykon", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (result.message) {
                    input.classList.add("success");
                    input.classList.remove("error");
                    showStatus(input, "✓");
                } else {
                    input.classList.add("error");
                    showStatus(input, "✗");
                }
            } catch (error) {
                console.error("Chyba při ukládání výkonu:", error);
                input.classList.add("error");
                showStatus(input, "✗");
            }
        };

        input.addEventListener("blur", saveHandler);
        input.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();
                saveHandler();
            }
        });
    });

    document.querySelectorAll("[name^='vykon_']").forEach(input => {
        input.addEventListener("blur", async function () {
            const disciplinaId = this.dataset.disciplineId;
            const vykon = this.value.trim();
            const zakId = this.dataset.zakId;
            const rocnik = this.dataset.rocnik;
            const skolniRok = this.dataset.skolniRok || getSkolniRokFromDOM();
            const bodyCell = document.getElementById("body_" + disciplinaId);

            if (vykon === "") {
                bodyCell.innerText = "0";
                if (typeof updateTotalPointsAndGrade === 'function') {
                    updateTotalPointsAndGrade();
                }
                if (typeof updateCompletedDisciplines === 'function') {
                    updateCompletedDisciplines();
                }
                return;
            }

            try {
                const response = await fetch("/ulozit_vykon", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        zak_id: zakId,
                        discipline_id: disciplinaId,
                        vykon: vykon,
                        rocnik: rocnik,
                        skolni_rok: skolniRok
                    })
                });

                const result = await response.json();
                if (response.ok && !result.error) {
                    bodyCell.innerText = result.body;
                    bodyCell.classList.remove("error");
                } else {
                    bodyCell.innerText = "Chyba";
                    bodyCell.classList.add("error");
                }
            } catch (err) {
                bodyCell.innerText = "Chyba";
                bodyCell.classList.add("error");
            }

            if (typeof updateTotalPointsAndGrade === 'function') {
                updateTotalPointsAndGrade();
            }
            if (typeof updateCompletedDisciplines === 'function') {
                updateCompletedDisciplines();
            }
        });

        // Enter → blur → spustí výše uvedené
        input.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                this.blur();
            }
        });

        if (typeof updateCompletedDisciplines === 'function') {
            input.addEventListener("input", updateCompletedDisciplines);
        }
    });

    function showStatus(input, symbol) {
        const statusSpan = input.closest("tr").querySelector(".ulozit-status");
        if (statusSpan) {
            statusSpan.textContent = symbol;
            setTimeout(() => {
                statusSpan.textContent = "";
            }, 2000);
        }
    }
});

document.addEventListener("DOMContentLoaded", function () {
    const tridaElement = document.getElementById("aktualni-trida");
    if (tridaElement && tridaElement.innerText.trim() === "Neznámá třída") {
        console.warn("⚠️ Třída žáka není definována.");
    }
});

document.addEventListener("DOMContentLoaded", () => {
    // Kontrola, zda jsme na stránce detailu žáka
    if (document.getElementById('detail-zaka-page')) {
        // Získání ID žáka z formuláře
        const zakIdInput = document.querySelector('[name="zak_id"]');
        if (zakIdInput) {
            const zakId = parseInt(zakIdInput.value);
            // Získání ročníku
            const rocnikInput = document.getElementById('selectedRocnik');
            const rocnik = rocnikInput ? parseInt(rocnikInput.value) : null;
            // Získání školního roku z DOM
            const skolniRok = getSkolniRokFromDOM();

            // Volání funkce pro načtení souhrnu
            if (zakId && rocnik) {
                console.log(`📊 Načítám souhrn žáka ID: ${zakId}, ročník: ${rocnik}, školní rok: ${skolniRok}`);
                getStudentSummary(zakId, rocnik, skolniRok)
                    .then(summary => {
                        if (summary) {
                            // Aktualizace UI s daty
                            updateStudentSummaryUI(summary);
                        }
                    })
                    .catch(error => {
                        console.error("❌ Chyba při načítání souhrnu žáka:", error);
                    });
            }
        }
    }
});

/**
 * Načte souhrn výkonů žáka a aktualizuje UI
 */
async function loadStudentSummary() {
    const zakId = document.querySelector("[name='zak_id']")?.value;
    const rocnik = document.getElementById("selectedRocnik")?.value || "6";
    const skolniRok = getSkolniRokFromDOM();

    if (!zakId || !rocnik || isNaN(skolniRok)) {
        console.error("❌ Chybí potřebná data pro načtení souhrnu.");
        return;
    }

    try {
        const summary = await getStudentSummary(zakId, rocnik, skolniRok);
        if (summary) {
            updateStudentSummaryUI(summary);
        }
    } catch (error) {
        console.error("❌ Chyba při načítání souhrnu žáka:", error);
    }
}
