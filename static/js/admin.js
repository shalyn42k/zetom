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
        const downloadButton = $('[data-download-open]');
        const canControlDownloadButton = Boolean(
            downloadButton && downloadButton.dataset.downloadAvailable !== 'false',
        );
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
            if (canControlDownloadButton) {
                downloadButton.disabled = checkedCount === 0;
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
        const fieldCheckboxes = $$('input[name="fields"]', downloadModal);
        const submitButton = $('[data-download-submit]', downloadModal);
        const tableSelection = $$('[data-row-checkbox]');
        const hiddenInputsContainer = $('[data-download-selected]', downloadModal);
        const requestsCountElement = $('[data-download-requests-count]', downloadModal);
        const requestsTotalElement = $('[data-download-requests-total]', downloadModal);
        const requestsHintElement = $('[data-download-requests-hint]', downloadModal);
        const fieldsCountElement = $('[data-download-fields-count]', downloadModal);
        const fieldsHintElement = $('[data-download-fields-hint]', downloadModal);
        const fieldsPreviewElement = $('[data-download-fields-preview]', downloadModal);
        const maxPreviewItems = Number(
            (fieldsPreviewElement && fieldsPreviewElement.dataset.max) || 5,
        );

        let currentSelectedIds = [];

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

        const restoreSelectionFromHiddenInputs = () => {
            if (!hiddenInputsContainer) {
                return;
            }
            const storedValues = $$('input[name="messages"]', hiddenInputsContainer).map(
                (input) => input.value,
            );
            if (!storedValues.length) {
                return;
            }
            const uniqueValues = Array.from(new Set(storedValues));
            tableSelection.forEach((checkbox) => {
                checkbox.checked = uniqueValues.includes(checkbox.value);
            });
        };

        const getSelectedIdsFromTable = () =>
            tableSelection
                .filter((checkbox) => checkbox.checked && !checkbox.disabled)
                .map((checkbox) => checkbox.value);

        const syncHiddenInputs = () => {
            if (!hiddenInputsContainer) {
                return;
            }
            hiddenInputsContainer.innerHTML = '';
            currentSelectedIds.forEach((id) => {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'messages';
                input.value = id;
                hiddenInputsContainer.appendChild(input);
            });
        };

        const updateRequestsSummary = () => {
            const total = tableSelection.length;
            if (requestsCountElement) {
                requestsCountElement.textContent = String(currentSelectedIds.length);
            }
            if (requestsTotalElement) {
                requestsTotalElement.textContent = String(total);
            }
            if (requestsHintElement) {
                const dataset = requestsHintElement.dataset;
                const hint =
                    currentSelectedIds.length === 0
                        ? dataset.empty || ''
                        : (dataset.selected || '').replace('{count}', String(currentSelectedIds.length));
                requestsHintElement.textContent = hint;
            }
        };

        const updatePreview = (selectedFields) => {
            if (!fieldsPreviewElement) {
                return;
            }
            fieldsPreviewElement.innerHTML = '';
            if (!selectedFields.length) {
                const emptyText = fieldsPreviewElement.dataset.empty || '';
                if (emptyText) {
                    const emptyElement = document.createElement('span');
                    emptyElement.className = 'download-summary__empty';
                    emptyElement.textContent = emptyText;
                    fieldsPreviewElement.appendChild(emptyElement);
                }
                return;
            }

            const fragment = document.createDocumentFragment();
            selectedFields.slice(0, maxPreviewItems).forEach((checkbox) => {
                const optionElement = checkbox.closest('.download-option');
                const label = optionElement
                    ? optionElement.querySelector('.download-option__label')
                    : null;
                if (!label) {
                    return;
                }
                const chip = document.createElement('span');
                chip.className = 'download-chip';
                const labelText = label.textContent ? label.textContent.trim() : '';
                chip.textContent = labelText;
                fragment.appendChild(chip);
            });

            if (selectedFields.length > maxPreviewItems) {
                const chip = document.createElement('span');
                chip.className = 'download-chip download-chip--more';
                chip.textContent = `+${selectedFields.length - maxPreviewItems}`;
                fragment.appendChild(chip);
            }

            fieldsPreviewElement.appendChild(fragment);
        };

        const updateFieldsSummary = () => {
            const selectedFields = fieldCheckboxes.filter((checkbox) => checkbox.checked);
            const totalFields = fieldCheckboxes.length;

            if (fieldsCountElement) {
                fieldsCountElement.textContent = String(selectedFields.length);
            }
            if (fieldsHintElement) {
                const dataset = fieldsHintElement.dataset;
                let hint = '';
                if (selectedFields.length === 0) {
                    hint = dataset.empty || '';
                } else if (selectedFields.length === totalFields && totalFields > 0) {
                    hint = dataset.all || '';
                } else {
                    hint = (dataset.partial || '')
                        .replace('{count}', String(selectedFields.length))
                        .replace('{total}', String(totalFields));
                }
                fieldsHintElement.textContent = hint;
            }

            updatePreview(selectedFields);
        };

        const updateSubmitState = () => {
            const hasRequests = currentSelectedIds.length > 0;
            const hasFields = fieldCheckboxes.some((checkbox) => checkbox.checked);
            if (submitButton) {
                submitButton.disabled = !(hasRequests && hasFields);
            }
        };

        const refreshAll = (options = {}) => {
            const { syncHidden = false } = options;
            if (syncHidden || downloadModal.classList.contains('is-visible')) {
                syncHiddenInputs();
            }
            updateRequestsSummary();
            updateFieldsSummary();
            updateSubmitState();
        };

        const handleTableChange = () => {
            currentSelectedIds = getSelectedIdsFromTable();
            refreshAll({ syncHidden: true });
        };

        const handleFieldChange = () => {
            updateFieldsSummary();
            updateSubmitState();
        };

        restoreSelectionFromHiddenInputs();
        currentSelectedIds = getSelectedIdsFromTable();
        refreshAll({ syncHidden: true });

        if (openButton) {
            openButton.addEventListener('click', () => {
                currentSelectedIds = getSelectedIdsFromTable();
                if (!currentSelectedIds.length) {
                    return;
                }
                refreshAll({ syncHidden: true });
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

        tableSelection.forEach((checkbox) => {
            checkbox.addEventListener('change', handleTableChange);
        });

        fieldCheckboxes.forEach((checkbox) => {
            checkbox.addEventListener('change', handleFieldChange);
        });
    });
})();
