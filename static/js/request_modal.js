(function (window) {
    const ready = (callback) => {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
        } else {
            callback();
        }
    };

    const buildUrl = (template, id) => {
        if (!template || typeof template !== 'string') {
            return '';
        }
        if (id === undefined || id === null) {
            return template;
        }
        return template.replace(/0(?!.*0)/, String(id));
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

    class RequestModalController {
        constructor(modal, options) {
            if (!modal) {
                throw new Error('Modal element is required');
            }
            this.modal = modal;
            this.options = Object.assign(
                {
                    autosaveDelay: 800,
                    allowDelete: true,
                    statusMap: {},
                    detailTemplate: '',
                    updateTemplate: '',
                    deleteTemplate: '',
                    detailErrorMessage: 'Unable to load request details.',
                    updateErrorMessage: 'Could not save changes. Please try again.',
                    deleteConfirmMessage: 'Are you sure you want to delete this request?',
                    lockedMessage: 'This request is being processed and cannot be edited.',
                    language: 'pl',
                    onAfterUpdate: null,
                    onAfterDelete: null,
                    onClose: null,
                },
                options || {},
            );
            this.form = modal.querySelector('[data-user-request-form]');
            this.feedbackBox = modal.querySelector('[data-user-request-error]');
            this.statusBadge = modal.querySelector('[data-user-request-status-badge]');
            this.titleElement = modal.querySelector('[data-user-request-title]');
            this.createdElement = modal.querySelector('[data-user-request-created]');
            this.finalChangesElement = modal.querySelector('[data-user-request-final-changes]');
            this.finalResponseElement = modal.querySelector('[data-user-request-final-response]');
            this.closeElements = Array.from(modal.querySelectorAll('[data-user-request-close]'));
            this.deleteButton = modal.querySelector('[data-user-request-delete]');
            this.attachmentsList = modal.querySelector('[data-user-request-attachments]');
            this.attachmentsField = this.form ? this.form.querySelector('input[name="attachments"]') : null;
            this.attachmentsEmptyMessage = this.attachmentsList ? this.attachmentsList.dataset.empty || '' : '';
            this.autosaveDelay = Number(this.options.autosaveDelay) || 800;
            this.statusMap = this.options.statusMap || {};
            this.language = this.options.language || 'pl';
            this.lockedMessage = this.options.lockedMessage || this.options.updateErrorMessage;
            this.editableFieldNames = ['full_name', 'phone', 'email', 'company', 'company_name', 'message'];
            this.modalBackdrop = modal.querySelector('.modal__backdrop');

            this.currentId = null;
            this.currentEditable = false;
            this.autosaveTimer = null;
            this.isBusy = false;
            this.isOpen = false;

            this.bindEvents();
        }

        bindEvents() {
            if (this.form) {
                this.form.addEventListener('submit', (event) => {
                    event.preventDefault();
                    this.submitUpdate();
                });
                this.form.addEventListener('input', (event) => {
                    const target = event.target;
                    if (
                        !(target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement)
                        || !this.editableFieldNames.includes(target.name)
                    ) {
                        return;
                    }
                    this.scheduleAutosave();
                });
                this.form.addEventListener('change', (event) => {
                    const target = event.target;
                    if (target instanceof HTMLSelectElement && this.editableFieldNames.includes(target.name)) {
                        this.scheduleAutosave();
                        return;
                    }
                    if (target instanceof HTMLInputElement && target.name === 'attachments') {
                        this.submitUpdate();
                    }
                });
            }

            if (this.deleteButton) {
                this.deleteButton.addEventListener('click', (event) => {
                    event.preventDefault();
                    this.deleteRequest();
                });
            }

            this.closeElements.forEach((element) => {
                element.addEventListener('click', () => this.close());
            });

            if (this.modalBackdrop) {
                this.modalBackdrop.addEventListener('click', () => this.close());
            }

            document.addEventListener('keydown', (event) => {
                if (event.key === 'Escape' && this.isOpen) {
                    this.close();
                }
            });
        }

        setFeedback(message, variant = 'error') {
            if (!this.feedbackBox) {
                return;
            }
            const content = (message || '').toString().trim();
            if (!content) {
                this.feedbackBox.textContent = '';
                this.feedbackBox.hidden = true;
                this.feedbackBox.removeAttribute('data-variant');
                return;
            }
            this.feedbackBox.textContent = content;
            this.feedbackBox.hidden = false;
            this.feedbackBox.dataset.variant = variant;
        }

        clearFeedback() {
            this.setFeedback('');
        }

        cancelAutosave() {
            if (this.autosaveTimer) {
                window.clearTimeout(this.autosaveTimer);
                this.autosaveTimer = null;
            }
        }

        open({ focus = true } = {}) {
            if (this.isOpen) {
                return;
            }
            this.modal.classList.add('is-visible');
            this.modal.setAttribute('aria-hidden', 'false');
            document.body.classList.add('has-open-modal');
            this.isOpen = true;
            if (focus && this.form) {
                const firstField = this.form.querySelector('input, textarea, select');
                if (firstField instanceof HTMLElement && !firstField.hasAttribute('disabled')) {
                    firstField.focus({ preventScroll: true });
                }
            }
        }

        openShell() {
            this.open({ focus: false });
        }

        close() {
            if (!this.isOpen) {
                return;
            }
            this.modal.classList.remove('is-visible');
            this.modal.setAttribute('aria-hidden', 'true');
            document.body.classList.remove('has-open-modal');
            this.isOpen = false;
            this.cancelAutosave();
            this.currentId = null;
            this.currentEditable = false;
            this.clearFeedback();
            this.renderAttachments([]);
            if (this.attachmentsField) {
                this.attachmentsField.value = '';
            }
            if (typeof this.options.onClose === 'function') {
                this.options.onClose();
            }
        }

        setEditableState(isEditable) {
            this.currentEditable = Boolean(isEditable);
            this.cancelAutosave();
            if (!this.form) {
                return;
            }
            const controls = Array.from(this.form.elements);
            controls.forEach((element) => {
                if (
                    !(element instanceof HTMLInputElement)
                    && !(element instanceof HTMLSelectElement)
                    && !(element instanceof HTMLTextAreaElement)
                ) {
                    return;
                }
                if (element.name === 'csrfmiddlewaretoken') {
                    return;
                }
                if (element.name === 'attachments') {
                    element.disabled = !this.currentEditable;
                    return;
                }
                if (element instanceof HTMLSelectElement) {
                    element.disabled = !this.currentEditable;
                } else if (element instanceof HTMLInputElement) {
                    const type = element.type;
                    if (type === 'text' || type === 'email' || type === 'tel') {
                        element.readOnly = !this.currentEditable;
                    } else {
                        element.disabled = !this.currentEditable;
                    }
                } else if (element instanceof HTMLTextAreaElement) {
                    element.readOnly = !this.currentEditable;
                }
            });
            if (this.deleteButton) {
                this.deleteButton.disabled = !this.currentEditable || this.options.allowDelete === false;
            }
            const saveButton = this.form ? this.form.querySelector('[data-user-request-save]') : null;
            if (saveButton instanceof HTMLButtonElement) {
                saveButton.disabled = !this.currentEditable;
            }
        }

        scheduleAutosave() {
            if (!this.currentEditable || !this.form || this.isBusy) {
                return;
            }
            this.cancelAutosave();
            this.autosaveTimer = window.setTimeout(() => {
                this.autosaveTimer = null;
                this.submitUpdate();
            }, this.autosaveDelay);
        }

        populateForm(data) {
            if (!this.form) {
                return;
            }
            this.form.reset();
            Object.entries(data || {}).forEach(([key, value]) => {
                const field = this.form.elements.namedItem(key);
                if (!field) {
                    return;
                }
                if (field instanceof HTMLInputElement || field instanceof HTMLTextAreaElement) {
                    field.value = value ?? '';
                } else if (field instanceof HTMLSelectElement) {
                    field.value = value ?? '';
                }
            });
            this.setFinalText(this.finalChangesElement, data.final_changes);
            this.setFinalText(this.finalResponseElement, data.final_response);
            this.renderAttachments(data.attachments || []);
            this.setEditableState(Boolean(data.is_editable));
        }

        setFinalText(element, value) {
            if (!element) {
                return;
            }
            const content = (value || '').toString().trim();
            if (content) {
                element.textContent = content;
            } else {
                element.textContent = element.dataset.empty || '';
            }
        }

        setStatusBadge(statusKey, fallbackLabel) {
            if (!this.statusBadge) {
                return;
            }
            const info = this.statusMap[statusKey] || {};
            const label = info.label || fallbackLabel || statusKey || '';
            const badgeClass = info.badge || 'badge--info';
            this.statusBadge.className = `badge ${badgeClass}`.trim();
            this.statusBadge.textContent = label;
        }

        setHeader(data) {
            if (this.titleElement) {
                const prefix = this.language === 'pl' ? 'Zgłoszenie #' : 'Request #';
                this.titleElement.textContent = data.id ? `${prefix}${data.id}` : prefix;
            }
            if (this.createdElement) {
                const label = this.language === 'pl' ? 'Utworzone:' : 'Created:';
                this.createdElement.textContent = data.created_at ? `${label} ${data.created_at}` : '';
            }
            this.setStatusBadge(data.status, data.status_label);
        }

        renderAttachments(items) {
            if (!this.attachmentsList) {
                return;
            }
            this.attachmentsList.innerHTML = '';
            const attachments = items || [];
            if (!attachments.length) {
                if (this.attachmentsEmptyMessage) {
                    const emptyItem = document.createElement('li');
                    emptyItem.className = 'attachment-list__empty';
                    emptyItem.textContent = this.attachmentsEmptyMessage;
                    this.attachmentsList.appendChild(emptyItem);
                }
                return;
            }
            attachments.forEach((item) => {
                const listItem = document.createElement('li');
                listItem.className = 'attachment-list__item';
                const link = document.createElement('a');
                link.href = item.url || '#';
                link.target = '_blank';
                link.rel = 'noopener';
                link.textContent = item.name || 'attachment';
                listItem.appendChild(link);
                if (item.size) {
                    const meta = document.createElement('span');
                    meta.className = 'attachment-list__meta';
                    const sizeKb = (Number(item.size) / 1024).toFixed(1);
                    meta.textContent = `${sizeKb} KB`;
                    listItem.appendChild(meta);
                }
                this.attachmentsList.appendChild(listItem);
            });
        }

        openWithData(data) {
            this.currentId = data ? data.id : null;
            this.populateForm(data || {});
            this.setHeader(data || {});
            this.clearFeedback();
            this.open();
            return Promise.resolve(data || {});
        }

        openForId(id) {
            if (!id) {
                return Promise.reject(new Error('missing_id'));
            }
            const url = buildUrl(this.options.detailTemplate, id);
            if (!url) {
                return Promise.reject(new Error('missing_url'));
            }
            this.isBusy = true;
            this.clearFeedback();
            return fetch(url, {
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
                    this.currentId = data.id;
                    this.populateForm(data);
                    this.setHeader(data);
                    this.open();
                    return data;
                })
                .catch((error) => {
                    const detailMessage = this.options.detailErrorMessage;
                    if (detailMessage) {
                        window.alert(detailMessage);
                    }
                    throw error;
                })
                .finally(() => {
                    this.isBusy = false;
                });
        }

        submitUpdate() {
            if (!this.form || !this.currentId || !this.currentEditable) {
                return;
            }
            const url = buildUrl(this.options.updateTemplate, this.currentId);
            if (!url) {
                return;
            }
            const formData = new FormData(this.form);
            const csrfToken = formData.get('csrfmiddlewaretoken') || getCsrfToken();
            this.isBusy = true;
            this.clearFeedback();
            this.cancelAutosave();
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
                    this.populateForm(data);
                    this.setHeader(data);
                    this.clearFeedback();
                    if (typeof this.options.onAfterUpdate === 'function') {
                        this.options.onAfterUpdate(data);
                    }
                })
                .catch((error) => {
                    if (error && error.error === 'locked') {
                        this.setEditableState(false);
                        this.setFeedback(this.lockedMessage);
                    } else if (error && error.errors) {
                        const messages = Object.values(error.errors)
                            .flat()
                            .join(' ');
                        this.setFeedback(messages || this.options.updateErrorMessage);
                    } else {
                        this.setFeedback(this.options.updateErrorMessage);
                    }
                })
                .finally(() => {
                    this.isBusy = false;
                    if (this.attachmentsField) {
                        this.attachmentsField.value = '';
                    }
                });
        }

        deleteRequest() {
            if (!this.currentId || this.options.allowDelete === false) {
                return;
            }
            if (!window.confirm(this.options.deleteConfirmMessage)) {
                return;
            }
            const url = buildUrl(this.options.deleteTemplate, this.currentId);
            if (!url) {
                return;
            }
            const csrfToken = getCsrfToken();
            this.isBusy = true;
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
                .then(() => {
                    const deletedId = this.currentId;
                    this.close();
                    if (typeof this.options.onAfterDelete === 'function') {
                        this.options.onAfterDelete(deletedId);
                    }
                })
                .catch((error) => {
                    if (error instanceof Error && error.message === '403') {
                        window.alert(this.lockedMessage);
                    } else {
                        window.alert(this.options.updateErrorMessage);
                    }
                })
                .finally(() => {
                    this.isBusy = false;
                });
        }
    }

    ready(() => {
        if (!window.ZetomRequestModal) {
            window.ZetomRequestModal = {};
        }
        window.ZetomRequestModal.RequestModalController = RequestModalController;
        window.ZetomRequestModal.getCsrfToken = getCsrfToken;
        window.ZetomRequestModal.buildUrl = buildUrl;
    });
})(window);
