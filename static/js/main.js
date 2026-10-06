// KitabKosh Online Bookstore Main Scripts

document.addEventListener("DOMContentLoaded", () => {
    // Auto fadeout flash alerts after 6 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 6000);
    });

    // Print Receipt Button handler
    const printReceiptBtn = document.getElementById("printReceiptBtn");
    if (printReceiptBtn) {
        printReceiptBtn.addEventListener("click", () => {
            window.print();
        });
    }
});
