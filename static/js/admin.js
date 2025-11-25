/*
# === FILE SUMMARY ===
# Purpose: Client-side logic for the admin panel interface.
# Responsible for: Handling bulk actions, trash operations, download selections, modals, filtering, pagination, and admin settings interactions.
# Connected to: templates/contact/admin_panel.html elements, admin_settings endpoint, forms rendered in admin views.
# Important classes/functions: DOMContentLoaded handler initialising form behaviours and settings management functions.
# Notes: Relies on data attributes and standard fetch API for AJAX requests.
# =====================================
*/
(function () {
    const $ = (selector, scope = document) => scope.querySelector(selector);
    const $$ = (selector, scope = document) => Array.from(scope.querySelectorAll(selector));

    const parseJsonData = (rawValue, fallbackValue) => {
        if (!rawValue) {
            return fallbackValue;
        }

        const normalised = rawValue
            .replace(/&quot;/g, '"')
            .replace(/&#x27;/g, "'")
            .trim();

        const candidates = [normalised, normalised.replace(/'/g, '"')];

        for (const candidate of candidates) {
            try {
                return JSON.parse(candidate);
            } catch (error) {
                // try next candidate
            }
        }

        console.warn('Unable to parse JSON data, falling back to default.');
        return fallbackValue;
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
        const attachmentsList = $('[data-request-attachments]', requestModal);
        const attachmentsEmptyMessage = attachmentsList ? attachmentsList.dataset.empty || '' : '';
        const clientLogList = $('[data-request-client-log]', requestModal);
        const clientLogEmptyMessage = clientLogList ? clientLogList.dataset.empty || '' : '';
        const tokenHashElement = $('[data-request-token-hash]', requestModal);
        const accessEnabledElement = $('[data-request-access-enabled]', requestModal);
        const backdrop = requestModal.querySelector('.modal__backdrop');
        const closeElements = $$('[data-request-close]', requestModal);
        const statusMap = parseJsonData(requestModal.dataset.statusMap, {});
        const detailErrorMessage = requestModal.dataset.detailError || '';
        const updateErrorMessage = requestModal.dataset.updateError || '';
        const detailTemplate = requestModal.dataset.detailTemplate || '';
        const updateTemplate = requestModal.dataset.updateTemplate || '';
        const rollbackTemplate = requestModal.dataset.rollbackTemplate || '';
        const language = requestModal.dataset.language || 'pl';
        const fieldLabels = language === 'pl'
            ? {
                  full_name: 'Imię i nazwisko',
                  phone: 'Telefon',
                  email: 'E-mail',
                  company: 'Firma',
                  company_name: 'Nazwa firmy',
                  message: 'Treść zgłoszenia',
              }
            : {
                  full_name: 'Full name',
                  phone: 'Phone',
                  email: 'E-mail',
                  company: 'Company',
                  company_name: 'Company name',
                  message: 'Message',
              };

        let currentRow = null;
        let currentId = null;
        let isBusy = false;

        const buildUrl = (template, id) => template.replace(/0(?!.*0)/, String(id));
        const buildRollbackUrl = (template, messageId, logId) =>
            template.replace(/0/, String(messageId)).replace(/0/, String(logId));

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
                customerCell.textContent = data.full_name || '';
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
            const companyNameCell = $('[data-cell="company-name"]', currentRow);
            if (companyNameCell) {
                companyNameCell.textContent = data.company_name || '';
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

        const clearFeedback = () => {
            if (feedbackBox) {
                feedbackBox.textContent = '';
                feedbackBox.hidden = true;
            }
        };

        const renderAttachments = (items) => {
            if (!attachmentsList) {
                return;
            }
            attachmentsList.innerHTML = '';
            if (!items || !items.length) {
                if (attachmentsEmptyMessage) {
                    const emptyItem = document.createElement('li');
                    emptyItem.className = 'attachment-list__empty';
                    emptyItem.textContent = attachmentsEmptyMessage;
                    attachmentsList.appendChild(emptyItem);
                }
                return;
            }
            items.forEach((item) => {
                const listItem = document.createElement('li');
                listItem.className = 'attachment-list__item';
                const link = document.createElement('a');
                link.href = item.url || '#';
                link.target = '_blank';
                link.rel = 'noopener';
                link.textContent = item.name || 'attachment';
                if (item.size) {
                    const sizeKb = (Number(item.size) / 1024).toFixed(1);
                    const sizeSpan = document.createElement('span');
                    sizeSpan.className = 'attachment-list__meta';
                    sizeSpan.textContent = `${sizeKb} KB`;
                    listItem.append(link, sizeSpan);
                } else {
                    listItem.appendChild(link);
                }
                attachmentsList.appendChild(listItem);
            });
        };

        const renderClientLog = (entries) => {
            if (!clientLogList) {
                return;
            }
            clientLogList.innerHTML = '';
            if (!entries || !entries.length) {
                if (clientLogEmptyMessage) {
                    const emptyItem = document.createElement('li');
                    emptyItem.className = 'client-log__empty';
                    emptyItem.textContent = clientLogEmptyMessage;
                    clientLogList.appendChild(emptyItem);
                }
                return;
            }
            entries.forEach((entry) => {
                const listItem = document.createElement('li');
                listItem.className = 'client-log__item';
                const header = document.createElement('div');
                header.className = 'client-log__header';
                const fieldLabel = fieldLabels[entry.field] || entry.field;
                header.textContent = `${fieldLabel} · ${entry.changed_at}`;
                const values = document.createElement('div');
                values.className = 'client-log__values';
                const previous = escapeHtml(entry.previous_value || '');
                const current = escapeHtml(entry.new_value || '');
                values.innerHTML = `<span class="client-log__from">${previous || '—'}</span> → <span class="client-log__to">${current || '—'}</span>`;
                listItem.append(header, values);
                const actions = document.createElement('div');
                actions.className = 'client-log__actions';
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'button button--ghost button--compact';
                button.dataset.logId = String(entry.id);
                button.dataset.logField = entry.field;
                button.dataset.logRollback = 'true';
                button.textContent = entry.is_reverted
                    ? language === 'pl'
                        ? 'Przywrócono'
                        : 'Reverted'
                    : language === 'pl'
                        ? 'Przywróć'
                        : 'Rollback';
                button.disabled = Boolean(entry.is_reverted);
                actions.appendChild(button);
                listItem.appendChild(actions);
                clientLogList.appendChild(listItem);
            });
        };

        const setAccessInfo = (data) => {
            if (tokenHashElement) {
                tokenHashElement.textContent = data.access_token_hash || '—';
            }
            if (accessEnabledElement) {
                const enabled = Boolean(data.access_enabled);
                if (language === 'pl') {
                    accessEnabledElement.textContent = enabled ? 'Tak' : 'Nie';
                } else {
                    accessEnabledElement.textContent = enabled ? 'Yes' : 'No';
                }
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
            renderAttachments(data.attachments || []);
            setAccessInfo(data);
            if (data.client_logs) {
                renderClientLog(data.client_logs);
            }
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
            clearFeedback();
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
            clearFeedback();
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
                    populateForm(data);
                    setHeader(data.id, data.created_at);
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

        const rollbackChange = (logId, trigger) => {
            if (!rollbackTemplate || !currentId) {
                return;
            }
            const url = buildRollbackUrl(rollbackTemplate, currentId, logId);
            if (!url) {
                return;
            }
            const csrfToken = getCsrfToken();
            isBusy = true;
            showError('');
            clearFeedback();
            if (trigger) {
                trigger.disabled = true;
            }
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken,
                },
            })
                .then((response) => {
                    if (!response.ok) {
                        throw new Error(String(response.status));
                    }
                    return response.json();
                })
                .then((data) => {
                    updateRowDisplay(data);
                    populateForm(data);
                    setHeader(data.id, data.created_at);
                })
                .catch(() => {
                    alert(updateErrorMessage || 'Unable to revert change.');
                    if (trigger) {
                        trigger.disabled = false;
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

        if (clientLogList) {
            clientLogList.addEventListener('click', (event) => {
                const target = event.target;
                if (!(target instanceof HTMLButtonElement) || target.dataset.logRollback !== 'true') {
                    return;
                }
                const logId = target.dataset.logId;
                if (!logId) {
                    return;
                }
                rollbackChange(logId, target);
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


    document.addEventListener('DOMContentLoaded', () => {
        const panelButtons = $$('[data-panel-trigger]');
        const panels = $$('[data-panel-content]');
        if (!panelButtons.length || !panels.length) {
            return;
        }

        const showPanel = (panelName) => {
            panels.forEach((panel) => {
                const shouldShow = panel.dataset.panelContent === panelName;
                panel.classList.toggle('is-hidden', !shouldShow);
            });
            panelButtons.forEach((button) => {
                button.classList.toggle('is-active', button.dataset.panel === panelName);
            });
        };

        panelButtons.forEach((button) => {
            button.addEventListener('click', () => showPanel(button.dataset.panel));
        });

        showPanel('requests');
    });

    document.addEventListener('DOMContentLoaded', () => {
        const settingsRoot = document.querySelector('[data-settings-panel]');
        const profileForm = settingsRoot
            ? settingsRoot.querySelector('[data-profile-form]')
            : null;
        if (!settingsRoot || !profileForm) {
            return;
        }

        const endpoint = settingsRoot.dataset.profileEndpoint;
        if (!endpoint) {
            return;
        }

        const errorBox = profileForm.querySelector('[data-profile-errors]');
        const successBox = profileForm.querySelector('[data-profile-success]');
        const emailDisplay = settingsRoot.querySelector('[data-profile-email-display]');
        const emailInput = profileForm.querySelector('[data-profile-email]');
        const oldPasswordInput = profileForm.querySelector('[data-profile-old-password]');
        const newPasswordInput = profileForm.querySelector('[data-profile-new-password]');
        const confirmInput = profileForm.querySelector('[data-profile-new-password-confirm]');

        const showError = (message) => {
            if (errorBox) {
                errorBox.textContent = message;
                errorBox.hidden = !message;
            }
            if (successBox) {
                successBox.hidden = true;
            }
        };

        const showSuccess = (message) => {
            if (successBox) {
                successBox.textContent = message;
                successBox.hidden = !message;
            }
            if (errorBox) {
                errorBox.hidden = true;
            }
        };

        profileForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            showError('');
            showSuccess('');

            const payload = {
                email: emailInput ? emailInput.value : '',
                old_password: oldPasswordInput ? oldPasswordInput.value : '',
                new_password: newPasswordInput ? newPasswordInput.value : '',
                new_password_confirm: confirmInput ? confirmInput.value : '',
            };

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken() || '',
                },
                body: JSON.stringify(payload),
            });

            const data = await response.json().catch(() => ({}));
            if (!response.ok || data.success === false) {
                const errors = (data && data.errors) || {};
                const combined = Object.values(errors).join(' ') || 'Unable to update profile.';
                showError(combined);
                return;
            }

            if (emailDisplay && data.email) {
                emailDisplay.textContent = data.email;
            }
            if (emailInput && data.email) {
                emailInput.value = data.email;
            }

            [oldPasswordInput, newPasswordInput, confirmInput].forEach((input) => {
                if (input) {
                    input.value = '';
                }
            });

            showSuccess('Profile updated successfully.');
        });
    });

    document.addEventListener('DOMContentLoaded', () => {
        const settingsRoot = document.querySelector('[data-settings-panel]');
        if (!settingsRoot) {
            return;
        }

        const rowsContainer = settingsRoot.querySelector('[data-settings-rows]');
        const emptyState = settingsRoot.querySelector('[data-settings-empty]');
        const addButton = settingsRoot.querySelector('[data-settings-add]');
        const applyButton = settingsRoot.querySelector('[data-settings-apply]');
        const errorBox = settingsRoot.querySelector('[data-settings-error]');
        const endpoint = settingsRoot.dataset.settingsEndpoint;
        const verifyEndpoint = settingsRoot.dataset.verifyEndpoint;
        const paginationContainer = settingsRoot.querySelector('[data-settings-pagination]');
        const confirmationBlock = settingsRoot.querySelector('[data-admin-password-confirmation]');
        const passwordInput = settingsRoot.querySelector('[data-admin-password-input]');
        const passwordConfirmButton = settingsRoot.querySelector('[data-admin-password-submit]');
        const passwordErrorBox = settingsRoot.querySelector('[data-admin-password-error]');
        const departmentsPrototype = settingsRoot.querySelector('select[data-department-prototype="true"]');

        if (!rowsContainer || !endpoint) {
            return;
        }

        const departmentsOptionsHTML = departmentsPrototype ? departmentsPrototype.innerHTML : '';
        const departmentsSize = departmentsPrototype ? departmentsPrototype.size || 4 : 4;
        const levelOptions = [
            { value: 'level1', label: 'level1' },
            { value: 'level2', label: 'level2' },
            { value: 'level3', label: 'level3' },
        ];

        const pageSize = 5;
        let allUsers = [];
        let baselineLevels = new Map();
        let currentPage = 1;
        let pendingPayload = null;

        const showError = (message) => {
            if (!errorBox) return;
            errorBox.textContent = message;
            errorBox.hidden = !message;
        };

        const showPasswordError = (message) => {
            if (!passwordErrorBox) return;
            passwordErrorBox.textContent = message;
            passwordErrorBox.hidden = !message;
        };

        const updateEmptyState = () => {
            if (!rowsContainer || !emptyState) return;
            const hasRows = rowsContainer.querySelector('[data-settings-row]');
            emptyState.style.display = hasRows ? 'none' : 'block';
        };

        const togglePasswordField = (user, passwordCell, passwordInputField) => {
            const enablePassword = user.level === 'level1';
            if (passwordCell) {
                passwordCell.style.display = enablePassword ? '' : 'none';
            }
            if (passwordInputField) {
                passwordInputField.disabled = !enablePassword;
                if (!enablePassword) {
                    passwordInputField.value = '';
                    user.password = '';
                    user.password_changed = false;
                }
            }
        };

        const refreshPagination = () => {
            if (!paginationContainer) return;
            paginationContainer.innerHTML = '';
            const totalPages = Math.max(1, Math.ceil(allUsers.length / pageSize) || 1);
            const createButton = (label, page, disabled = false) => {
                const button = document.createElement('button');
                button.type = 'button';
                button.textContent = label;
                button.className = 'pagination__page';
                if (disabled) {
                    button.disabled = true;
                }
                button.addEventListener('click', () => {
                    currentPage = page;
                    renderRows(currentPage);
                });
                return button;
            };

            const prevButton = createButton('‹', Math.max(1, currentPage - 1), currentPage === 1);
            paginationContainer.appendChild(prevButton);

            for (let page = 1; page <= totalPages; page += 1) {
                const pageButton = createButton(String(page), page, false);
                if (page === currentPage) {
                    pageButton.classList.add('pagination__page--active');
                }
                paginationContainer.appendChild(pageButton);
            }

            const nextButton = createButton('›', Math.min(totalPages, currentPage + 1), currentPage === totalPages);
            paginationContainer.appendChild(nextButton);
        };

        const buildRow = (user, index) => {
            const row = document.createElement('div');
            row.className = 'settings-table__row';
            row.dataset.settingsRow = 'true';
            row.dataset.index = String(index);
            row.classList.toggle('is-marked-for-deletion', Boolean(user.marked_for_deletion));

            const idCell = document.createElement('span');
            idCell.textContent = user.user_id ? `#${user.user_id}` : '—';

            const emailInput = document.createElement('input');
            emailInput.type = 'email';
            emailInput.required = true;
            emailInput.value = user.email || '';
            emailInput.addEventListener('input', () => {
                allUsers[index].email = emailInput.value;
            });

            const passwordCell = document.createElement('div');
            passwordCell.className = 'settings-table__password';
            const passwordInputField = document.createElement('input');
            passwordInputField.type = 'text';
            passwordInputField.value = user.password || '';
            passwordInputField.placeholder = 'Password';
            passwordInputField.autocomplete = 'new-password';
            passwordInputField.addEventListener('input', () => {
                allUsers[index].password = passwordInputField.value;
                allUsers[index].password_changed = true;
            });
            passwordCell.appendChild(passwordInputField);

            const levelSelect = document.createElement('select');
            levelOptions.forEach((option) => {
                const opt = document.createElement('option');
                opt.value = option.value;
                opt.textContent = option.label;
                opt.selected = option.value === user.level;
                levelSelect.appendChild(opt);
            });
            levelSelect.addEventListener('change', () => {
                allUsers[index].level = levelSelect.value;
                togglePasswordField(allUsers[index], passwordCell, passwordInputField);
                renderRows(currentPage);
            });

            const departmentSelect = document.createElement('select');
            departmentSelect.innerHTML = departmentsOptionsHTML;
            departmentSelect.multiple = true;
            departmentSelect.size = departmentsSize;
            const selectedDepartments = Array.isArray(user.departments) ? user.departments : [];
            Array.from(departmentSelect.options).forEach((opt) => {
                opt.selected = selectedDepartments.includes(opt.value);
            });
            departmentSelect.addEventListener('change', () => {
                const selectedValues = Array.from(departmentSelect.selectedOptions).map((opt) => opt.value);
                allUsers[index].departments = selectedValues;
            });

            const deleteCell = document.createElement('div');
            deleteCell.className = 'settings-table__delete';
            const deleteButton = document.createElement('button');
            deleteButton.type = 'button';
            deleteButton.innerHTML = '🗑';
            deleteButton.title = 'Delete user';
            deleteButton.addEventListener('click', () => {
                if (!allUsers[index].marked_for_deletion) {
                    const confirmed = window.confirm('Delete this user? They will be removed after Apply.');
                    if (!confirmed) {
                        return;
                    }
                    allUsers[index].marked_for_deletion = true;
                } else {
                    allUsers[index].marked_for_deletion = false;
                }
                renderRows(currentPage);
            });
            deleteCell.appendChild(deleteButton);

            row.append(
                idCell,
                emailInput,
                passwordCell,
                levelSelect,
                departmentSelect,
                deleteCell,
            );
            togglePasswordField(user, passwordCell, passwordInputField);
            return row;
        };

        const renderRows = (page = 1) => {
            if (!rowsContainer) return;
            const start = (page - 1) * pageSize;
            const end = start + pageSize;
            const usersSlice = allUsers.slice(start, end);
            rowsContainer.innerHTML = '';
            usersSlice.forEach((user, index) => {
                const row = buildRow(user, start + index);
                rowsContainer.appendChild(row);
            });
            updateEmptyState();
            refreshPagination();
        };

        const setUsers = (users) => {
            baselineLevels = new Map();
            allUsers = (users || []).map((user) => {
                if (user.user_id) {
                    baselineLevels.set(String(user.user_id), user.level);
                }
                return {
                    user_id: user.user_id || null,
                    email: user.email || '',
                    level: user.level || '',
                    password: '',
                    password_changed: false,
                    departments: Array.isArray(user.departments) ? user.departments : [],
                    marked_for_deletion: Boolean(user.marked_for_deletion),
                    is_new: Boolean(user.is_new) || !user.user_id,
                };
            });
            currentPage = 1;
            renderRows(currentPage);
        };

        const fetchUsers = async () => {
            const response = await fetch(endpoint);
            if (!response.ok) {
                showError('Unable to load settings data.');
                return;
            }
            const data = await response.json();
            showError('');
            setUsers(data.users || []);
        };

        const buildPayload = () => ({
            users: allUsers.map((user) => ({
                user_id: user.user_id || null,
                email: user.email || '',
                level: user.level || '',
                password: user.level === 'level1' && user.password_changed ? user.password || '' : '',
                password_changed: user.level === 'level1' ? Boolean(user.password_changed) : false,
                departments: Array.isArray(user.departments) ? user.departments : [],
                marked_for_deletion: Boolean(user.marked_for_deletion),
                is_new: Boolean(user.is_new) || !user.user_id,
            })),
        });

        const hasDangerousChanges = (payload) => {
            const removesUser = payload.users.some((user) => user.marked_for_deletion);
            const levelChanged = payload.users.some((user) => {
                if (!user.user_id) return false;
                const baseline = baselineLevels.get(String(user.user_id));
                return baseline && baseline !== user.level;
            });
            return removesUser || levelChanged;
        };

        const applyChanges = async (payload) => {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken() || '',
                },
                body: JSON.stringify(payload),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                showError((data.errors && data.errors.join(', ')) || 'Validation error.');
                return;
            }
            showError('');
            if (confirmationBlock) {
                confirmationBlock.hidden = true;
            }
            if (passwordInput) {
                passwordInput.value = '';
            }
            pendingPayload = null;
            setUsers(data.users || []);
        };

        const verifyPassword = async () => {
            if (!verifyEndpoint || !passwordInput) {
                return false;
            }
            const response = await fetch(verifyEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken() || '',
                },
                body: JSON.stringify({ password: passwordInput.value || '' }),
            });
            const data = await response.json().catch(() => ({}));
            return Boolean(data.valid && response.ok);
        };

        if (addButton) {
            addButton.addEventListener('click', () => {
                allUsers.push({
                    user_id: null,
                    email: '',
                    level: '',
                    password: '',
                    password_changed: false,
                    departments: [],
                    marked_for_deletion: false,
                    is_new: true,
                });
                currentPage = Math.ceil(allUsers.length / pageSize) || 1;
                renderRows(currentPage);
            });
        }

        if (applyButton) {
            applyButton.addEventListener('click', () => {
                const payload = buildPayload();
                const confirmed = window.confirm('Apply changes to users? This will update access and departments.');
                if (!confirmed) {
                    return;
                }
                if (hasDangerousChanges(payload) && verifyEndpoint) {
                    pendingPayload = payload;
                    showPasswordError('');
                    if (confirmationBlock) {
                        confirmationBlock.hidden = false;
                    }
                    if (passwordInput) {
                        passwordInput.value = '';
                        passwordInput.focus();
                    }
                    return;
                }
                applyChanges(payload).catch(() => showError('Unable to save changes.'));
            });
        }

        if (passwordConfirmButton) {
            passwordConfirmButton.addEventListener('click', async () => {
                if (!pendingPayload) {
                    pendingPayload = buildPayload();
                }
                const valid = await verifyPassword();
                if (!valid) {
                    showPasswordError('Invalid administrator password.');
                    return;
                }
                showPasswordError('');
                applyChanges(pendingPayload).catch(() => showError('Unable to save changes.'));
            });
        }

        fetchUsers().catch(() => showError('Unable to load settings data.'));
    });
})();
