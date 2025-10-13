(function () {
    const $ = (selector, scope = document) => scope.querySelector(selector);
    const $$ = (selector, scope = document) => Array.from(scope.querySelectorAll(selector));

    document.addEventListener('DOMContentLoaded', () => {
        const bulkForm = $('[data-bulk-form]');
        if (!bulkForm) {
            return;
        }

        const selectAll = $('[data-select-all]', bulkForm);
        const checkboxes = $$('[data-row-checkbox]', bulkForm);
        const submitButton = $('[data-bulk-submit]', bulkForm);
        const emptyMessage = bulkForm.dataset.emptySelection || 'Please select at least one message.';

        const updateState = () => {
            const checkedCount = checkboxes.filter((cb) => cb.checked).length;
            if (selectAll) {
                selectAll.checked = checkedCount === checkboxes.length && checkedCount > 0;
                selectAll.indeterminate = checkedCount > 0 && checkedCount < checkboxes.length;
            }
            if (submitButton) {
                submitButton.disabled = checkedCount === 0;
            }
        };

        if (selectAll) {
            selectAll.addEventListener('change', () => {
                checkboxes.forEach((checkbox) => {
                    checkbox.checked = selectAll.checked;
                });
                updateState();
            });
        }

        checkboxes.forEach((checkbox) => {
            checkbox.addEventListener('change', updateState);
        });

        bulkForm.addEventListener('submit', (event) => {
            const hasSelection = checkboxes.some((cb) => cb.checked);
            if (!hasSelection) {
                event.preventDefault();
                alert(emptyMessage);
            }
        });

        updateState();
    });
})();
