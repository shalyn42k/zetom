(function () {
    const $ = (selector, scope = document) => scope.querySelector(selector);
    const $$ = (selector, scope = document) => Array.from(scope.querySelectorAll(selector));

    const ready = (callback) => {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback, { once: true });
        } else {
            callback();
        }
    };

    const escapeHtml = (value) => {
        const div = document.createElement('div');
        div.textContent = value;
        return div.innerHTML;
    };

    ready(() => {
        const form = $('[data-contact-form]');
        if (form) {
            const botCheckbox = form.querySelector('[data-bot-check]');
            const submitButton = $('[data-form-submit]', form);
            const reviewModal = $('[data-review-modal]', form) || $('[data-review-modal]');
            const reviewCheckbox = reviewModal
                ? reviewModal.querySelector('[data-review-confirm]')
                    || reviewModal.querySelector('input[name="review_confirmed"]')
                : null;
            const reviewError = reviewModal ? $('[data-review-error]', reviewModal) : null;
            const reviewStaticError = $('[data-review-error-static]', form);
            const botError = $('[data-bot-error]', form);
            const botErrorMessage = form.dataset.botRequiredMessage || '';
            const closeButtons = reviewModal ? $$('[data-review-close]', reviewModal) : [];
            const editButton = reviewModal ? $('[data-review-edit]', reviewModal) : null;
            const sendButton = reviewModal ? $('[data-review-send]', reviewModal) : null;
            const backdrop = reviewModal ? reviewModal.querySelector('.modal__backdrop') : null;
            const requiredMessage = reviewModal ? reviewModal.dataset.errorRequired || '' : '';
            const editFieldButtons = reviewModal ? $$('[data-review-edit-field]', reviewModal) : [];
            const fieldEditors = new Map();

            const getFormElement = (fieldName) => form.elements.namedItem(fieldName);

            const readElementDisplayValue = (element) => {
                if (!element) {
                    return '';
                }
                if (element instanceof HTMLSelectElement) {
                    const option = element.options[element.selectedIndex];
                    return option ? option.text : element.value;
                }
                return element.value;
            };

            const updateSummaryField = (key) => {
                if (!reviewModal) {
                    return;
                }
                const summaryField = reviewModal.querySelector(`[data-review-value="${key}"]`);
                const element = getFormElement(key);
                if (!summaryField || !element) {
                    return;
                }
                const displayValue = readElementDisplayValue(element);
                if (key === 'message') {
                    summaryField.innerHTML = escapeHtml(displayValue).replace(/\n/g, '<br>');
                } else {
                    summaryField.textContent = displayValue;
                }
            };

            const ensureEditor = (key) => {
                if (fieldEditors.has(key)) {
                    return fieldEditors.get(key);
                }
                if (!reviewModal) {
                    return null;
                }
                const container = reviewModal.querySelector(`[data-review-editor="${key}"]`);
                const element = getFormElement(key);
                if (!container || !element) {
                    return null;
                }
                const clone = element.cloneNode(true);
                clone.removeAttribute('id');
                clone.removeAttribute('name');
                clone.id = '';
                clone.name = '';
                clone.required = false;
                clone.dataset.reviewInput = key;
                clone.classList.add('review-summary__editor-input');
                if (clone instanceof HTMLSelectElement) {
                    clone.value = element.value;
                } else if (clone instanceof HTMLInputElement || clone instanceof HTMLTextAreaElement) {
                    clone.value = element.value;
                }
                const updateFromClone = () => {
                    if (element instanceof HTMLSelectElement) {
                        element.value = clone.value;
                        Array.from(element.options).forEach((option) => {
                            option.selected = option.value === clone.value;
                        });
                    } else if (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement) {
                        element.value = clone.value;
                    }
                    updateSummaryField(key);
                };
                const eventName = clone instanceof HTMLSelectElement ? 'change' : 'input';
                clone.addEventListener(eventName, updateFromClone);
                container.appendChild(clone);
                fieldEditors.set(key, clone);
                return clone;
            };

            const syncEditorWithForm = (key) => {
                const editor = ensureEditor(key);
                const element = getFormElement(key);
                if (!editor || !element) {
                    return;
                }
                if (editor instanceof HTMLSelectElement) {
                    editor.value = element.value;
                } else if (editor instanceof HTMLInputElement || editor instanceof HTMLTextAreaElement) {
                    editor.value = element.value;
                }
            };

            const setEditingState = (key, shouldEdit) => {
                if (!reviewModal) {
                    return;
                }
                const item = reviewModal.querySelector(`[data-review-field="${key}"]`);
                const container = reviewModal.querySelector(`[data-review-editor="${key}"]`);
                const button = reviewModal.querySelector(`[data-review-edit-field="${key}"]`);
                if (!item || !container || !button) {
                    return;
                }
                if (shouldEdit) {
                    const editor = ensureEditor(key);
                    if (!editor) {
                        return;
                    }
                    syncEditorWithForm(key);
                    container.hidden = false;
                    item.classList.add('is-editing');
                    button.textContent = button.dataset.labelDone || button.textContent;
                    button.setAttribute('aria-expanded', 'true');
                    window.requestAnimationFrame(() => {
                        editor.focus();
                        if (editor instanceof HTMLInputElement || editor instanceof HTMLTextAreaElement) {
                            const length = editor.value.length;
                            editor.setSelectionRange(length, length);
                        }
                    });
                } else {
                    container.hidden = true;
                    item.classList.remove('is-editing');
                    button.textContent = button.dataset.labelEdit || button.textContent;
                    button.setAttribute('aria-expanded', 'false');
                }
            };

            const resetEditing = () => {
                editFieldButtons.forEach((button) => {
                    const key = button.dataset.reviewEditField;
                    setEditingState(key, false);
                });
            };

            const showReviewStaticError = (message) => {
                if (!reviewStaticError) {
                    return;
                }
                reviewStaticError.textContent = message;
                reviewStaticError.hidden = !message;
            };

            const showBotError = (message) => {
                if (!botError) {
                    return;
                }
                botError.textContent = message;
                botError.hidden = !message;
            };

            const hideBotError = () => {
                showBotError('');
            };

            if (botCheckbox) {
                botCheckbox.addEventListener('change', () => {
                    if (botCheckbox.checked) {
                        hideBotError();
                    }
                });
            }

            let allowSubmit = false;

            const showReviewError = (message) => {
                if (!reviewError) {
                    return;
                }
                reviewError.textContent = message;
                reviewError.hidden = !message;
            };

            const closeModal = ({ resetReview = true } = {}) => {
                if (!reviewModal) {
                    return;
                }
                reviewModal.classList.remove('is-visible');
                reviewModal.setAttribute('aria-hidden', 'true');
                document.body.classList.remove('has-modal');
                showReviewError('');
                if (resetReview && reviewCheckbox) {
                    reviewCheckbox.checked = false;
                }
                resetEditing();
            };

            const populateReview = () => {
                if (!reviewModal) {
                    return;
                }
                const fields = ['first_name', 'last_name', 'phone', 'email', 'company', 'message'];
                fields.forEach((key) => {
                    updateSummaryField(key);
                });
            };

            const openModal = () => {
                if (!reviewModal) {
                    return;
                }
                populateReview();
                showReviewStaticError('');
                showReviewError('');
                hideBotError();
                if (reviewCheckbox) {
                    reviewCheckbox.checked = false;
                }
                resetEditing();
                reviewModal.classList.add('is-visible');
                reviewModal.setAttribute('aria-hidden', 'false');
                document.body.classList.add('has-modal');
                const firstFocusable = reviewModal.querySelector('button, [href], input, select, textarea');
                if (firstFocusable instanceof HTMLElement) {
                    firstFocusable.focus();
                }
            };

            if (reviewCheckbox) {
                reviewCheckbox.addEventListener('change', () => {
                    if (reviewCheckbox.checked) {
                        showReviewError('');
                    }
                });
            }

            if (sendButton) {
                sendButton.addEventListener('click', () => {
                    if (!reviewCheckbox || !reviewCheckbox.checked) {
                        showReviewError(requiredMessage);
                        return;
                    }
                    if (botCheckbox && !botCheckbox.checked) {
                        closeModal({ resetReview: false });
                        if (botErrorMessage) {
                            showBotError(botErrorMessage);
                        }
                        if (botCheckbox instanceof HTMLElement) {
                            botCheckbox.focus();
                        }
                        return;
                    }
                    showReviewStaticError('');
                    allowSubmit = true;
                    closeModal({ resetReview: false });
                    if (submitButton && typeof form.requestSubmit === 'function') {
                        form.requestSubmit(submitButton);
                    } else if (submitButton) {
                        submitButton.click();
                    } else {
                        form.submit();
                    }
                });
            }

            if (editButton) {
                editButton.addEventListener('click', () => {
                    closeModal();
                    const firstInput = form.querySelector('input, textarea, select');
                    if (firstInput instanceof HTMLElement) {
                        firstInput.focus();
                    }
                });
            }

            editFieldButtons.forEach((button) => {
                button.addEventListener('click', () => {
                    const key = button.dataset.reviewEditField;
                    if (!key) {
                        return;
                    }
                    const item = reviewModal ? reviewModal.querySelector(`[data-review-field="${key}"]`) : null;
                    const isEditing = item ? item.classList.contains('is-editing') : false;
                    setEditingState(key, !isEditing);
                });
            });

            const closeElements = closeButtons.concat(backdrop ? [backdrop] : []);
            closeElements.forEach((element) => {
                if (!element) {
                    return;
                }
                element.addEventListener('click', () => closeModal());
            });

            document.addEventListener('keydown', (event) => {
                if (event.key === 'Escape' && reviewModal && reviewModal.classList.contains('is-visible')) {
                    closeModal();
                }
            });

            form.addEventListener('submit', (event) => {
                if (allowSubmit) {
                    allowSubmit = false;
                    return;
                }
                event.preventDefault();
                openModal();
            });
        }

        const successModal = $('[data-success-modal]');
        if (successModal) {
            const closeElements = $$('[data-success-close]', successModal).concat(
                successModal.querySelector('.modal__backdrop')
            );
            const closeSuccessModal = () => {
                successModal.classList.remove('is-visible');
                successModal.setAttribute('aria-hidden', 'true');
                document.body.classList.remove('has-modal');
            };

            successModal.classList.add('is-visible');
            successModal.setAttribute('aria-hidden', 'false');
            document.body.classList.add('has-modal');

            closeElements.forEach((element) => {
                if (!element) {
                    return;
                }
                element.addEventListener('click', closeSuccessModal);
            });

            document.addEventListener('keydown', (event) => {
                if (event.key === 'Escape' && successModal.classList.contains('is-visible')) {
                    closeSuccessModal();
                }
            });
        }
    });
})();
