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

    document.addEventListener('DOMContentLoaded', () => {
        const downloadModal = $('[data-download-modal]');
        if (!downloadModal) {
            return;
        }

        const openButton = $('[data-download-open]');
        const closeElements = $$('[data-download-close]', downloadModal).concat(
            downloadModal.querySelector('.modal__backdrop')
        );
        const selectAll = $('[data-download-select-all]', downloadModal);
        const requestCheckboxes = $$('input[name="messages"]', downloadModal);
        const fieldCheckboxes = $$('input[name="fields"]', downloadModal);
        const submitButton = $('[data-download-submit]', downloadModal);
        const tableSelection = $$('[data-row-checkbox]');

        const applyTableSelection = () => {
            if (!tableSelection.length) {
                return;
            }
            const selectedIds = tableSelection
                .filter((checkbox) => checkbox.checked)
                .map((checkbox) => checkbox.value);
            requestCheckboxes.forEach((checkbox) => {
                checkbox.checked = selectedIds.includes(checkbox.value);
            });
        };

        const toggleModal = (shouldOpen) => {
            if (!downloadModal) {
                return;
            }
            if (shouldOpen) {
                downloadModal.classList.add('is-visible');
                downloadModal.setAttribute('aria-hidden', 'false');
                document.body.classList.add('has-modal');
            } else {
                downloadModal.classList.remove('is-visible');
                downloadModal.setAttribute('aria-hidden', 'true');
                document.body.classList.remove('has-modal');
            }
        };

        const updateSelectAllState = () => {
            if (!selectAll) {
                return;
            }
            const checkedCount = requestCheckboxes.filter((checkbox) => checkbox.checked).length;
            const total = requestCheckboxes.length;
            selectAll.checked = total > 0 && checkedCount === total;
            selectAll.indeterminate = checkedCount > 0 && checkedCount < total;
        };

        const updateSubmitState = () => {
            const hasRequests = requestCheckboxes.some((checkbox) => checkbox.checked);
            const hasFields = fieldCheckboxes.some((checkbox) => checkbox.checked);
            if (submitButton) {
                submitButton.disabled = !(hasRequests && hasFields);
            }
        };

        const updateState = () => {
            updateSelectAllState();
            updateSubmitState();
        };

        if (selectAll) {
            selectAll.addEventListener('change', () => {
                requestCheckboxes.forEach((checkbox) => {
                    checkbox.checked = selectAll.checked;
                });
                updateState();
            });
        }

        requestCheckboxes.forEach((checkbox) => {
            checkbox.addEventListener('change', updateState);
        });

        fieldCheckboxes.forEach((checkbox) => {
            checkbox.addEventListener('change', updateSubmitState);
        });

        if (openButton) {
            openButton.addEventListener('click', () => {
                applyTableSelection();
                updateState();
                toggleModal(true);
            });
        }

        closeElements.forEach((element) => {
            if (!element) {
                return;
            }
            element.addEventListener('click', () => toggleModal(false));
        });

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && downloadModal.classList.contains('is-visible')) {
                toggleModal(false);
            }
        });

        updateState();
    });
})();
