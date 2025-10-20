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
        const canControlOpenButton = Boolean(
            openButton && openButton.dataset.downloadAvailable !== 'false',
        );
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

        const updateOpenButtonState = () => {
            if (!canControlOpenButton) {
                return;
            }
            const shouldDisable = currentSelectedIds.length === 0;
            openButton.disabled = shouldDisable;
            openButton.toggleAttribute('disabled', shouldDisable);
        };

        const refreshAll = (options = {}) => {
            const { syncHidden = false } = options;
            if (syncHidden || downloadModal.classList.contains('is-visible')) {
                syncHiddenInputs();
            }
            updateRequestsSummary();
            updateFieldsSummary();
            updateSubmitState();
            updateOpenButtonState();
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

    document.addEventListener('DOMContentLoaded', () => {
        const requestModal = $('[data-request-modal]');
        if (!requestModal) {
            return;
        }

        const rows = $$('[data-request-row]');
        const form = $('[data-request-form]', requestModal);
        const titleElement = $('[data-request-title]', requestModal);
        const createdElement = $('[data-request-created]', requestModal);
        const errorBox = $('[data-request-errors]', requestModal);
        const feedbackBox = $('[data-request-feedback]', requestModal);
        const backdrop = requestModal.querySelector('.modal__backdrop');
        const closeElements = $$('[data-request-close]', requestModal);
        const statusMap = (() => {
            try {
                return JSON.parse(requestModal.dataset.statusMap || '{}');
            } catch (error) {
                console.error('Invalid status map', error);
                return {};
            }
        })();
        const successMessage = requestModal.dataset.successMessage || '';
        const detailErrorMessage = requestModal.dataset.detailError || '';
        const updateErrorMessage = requestModal.dataset.updateError || '';
        const detailTemplate = requestModal.dataset.detailTemplate || '';
        const updateTemplate = requestModal.dataset.updateTemplate || '';
        const language = requestModal.dataset.language || 'pl';

        let currentRow = null;
        let currentId = null;
        let isBusy = false;

        const buildUrl = (template, id) => template.replace(/0(?!.*0)/, String(id));

        const toggleModal = (shouldOpen) => {
            if (!requestModal) {
                return;
            }
            if (shouldOpen) {
                requestModal.classList.add('is-visible');
                requestModal.setAttribute('aria-hidden', 'false');
                document.body.classList.add('has-modal');
            } else {
                requestModal.classList.remove('is-visible');
                requestModal.setAttribute('aria-hidden', 'true');
                document.body.classList.remove('has-modal');
                currentRow = null;
                currentId = null;
                if (form) {
                    form.reset();
                }
                if (errorBox) {
                    errorBox.hidden = true;
                    errorBox.textContent = '';
                }
                if (feedbackBox) {
                    feedbackBox.hidden = true;
                    feedbackBox.textContent = '';
                }
            }
        };

        const focusFirstField = () => {
            if (!form) {
                return;
            }
            const firstInput = form.querySelector('input, select, textarea');
            if (firstInput) {
                firstInput.focus();
            }
        };

        const escapeHtml = (value) => {
            const div = document.createElement('div');
            div.textContent = value;
            return div.innerHTML;
        };

        const buildGmailLink = (email) => {
            if (!email) {
                return '#';
            }
            return `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(email)}`;
        };

        const updateRowDisplay = (data) => {
            if (!currentRow) {
                return;
            }
            const customerCell = $('[data-cell="customer"]', currentRow);
            if (customerCell) {
                customerCell.textContent = `${data.first_name} ${data.last_name}`.trim();
            }
            const phoneElement = $('[data-cell-phone]', currentRow);
            if (phoneElement) {
                phoneElement.textContent = data.phone;
                if (phoneElement instanceof HTMLAnchorElement) {
                    phoneElement.href = `tel:${data.phone}`;
                }
            }
            const emailElement = $('[data-cell-email]', currentRow);
            if (emailElement) {
                emailElement.textContent = data.email;
                if (emailElement instanceof HTMLAnchorElement) {
                    emailElement.href = buildGmailLink(data.email);
                }
            }
            const companyCell = $('[data-cell="company"]', currentRow);
            if (companyCell) {
                companyCell.textContent = data.company;
            }
            const messageCell = $('[data-cell="message"]', currentRow);
            if (messageCell) {
                const html = escapeHtml(data.message || '').replace(/\n/g, '<br>');
                messageCell.innerHTML = html;
            }
            const statusCell = $('[data-cell="status"]', currentRow);
            if (statusCell) {
                const badge = $('[data-status-badge]', statusCell);
                if (badge) {
                    const statusInfo = statusMap[data.status] || {};
                    const label = data.status_label || statusInfo.label || data.status;
                    const badgeClass = data.status_badge || statusInfo.badge || '';
                    badge.textContent = label;
                    badge.className = `badge ${badgeClass}`.trim();
                }
            }
        };

        const showError = (message) => {
            if (errorBox) {
                errorBox.textContent = message;
                errorBox.hidden = !message;
            }
        };

        const showFeedback = (message) => {
            if (feedbackBox) {
                feedbackBox.textContent = message;
                feedbackBox.hidden = !message;
            }
        };

        const populateForm = (data) => {
            if (!form) {
                return;
            }
            form.reset();
            Object.entries(data).forEach(([key, value]) => {
                const field = form.elements.namedItem(key);
                if (!field) {
                    return;
                }
                if (field instanceof HTMLInputElement || field instanceof HTMLTextAreaElement) {
                    field.value = value ?? '';
                } else if (field instanceof HTMLSelectElement) {
                    field.value = value ?? '';
                }
            });
        };

        const setHeader = (id, createdAt) => {
            if (titleElement) {
                const prefix = language === 'pl' ? 'Zgłoszenie #' : 'Request #';
                titleElement.textContent = `${prefix}${id}`;
            }
            if (createdElement) {
                const label = language === 'pl' ? 'Utworzone:' : 'Created:';
                createdElement.textContent = createdAt ? `${label} ${createdAt}` : '';
            }
        };

        const getCsrfToken = () => {
            const cookieValue = document.cookie
                .split('; ')
                .find((row) => row.startsWith('csrftoken='));
            if (!cookieValue) {
                return '';
            }
            return decodeURIComponent(cookieValue.split('=')[1]);
        };

        const fetchDetails = (row) => {
            if (!row || isBusy) {
                return;
            }
            const id = row.dataset.requestId;
            if (!id) {
                return;
            }
            const url = buildUrl(detailTemplate, id);
            if (!url) {
                return;
            }
            isBusy = true;
            showError('');
            showFeedback('');
            fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
                .then((response) => {
                    if (!response.ok) {
                        throw new Error(String(response.status));
                    }
                    return response.json();
                })
                .then((data) => {
                    currentRow = row;
                    currentId = data.id;
                    populateForm(data);
                    setHeader(data.id, data.created_at);
                    toggleModal(true);
                    focusFirstField();
                })
                .catch(() => {
                    alert(detailErrorMessage || 'Unable to load request.');
                })
                .finally(() => {
                    isBusy = false;
                });
        };

        const submitUpdate = () => {
            if (!form || !currentId) {
                return;
            }
            const url = buildUrl(updateTemplate, currentId);
            if (!url) {
                return;
            }
            const formData = new FormData(form);
            const csrfToken = formData.get('csrfmiddlewaretoken') || getCsrfToken();
            isBusy = true;
            showError('');
            showFeedback('');
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken,
                },
                body: formData,
            })
                .then((response) => {
                    if (response.ok) {
                        return response.json();
                    }
                    return response.json().then((data) => {
                        throw data;
                    });
                })
                .then((data) => {
                    updateRowDisplay(data);
                    showFeedback(successMessage);
                    showError('');
                })
                .catch((error) => {
                    if (error && error.errors) {
                        const messages = Object.values(error.errors)
                            .flat()
                            .join(' ');
                        showError(messages || updateErrorMessage);
                    } else {
                        showError(updateErrorMessage);
                    }
                })
                .finally(() => {
                    isBusy = false;
                });
        };

        if (form) {
            form.addEventListener('submit', (event) => {
                event.preventDefault();
                submitUpdate();
            });
        }

        const handleRowActivation = (row, event) => {
            const interactive = event.target instanceof Element
                ? event.target.closest('input, a, button, label')
                : null;
            if (interactive) {
                return;
            }
            fetchDetails(row);
        };

        rows.forEach((row) => {
            row.addEventListener('click', (event) => {
                handleRowActivation(row, event);
            });
            row.addEventListener('keydown', (event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    fetchDetails(row);
                }
            });
        });

        const closeModal = () => toggleModal(false);

        closeElements.forEach((element) => {
            if (!element) {
                return;
            }
            element.addEventListener('click', closeModal);
        });

        if (backdrop) {
            backdrop.addEventListener('click', closeModal);
        }

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && requestModal.classList.contains('is-visible')) {
                closeModal();
            }
        });
    });
})();
