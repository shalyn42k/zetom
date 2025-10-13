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

    document.addEventListener('DOMContentLoaded', () => {
        const trashModal = $('[data-trash-modal]');
        if (!trashModal) {
            return;
        }

        const trashOpenButton = $('[data-trash-open]');
        const trashCloseElements = $$('[data-trash-close]', trashModal).concat(trashModal.querySelector('.modal__backdrop'));
        const trashForm = $('[data-trash-form]', trashModal);
        const trashActionField = trashForm ? trashForm.querySelector('input[name="action"]') : null;
        const trashSelectAll = $('[data-trash-select-all]', trashModal);
        const trashCheckboxes = $$('[data-trash-row]', trashModal);
        const trashButtons = $$('[data-trash-action]', trashModal);

        const toggleModal = (shouldOpen) => {
            if (!trashModal) {
                return;
            }
            if (shouldOpen) {
                trashModal.classList.add('is-visible');
                trashModal.setAttribute('aria-hidden', 'false');
                document.body.classList.add('has-modal');
            } else {
                trashModal.classList.remove('is-visible');
                trashModal.setAttribute('aria-hidden', 'true');
                document.body.classList.remove('has-modal');
            }
        };

        const updateTrashState = () => {
            const hasSelection = trashCheckboxes.some((checkbox) => checkbox.checked);

            if (trashSelectAll) {
                const enabledCheckboxes = trashCheckboxes.filter((checkbox) => !checkbox.disabled);
                const checkedCount = enabledCheckboxes.filter((checkbox) => checkbox.checked).length;
                trashSelectAll.checked = checkedCount > 0 && checkedCount === enabledCheckboxes.length;
                trashSelectAll.indeterminate = checkedCount > 0 && checkedCount < enabledCheckboxes.length;
            }

            trashButtons.forEach((button) => {
                if (button.dataset.requiresSelection === 'true') {
                    button.disabled = !hasSelection;
                }
            });
        };

        if (trashSelectAll) {
            trashSelectAll.addEventListener('change', () => {
                trashCheckboxes.forEach((checkbox) => {
                    checkbox.checked = trashSelectAll.checked && !checkbox.disabled;
                });
                updateTrashState();
            });
        }

        trashCheckboxes.forEach((checkbox) => {
            checkbox.addEventListener('change', updateTrashState);
        });

        trashButtons.forEach((button) => {
            button.addEventListener('click', () => {
                if (trashActionField) {
                    trashActionField.value = button.dataset.trashActionValue || '';
                }
            });
        });

        if (trashOpenButton) {
            trashOpenButton.addEventListener('click', () => toggleModal(true));
        }

        trashCloseElements.forEach((element) => {
            if (!element) {
                return;
            }
            element.addEventListener('click', () => toggleModal(false));
        });

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && trashModal.classList.contains('is-visible')) {
                toggleModal(false);
            }
        });

        updateTrashState();
    });
})();
