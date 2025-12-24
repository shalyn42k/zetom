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

    document.addEventListener('DOMContentLoaded', () => {
        const panelButtons = document.querySelectorAll('[data-panel-trigger]');
        const panels = document.querySelectorAll('[data-panel-content]');

        if (panelButtons.length && panels.length) {
            panelButtons.forEach((btn) => {
                btn.addEventListener('click', () => {
                    const target = btn.getAttribute('data-panel');
                    if (!target) return;

                    panelButtons.forEach((b) => b.classList.remove('is-active'));
                    btn.classList.add('is-active');

                    panels.forEach((panel) => {
                        const name = panel.getAttribute('data-panel-content');
                        if (name === target) {
                            panel.classList.remove('is-hidden');
                        } else {
                            panel.classList.add('is-hidden');
                        }
                    });
                });
            });
        }
    });

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
        const settingsPanel = document.querySelector('[data-settings-panel]');
        if (!settingsPanel) {
            return;
        }

        const language = document.documentElement.lang || 'en';
        const profileForm = settingsPanel.querySelector('[data-profile-form]');
        const profileEndpoint = settingsPanel.getAttribute('data-profile-endpoint');
        const verifyEndpoint = settingsPanel.getAttribute('data-verify-endpoint');
        const resetEndpoint = settingsPanel.getAttribute('data-reset-endpoint');
        const rowsContainer = settingsPanel.querySelector('[data-settings-rows]');
        const emptyState = settingsPanel.querySelector('[data-settings-empty]');
        const addButton = settingsPanel.querySelector('[data-settings-add]');
        const applyButton = settingsPanel.querySelector('[data-settings-apply]');
        const errorBox = settingsPanel.querySelector('[data-settings-error]');
        const endpoint = settingsPanel.getAttribute('data-settings-endpoint');
        const currentAdminId = settingsPanel.getAttribute('data-admin-id');
        const departmentsPrototype = settingsPanel.querySelector('select[data-department-prototype="true"]');
        const permissionDefaults = parseJsonData(
            settingsPanel.getAttribute('data-permissions-defaults'),
            {},
        );
        const departmentLabelMap = {};
        if (departmentsPrototype) {
            Array.from(departmentsPrototype.options).forEach((opt) => {
                departmentLabelMap[opt.value] = opt.textContent;
            });
        }

        const adminPasswordSection = settingsPanel.querySelector('[data-admin-password-confirmation]');
        const adminPasswordInput = settingsPanel.querySelector('[data-admin-password-input]');
        const adminPasswordSubmit = settingsPanel.querySelector('[data-admin-password-submit]');
        const adminPasswordError = settingsPanel.querySelector('[data-admin-password-error]');
        const profileErrors = settingsPanel.querySelector('[data-profile-errors]');
        const profileSuccess = settingsPanel.querySelector('[data-profile-success]');
        const profileEmailInput = settingsPanel.querySelector('[data-profile-email]');
        const profileOldPassword = settingsPanel.querySelector('[data-profile-old-password]');
        const profileNewPassword = settingsPanel.querySelector('[data-profile-new-password]');
        const profileNewPasswordConfirm = settingsPanel.querySelector('[data-profile-new-password-confirm]');
        const profileEmailDisplay = settingsPanel.querySelector('[data-profile-email-display]');
        const userModal = document.querySelector('[data-user-modal]');
        const userModalForm = userModal?.querySelector('[data-user-form]');
        const userModalTitle = userModal?.querySelector('[data-user-modal-title]');
        const userModalError = userModal?.querySelector('[data-user-modal-error]');
        const userEmailInput = userModal?.querySelector('[data-user-email]');
        const userLevelSelect = userModal?.querySelector('[data-user-level]');
        const userPasswordMount = userModal?.querySelector('[data-user-password-mount]');
        let manualPasswordBlock = userModal?.querySelector('[data-user-password-block]');
        let manualPasswordToggleWrapper = manualPasswordBlock?.querySelector('[data-user-password-toggle-wrapper]');
        let manualPasswordToggle = manualPasswordBlock?.querySelector('[data-user-password-toggle]');
        let manualPasswordRow = manualPasswordBlock?.querySelector('[data-user-password-row]');
        let manualPasswordInput = manualPasswordBlock?.querySelector('[data-user-password]');
        const manualPasswordTemplate = manualPasswordBlock?.cloneNode(true);
        const userDepartmentsContainer = userModal?.querySelector('[data-user-departments]');
        const permissionOverrideToggle = userModal?.querySelector('[data-permission-override]');
        const permissionList = userModal?.querySelector('[data-user-permissions]');
        const permissionModeLabel = userModal?.querySelector('[data-permission-mode-label]');
        const permissionModeHint = userModal?.querySelector('[data-permission-mode-hint]');
        const permissionModePill = userModal?.querySelector('[data-permission-mode-pill]');
        const tabButtons = userModal ? userModal.querySelectorAll('[data-tab-target]') : [];
        const tabPanels = userModal ? userModal.querySelectorAll('[data-tab-content]') : [];

        const PAGE_SIZE = 5;
        let users = [];
        let originalLevelMap = new Map();
        let currentPage = 1;
        let pendingPayload = null;
        let activeUserIndex = null;
        let isManualPassword = false;
        let isEditingExistingUser = false;

        const getCsrfToken = () => {
            const name = 'csrftoken=';
            return document.cookie
                .split(';')
                .map((cookie) => cookie.trim())
                .find((cookie) => cookie.startsWith(name))?.slice(name.length);
        };

        const normaliseErrorMessages = (input) => {
            const rawMessages = [];
            if (Array.isArray(input)) {
                rawMessages.push(...input);
            } else if (input && typeof input === 'object') {
                Object.values(input).forEach((value) => {
                    if (Array.isArray(value)) {
                        rawMessages.push(...value);
                    } else if (value) {
                        rawMessages.push(String(value));
                    }
                });
            } else if (typeof input === 'string' && input.trim()) {
                rawMessages.push(input);
            }
            return Array.from(
                new Set(
                    rawMessages
                        .map((msg) => String(msg).trim())
                        .filter(Boolean),
                ),
            );
        };

        const showError = (message) => {
            if (!errorBox) return;
            const uniqueMessages = normaliseErrorMessages(message);
            if (uniqueMessages.length) {
                errorBox.innerHTML = uniqueMessages.map((msg) => `<div>${msg}</div>`).join('');
                errorBox.hidden = false;
            } else {
                errorBox.innerHTML = '';
                errorBox.hidden = true;
            }
        };

        const showProfileError = (message) => {
            if (!profileErrors) return;
            profileErrors.textContent = message || '';
            profileErrors.hidden = !message;
        };

        const showProfileSuccess = (visible) => {
            if (!profileSuccess) return;
            profileSuccess.hidden = !visible;
        };

        const fallbackPermissions = Object.values(permissionDefaults)[0] || {};
        const permissionLabels = {
            can_edit_messages:
                language === 'pl' ? 'Edycja wiadomości' : 'Edit messages',
            can_delete_messages:
                language === 'pl' ? 'Usuwanie i kosz' : 'Delete & trash',
            can_export_messages: language === 'pl' ? 'Eksport' : 'Export',
            can_send_emails: language === 'pl' ? 'Wysyłanie e-maili' : 'Send emails',
        };

        const getRolePermissions = (level) => ({
            ...(permissionDefaults[level] || fallbackPermissions),
        });

        const renderPermissionCheckboxes = (mode, level, customPermissions) => {
            if (!permissionList) return;
            const basePermissions = getRolePermissions(level);
            const effective = mode === 'custom'
                ? { ...basePermissions, ...(customPermissions || {}) }
                : basePermissions;
            permissionList.innerHTML = '';
            Object.entries(permissionLabels).forEach(([key, label]) => {
                const wrapper = document.createElement('label');
                wrapper.className = 'checkbox-pill checkbox-pill--permission';
                const checkboxId = `permission-${key}`;
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = checkboxId;
                checkbox.value = key;
                checkbox.dataset.permissionItem = 'true';
                checkbox.checked = Boolean(effective[key]);
                checkbox.disabled = mode !== 'custom';
                const text = document.createElement('span');
                text.textContent = label;
                wrapper.setAttribute('for', checkboxId);
                wrapper.append(checkbox, text);
                permissionList.appendChild(wrapper);
            });
        };

        const updateEmptyState = () => {
            if (!rowsContainer || !emptyState) return;
            emptyState.style.display = users.length ? 'none' : 'block';
        };

        const buildRow = (user) => {
            const row = document.createElement('div');
            row.className = 'settings-table__row';
            row.dataset.settingsRow = 'true';
            row.dataset.userId = user.user_id || '';
            row.dataset.isNew = user.is_new ? 'true' : 'false';
            row.dataset.markedForDeletion = user.marked_for_deletion ? 'true' : 'false';
            row.dataset.index = user.index;
            row.tabIndex = 0;

            const idCell = document.createElement('span');
            idCell.textContent = user.user_id ? `#${user.user_id}` : '—';

            const emailCell = document.createElement('span');
            emailCell.className = 'settings-table__cell-text';
            emailCell.textContent = user.email || '—';

            const levelCell = document.createElement('span');
            levelCell.className = 'settings-table__pill';
            levelCell.textContent = user.level || '—';

            const departmentCell = document.createElement('span');
            departmentCell.className = 'settings-table__cell-text';
            const departmentLabels = Array.isArray(user.departments)
                ? user.departments
                      .map((dept) => departmentLabelMap[dept] || dept)
                      .filter(Boolean)
                : [];
            departmentCell.textContent = departmentLabels.length ? departmentLabels.join(', ') : '—';

            const permissionCell = document.createElement('div');
            permissionCell.className = 'settings-table__meta';
            const permissionStatus = document.createElement('span');
            permissionStatus.className = 'badge badge--info';
            permissionStatus.textContent =
                user.permissions_mode === 'custom'
                    ? language === 'pl'
                        ? 'Ręczna konfiguracja'
                        : 'Custom'
                    : language === 'pl'
                        ? 'Domyślne'
                        : 'Defaults';
            permissionCell.append(permissionStatus);

            const hiddenPasswordInput = document.createElement('input');
            hiddenPasswordInput.type = 'hidden';
            hiddenPasswordInput.value = user.password_plaintext || '';
            hiddenPasswordInput.dataset.settingsPassword = 'true';
            permissionCell.appendChild(hiddenPasswordInput);

            const actionsCell = document.createElement('div');
            actionsCell.className = 'settings-table__delete settings-table__actions';

            const editButton = document.createElement('button');
            editButton.type = 'button';
            editButton.className = 'settings-table__action settings-table__action--success';
            editButton.textContent = language === 'pl' ? 'Edytuj' : 'Edit';
            editButton.addEventListener('click', (event) => {
                event.stopPropagation();
                openUserModal(user);
            });

            const resetButton = document.createElement('button');
            resetButton.type = 'button';
            resetButton.className = 'settings-table__action settings-table__action--info';
            resetButton.dataset.userReset = 'true';
            resetButton.dataset.userId = user.user_id || '';
            resetButton.title = language === 'pl'
                ? 'Wyślij nowe hasło e-mailem'
                : 'Send new password via email';
            resetButton.textContent = language === 'pl' ? 'Resetuj hasło' : 'Resend password';
            if (!user.user_id) {
                resetButton.disabled = true;
            }

            const deleteButton = document.createElement('button');
            deleteButton.type = 'button';
            deleteButton.className = 'settings-table__action settings-table__action--danger';
            deleteButton.textContent = language === 'pl' ? 'Usuń' : 'Delete';
            deleteButton.title = language === 'pl' ? 'Usuń użytkownika' : 'Delete user';

            const isCurrentAdmin = String(user.user_id) === String(currentAdminId);
            if (isCurrentAdmin) {
                row.classList.add('settings-row--self');
                deleteButton.disabled = true;
                deleteButton.setAttribute('aria-disabled', 'true');
                editButton.disabled = false;
                resetButton.disabled = false;
            } else {
                deleteButton.addEventListener('click', (event) => {
                    event.stopPropagation();
                    const confirmation = window.confirm(
                        language === 'pl'
                            ? 'Usunąć tego użytkownika? Zostanie usunięty po kliknięciu Apply.'
                            : 'Delete this user? They will be removed after clicking Apply.',
                    );
                    if (!confirmation) {
                        return;
                    }
                    const isMarked = row.dataset.markedForDeletion === 'true';
                    const targetUser = users[user.index];
                    if (targetUser) {
                        targetUser.marked_for_deletion = !isMarked;
                    }
                    row.dataset.markedForDeletion = (!isMarked).toString();
                    row.classList.toggle('is-marked-for-deletion', !isMarked);
                    deleteButton.setAttribute('aria-pressed', (!isMarked).toString());
                });
            }
            editButton.disabled = false;
            resetButton.disabled = !user.user_id;

            actionsCell.append(editButton, resetButton, deleteButton);

            row.append(
                idCell,
                emailCell,
                levelCell,
                departmentCell,
                permissionCell,
                actionsCell,
            );
            return row;
        };

        const renderPagination = () => {
            const paginationContainer = settingsPanel.querySelector('[data-settings-pagination]');
            if (!paginationContainer) return;
            const totalPages = Math.max(1, Math.ceil(users.length / PAGE_SIZE));
            if (currentPage > totalPages) {
                currentPage = totalPages;
            }
            paginationContainer.innerHTML = '';
            for (let page = 1; page <= totalPages; page += 1) {
                const button = document.createElement('button');
                button.type = 'button';
                button.textContent = page.toString();
                button.className = 'pagination__page';
                if (page === currentPage) {
                    button.classList.add('is-active');
                }
                button.addEventListener('click', () => {
                    currentPage = page;
                    renderRows();
                });
                paginationContainer.appendChild(button);
            }
        };

        const renderRows = () => {
            if (!rowsContainer) return;
            rowsContainer.innerHTML = '';
            const start = (currentPage - 1) * PAGE_SIZE;
            const paginatedUsers = users.slice(start, start + PAGE_SIZE);
            paginatedUsers.forEach((user) => {
                const row = buildRow(user);
                rowsContainer.appendChild(row);
            });
            updateEmptyState();
            renderPagination();
        };

        const toggleUserModal = (shouldOpen) => {
            if (!userModal) return;
            if (shouldOpen) {
                userModal.classList.add('is-visible');
                userModal.setAttribute('aria-hidden', 'false');
                document.body.classList.add('has-modal');
            } else {
                userModal.classList.remove('is-visible');
                userModal.setAttribute('aria-hidden', 'true');
                document.body.classList.remove('has-modal');
            }
        };

        const populateDepartmentSelect = (selectedValues) => {
            if (!userDepartmentsContainer) return;
            const selected = Array.isArray(selectedValues) ? selectedValues : [];
            userDepartmentsContainer.innerHTML = '';
            Object.entries(departmentLabelMap).forEach(([value, label]) => {
                const checkboxId = `user-dept-${value}`;
                const option = document.createElement('label');
                option.className = 'user-modal__department';
                option.setAttribute('for', checkboxId);
                const input = document.createElement('input');
                input.type = 'checkbox';
                input.id = checkboxId;
                input.value = value;
                input.checked = selected.includes(value);
                const text = document.createElement('span');
                text.textContent = label;
                option.append(input, text);
                userDepartmentsContainer.appendChild(option);
            });
        };

        const readPermissionSelection = () => {
            const items = permissionList ? permissionList.querySelectorAll('[data-permission-item]') : [];
            const result = {};
            items.forEach((checkbox) => {
                result[checkbox.value] = checkbox.checked;
            });
            return result;
        };

        const applyPermissionModeState = (mode) => {
            if (!permissionList) return;
            const items = permissionList.querySelectorAll('[data-permission-item]');
            items.forEach((checkbox) => {
                checkbox.disabled = mode !== 'custom';
            });
            permissionList.classList.toggle('is-disabled', mode !== 'custom');
            if (permissionModeLabel) {
                permissionModeLabel.textContent = mode === 'custom'
                    ? (language === 'pl' ? 'Konfiguruj ręcznie' : 'Configure manually')
                    : (language === 'pl' ? 'Użyj domyślnych uprawnień roli' : 'Use role defaults');
            }
            if (permissionModeHint) {
                permissionModeHint.textContent = mode === 'custom'
                    ? (language === 'pl'
                        ? 'Możesz selektywnie włączyć lub wyłączyć funkcje niezależnie od roli.'
                        : 'Fine-tune available actions regardless of the base role.')
                    : (language === 'pl'
                        ? 'Uprawnienia są dziedziczone z wybranego poziomu dostępu.'
                        : 'Permissions inherit from the selected access level.');
            }
            if (permissionModePill) {
                permissionModePill.textContent = mode === 'custom'
                    ? (language === 'pl' ? 'Nadpisane' : 'Custom')
                    : (language === 'pl' ? 'Domyślne' : 'Defaults');
                permissionModePill.classList.toggle('badge--warning', mode === 'custom');
                permissionModePill.classList.toggle('badge--info', mode !== 'custom');
            }
        };

        const activateTab = (target) => {
            const targetName = target || 'departments';
            tabButtons.forEach((button) => {
                const isActive = button.dataset.tabTarget === targetName;
                button.classList.toggle('is-active', isActive);
                button.setAttribute('aria-selected', isActive ? 'true' : 'false');
            });
            tabPanels.forEach((panel) => {
                const isActive = panel.dataset.tabContent === targetName;
                panel.classList.toggle('is-hidden', !isActive);
                panel.setAttribute('aria-hidden', isActive ? 'false' : 'true');
            });
        };

        tabButtons.forEach((button) => {
            button.addEventListener('click', () => {
                activateTab(button.dataset.tabTarget);
            });
        });

        activateTab('departments');

        const bindManualPasswordToggle = () => {
            manualPasswordToggle?.addEventListener('change', () => {
                updateManualPasswordVisibility();
            });
        };

        const restoreManualPasswordBlock = () => {
            if (!userPasswordMount || manualPasswordBlock || !manualPasswordTemplate) return;
            const restoredBlock = manualPasswordTemplate.cloneNode(true);
            userPasswordMount.appendChild(restoredBlock);
            manualPasswordBlock = restoredBlock;
            manualPasswordToggleWrapper = manualPasswordBlock.querySelector('[data-user-password-toggle-wrapper]');
            manualPasswordToggle = manualPasswordBlock.querySelector('[data-user-password-toggle]');
            manualPasswordRow = manualPasswordBlock.querySelector('[data-user-password-row]');
            manualPasswordInput = manualPasswordBlock.querySelector('[data-user-password]');
            bindManualPasswordToggle();
        };

        const removeManualPasswordBlock = () => {
            if (!manualPasswordBlock) return;
            manualPasswordBlock.remove();
            manualPasswordBlock = null;
            manualPasswordToggleWrapper = null;
            manualPasswordToggle = null;
            manualPasswordRow = null;
            manualPasswordInput = null;
        };

        const openUserModal = (user) => {
            if (!userModal || !userEmailInput || !userLevelSelect) return;
            activeUserIndex = user.index;
            isEditingExistingUser = Boolean(user.user_id);
            if (userModalError) {
                userModalError.hidden = true;
                userModalError.textContent = '';
            }
            userEmailInput.value = user.email || '';
            userLevelSelect.value = user.level || 'level3';
            if (isEditingExistingUser) {
                removeManualPasswordBlock();
                isManualPassword = false;
            } else {
                restoreManualPasswordBlock();
                isManualPassword = Boolean(user.is_manual_password);
                if (manualPasswordToggle) {
                    manualPasswordToggle.checked = isManualPassword;
                }
                if (manualPasswordInput) {
                    manualPasswordInput.value = isManualPassword ? user.password || '' : '';
                }
            }
            updateManualPasswordVisibility();
            populateDepartmentSelect(user.departments);
            const mode = user.permissions_mode || 'inherit';
            if (permissionOverrideToggle) {
                permissionOverrideToggle.checked = mode === 'custom';
            }
            renderPermissionCheckboxes(mode, user.level || 'level3', user.custom_permissions || user.permissions);
            applyPermissionModeState(mode);
            activateTab('departments');
            if (userModalTitle) {
                userModalTitle.textContent = user.user_id
                    ? language === 'pl'
                        ? `Edycja użytkownika #${user.user_id}`
                        : `Edit user #${user.user_id}`
                    : language === 'pl'
                        ? 'Nowy użytkownik'
                        : 'New user';
            }
            toggleUserModal(true);
        };

        const closeUserModal = () => {
            activeUserIndex = null;
            toggleUserModal(false);
        };

        userModal?.addEventListener('click', (event) => {
            if (event.target.closest('[data-user-modal-close]')) {
                closeUserModal();
            }
        });

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && userModal && userModal.classList.contains('is-visible')) {
                closeUserModal();
            }
        });

        permissionOverrideToggle?.addEventListener('change', () => {
            const mode = permissionOverrideToggle.checked ? 'custom' : 'inherit';
            const custom = readPermissionSelection();
            renderPermissionCheckboxes(mode, userLevelSelect ? userLevelSelect.value : 'level3', custom);
            applyPermissionModeState(mode);
        });

        userLevelSelect?.addEventListener('change', () => {
            const mode = permissionOverrideToggle?.checked ? 'custom' : 'inherit';
            const custom = mode === 'custom' ? readPermissionSelection() : {};
            renderPermissionCheckboxes(mode, userLevelSelect.value, custom);
            applyPermissionModeState(mode);
            updateManualPasswordVisibility();
        });

        userModalForm?.addEventListener('submit', (event) => {
            event.preventDefault();
            if (activeUserIndex === null) return;
            const targetUser = users[activeUserIndex];
            if (!targetUser) return;
            targetUser.email = userEmailInput ? userEmailInput.value.trim() : '';
            targetUser.level = userLevelSelect ? userLevelSelect.value : targetUser.level;
            targetUser.departments = userDepartmentsContainer
                ? Array.from(userDepartmentsContainer.querySelectorAll('input[type="checkbox"]'))
                      .filter((input) => input.checked)
                      .map((input) => input.value)
                : targetUser.departments;
            if (isManualPassword) {
                const manualPassword = manualPasswordInput ? manualPasswordInput.value.trim() : '';
                if (!manualPassword) {
                    if (userModalError) {
                        userModalError.textContent =
                            language === 'pl' ? 'Hasło jest wymagane.' : 'Password is required.';
                        userModalError.hidden = false;
                    }
                    return;
                }
                targetUser.password = manualPassword;
                targetUser.password_changed = true;
                targetUser.is_manual_password = true;
            } else {
                targetUser.password = '';
                targetUser.password_changed = false;
                targetUser.is_manual_password = false;
            }
            const mode = permissionOverrideToggle?.checked ? 'custom' : 'inherit';
            targetUser.permissions_mode = mode;
            if (mode === 'custom') {
                const selectedPermissions = readPermissionSelection();
                targetUser.permissions = { ...getRolePermissions(targetUser.level), ...selectedPermissions };
                targetUser.custom_permissions = selectedPermissions;
            } else {
                targetUser.permissions = getRolePermissions(targetUser.level);
                targetUser.custom_permissions = {};
            }
            renderRows();
            closeUserModal();
        });

        const updateManualPasswordVisibility = () => {
            if (!manualPasswordBlock) return;
            const shouldShow = Boolean(manualPasswordToggle && manualPasswordToggle.checked);
            const isNewUser = !isEditingExistingUser;

            if (manualPasswordToggleWrapper) {
                manualPasswordToggleWrapper.hidden = !isNewUser;
            }

            if (!isNewUser) {
                removeManualPasswordBlock();
                isManualPassword = false;
                return;
            }

            if (manualPasswordRow) {
                manualPasswordRow.hidden = !shouldShow;
                manualPasswordRow.classList.toggle('is-visible', shouldShow);
            }

            isManualPassword = shouldShow;
            if (manualPasswordInput) {
                manualPasswordInput.toggleAttribute('required', shouldShow);
                if (!shouldShow) {
                    manualPasswordInput.value = '';
                }
            }
        };

        bindManualPasswordToggle();

        const setUsers = (list) => {
            users = (list || []).map((user, index) => ({
                ...user,
                index,
                password: '',
                password_changed: false,
                is_manual_password: Boolean(user.is_manual_password),
                marked_for_deletion: Boolean(user.marked_for_deletion),
                is_new: Boolean(user.is_new),
                permissions_mode: user.permissions_mode || 'inherit',
                permissions: user.permissions || getRolePermissions(user.level),
                custom_permissions:
                    (user.permissions_mode || 'inherit') === 'custom'
                        ? user.permissions || getRolePermissions(user.level)
                        : {},
            }));
            originalLevelMap = new Map(
                users.filter((u) => u.user_id).map((u) => [String(u.user_id), u.level]),
            );
            currentPage = 1;
            renderRows();
        };

        const fetchUsers = async () => {
            if (!endpoint || !rowsContainer) {
                return;
            }
            const response = await fetch(endpoint);
            if (!response.ok) {
                showError('Unable to load settings data.');
                return;
            }
            const data = await response.json();
            setUsers(data.users || []);
            showError('');
        };

        const buildPayload = () => ({
            users: users.map((user) => ({
                user_id: user.user_id || null,
                email: user.email || '',
                level: user.level || '',
                password:
                    user.is_manual_password && user.password_changed ? user.password || '' : '',
                password_changed: Boolean(user.password_changed && user.is_manual_password),
                is_manual_password: Boolean(user.is_manual_password),
                departments: Array.isArray(user.departments) ? user.departments : [],
                marked_for_deletion: Boolean(user.marked_for_deletion),
                is_new: Boolean(user.is_new),
                permissions_mode: user.permissions_mode || 'inherit',
                permissions:
                    (user.permissions_mode || 'inherit') === 'custom'
                        ? user.custom_permissions || user.permissions || {}
                        : getRolePermissions(user.level),
            })),
        });

        const hasDangerousChanges = (payload) =>
            payload.users.some((user) => {
                if (user.marked_for_deletion) return true;
                if (user.user_id && originalLevelMap.has(String(user.user_id))) {
                    const previousLevel = originalLevelMap.get(String(user.user_id));
                    if (previousLevel !== user.level) {
                        return true;
                    }
                }
                return false;
            });

        const submitChanges = async (payload) => {
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
                const errorMessages = normaliseErrorMessages(data.errors);
                showError(errorMessages.length ? errorMessages : 'Validation error.');
                return;
            }
            showError('');
            setUsers(data.users || []);
        };

        const applyChanges = async () => {
            if (!rowsContainer) return;
            const payload = buildPayload();
            const confirmation = window.confirm(
                language === 'pl'
                    ? 'Na pewno zastosować zmiany? Zaktualizuje to użytkowników i ich poziomy dostępu.'
                    : 'Are you sure you want to apply changes? This will update users and access levels.',
            );
            if (!confirmation) {
                return;
            }
            const dangerous = hasDangerousChanges(payload);
            if (dangerous && adminPasswordSection && verifyEndpoint) {
                pendingPayload = payload;
                adminPasswordSection.hidden = false;
                if (adminPasswordError) {
                    adminPasswordError.hidden = true;
                }
                adminPasswordInput && adminPasswordInput.focus();
                return;
            }
            await submitChanges(payload);
        };

        const verifyAdminPassword = async () => {
            if (!verifyEndpoint || !pendingPayload) return;
            const passwordValue = adminPasswordInput ? adminPasswordInput.value : '';
            const response = await fetch(verifyEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken() || '',
                },
                body: JSON.stringify({ password: passwordValue }),
            });
            const data = await response.json().catch(() => ({}));
            if (!data.valid) {
                if (adminPasswordError) {
                    adminPasswordError.textContent = data.error || 'Invalid password.';
                    adminPasswordError.hidden = false;
                }
                return;
            }
            if (adminPasswordError) {
                adminPasswordError.hidden = true;
            }
            if (adminPasswordInput) {
                adminPasswordInput.value = '';
            }
            adminPasswordSection && (adminPasswordSection.hidden = true);
            const payload = pendingPayload;
            pendingPayload = null;
            await submitChanges(payload);
        };

        addButton?.addEventListener('click', () => {
            const newUser = {
                user_id: null,
                email: '',
                password_plaintext: '',
                has_password: false,
                level: '',
                is_new: true,
                marked_for_deletion: false,
                departments: [],
                password: '',
                password_changed: false,
                permissions_mode: 'inherit',
                permissions: getRolePermissions('level3'),
                custom_permissions: {},
                index: users.length,
            };
            users.push(newUser);
            renderRows();
            openUserModal(newUser);
        });

        applyButton?.addEventListener('click', () => {
            applyChanges().catch(() => showError('Unable to save changes.'));
        });

        adminPasswordSubmit?.addEventListener('click', () => {
            verifyAdminPassword().catch(() => {
                if (adminPasswordError) {
                    adminPasswordError.textContent = 'Unable to verify password.';
                    adminPasswordError.hidden = false;
                }
            });
        });

        profileForm?.addEventListener('submit', async (event) => {
            event.preventDefault();
            if (!profileEndpoint) return;
            showProfileError('');
            showProfileSuccess(false);
            const payload = {
                email: profileEmailInput ? profileEmailInput.value : '',
                old_password: profileOldPassword ? profileOldPassword.value : '',
                new_password: profileNewPassword ? profileNewPassword.value : '',
                new_password_confirm: profileNewPasswordConfirm ? profileNewPasswordConfirm.value : '',
            };
            const response = await fetch(profileEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken() || '',
                },
                body: JSON.stringify(payload),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok || data.success === false) {
                const errorText = Array.isArray(data.errors) ? data.errors.join(', ') : 'Unable to save profile.';
                showProfileError(errorText);
                showProfileSuccess(false);
                return;
            }
            if (profileEmailDisplay && data.email) {
                profileEmailDisplay.textContent = data.email;
            }
            if (profileOldPassword) profileOldPassword.value = '';
            if (profileNewPassword) profileNewPassword.value = '';
            if (profileNewPasswordConfirm) profileNewPasswordConfirm.value = '';
            showProfileSuccess(true);
        });

        const resetMessages = {
            confirm:
                language === 'pl'
                    ? 'Wysłać nowe hasło do tego użytkownika? Można to robić raz dziennie.'
                    : 'Send a new password to this user? This can be done only once per day.',
            success:
                language === 'pl'
                    ? 'Hasło zostało wysłane do użytkownika.'
                    : 'Password has been sent to the user.',
            failure:
                language === 'pl'
                    ? 'Nie udało się zresetować hasła.'
                    : 'Unable to reset password.',
            network:
                language === 'pl'
                    ? 'Błąd sieci podczas resetowania hasła.'
                    : 'Network error while resetting password.',
        };

        settingsPanel.addEventListener('click', async (event) => {
            const resetButton = event.target.closest('[data-user-reset]');
            if (!resetButton) return;
            event.stopPropagation();

            const userId = resetButton.getAttribute('data-user-id');
            if (!userId || !resetEndpoint) return;

            const confirmed = window.confirm(resetMessages.confirm);
            if (!confirmed) {
                return;
            }

            resetButton.disabled = true;

            try {
                const response = await fetch(resetEndpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken() || '',
                    },
                    body: JSON.stringify({ user_id: userId }),
                });

                const data = await response.json().catch(() => ({}));

                if (!response.ok || !data.success) {
                    const message = data.message || data.error || resetMessages.failure;
                    showError(message);
                    if (data.error !== 'too_frequent') {
                        resetButton.disabled = false;
                    }
                    return;
                }

                showError(resetMessages.success);
            } catch (error) {
                showError(resetMessages.network);
                resetButton.disabled = false;
            }
        });

        fetchUsers().catch(() => showError('Unable to load settings data.'));
    });

    document.addEventListener('DOMContentLoaded', () => {
        const layout = document.querySelector('.admin-layout');
        const toggle = document.querySelector('[data-sidebar-toggle]');

        if (layout && toggle) {
            toggle.addEventListener('click', () => {
                layout.classList.toggle('admin-layout--collapsed');
            });
        }
    });

    document.addEventListener('DOMContentLoaded', () => {
        const form = document.querySelector('[data-email-form]');
        if (!form) return;

        const mainInput = form.querySelector('[data-email-main-message]');
        const quoteTitleInput = form.querySelector('[data-email-quote-title]');
        const quoteBodyInput = form.querySelector('[data-email-quote-body]');

        const previewBody = document.querySelector('[data-email-preview-body]');
        const previewQuoteTitle = document.querySelector('[data-email-preview-quote-title]');
        const previewQuoteBody = document.querySelector('[data-email-preview-quote-body]');
        const previewQuoteBlock = document.querySelector('[data-email-preview-quote-block]');

        if (!mainInput || !previewBody || !previewQuoteBlock) return;

        const escapeHtml = (value) =>
            value
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');

        const formatText = (value) => escapeHtml(value).replace(/\n/g, '<br>');

        const updatePreview = () => {
            const mainValue = mainInput.value || '';
            previewBody.innerHTML = formatText(mainValue);

            const quoteTitleValue = quoteTitleInput ? quoteTitleInput.value : '';
            const quoteBodyValue = quoteBodyInput ? quoteBodyInput.value : '';

            if (previewQuoteTitle) {
                previewQuoteTitle.innerHTML = formatText(quoteTitleValue);
            }
            if (previewQuoteBody) {
                previewQuoteBody.innerHTML = formatText(quoteBodyValue);
            }

            const hasQuote = quoteBodyValue.trim().length > 0;
            previewQuoteBlock.style.display = hasQuote ? 'block' : 'none';
        };

        [mainInput, quoteTitleInput, quoteBodyInput].forEach((input) => {
            if (!input) return;
            input.addEventListener('input', updatePreview);
        });

        updatePreview();
    });
})();
