function toggleLang() {
    let currentLang = "{{ lang }}";
    let newLang = currentLang === "pl" ? "eng" : "pl";
    window.location.href = "/panel?lang=" + newLang;
}
