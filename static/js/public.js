(function () {
    const ready = (callback) => {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
        } else {
            callback();
        }
    };

    const initRequestsModal = () => {
        const trigger = document.querySelector('[data-open-user-requests]');
        const modal = document.querySelector('[data-user-request-modal]');
        if (!trigger || !modal || !window.ZetomRequestModal) {
            return;
        }

        const { RequestModalController, getCsrfToken } = window.ZetomRequestModal;

        const detailTemplate = modal.dataset.detailTemplate || '';
        const updateTemplate = modal.dataset.updateTemplate || '';
        const statusMap = JSON.parse(modal.dataset.statusMap || '{}');
        const detailErrorMessage = modal.dataset.detailError || 'Unable to load request details.';
        const updateErrorMessage = modal.dataset.updateError || 'Could not save changes.';
        const lockedMessage = modal.dataset.lockedMessage || updateErrorMessage;
        const language = modal.dataset.language || 'pl';
        const restoreUrl = modal.dataset.restoreUrl || '';
        const restoreSuccessMessage = modal.dataset.restoreSuccess || '';
        const restoreErrorFallback = modal.dataset.restoreError || updateErrorMessage;
        const deleteTemplate = modal.dataset.deleteTemplate || '';

        let activeRequestId = modal.dataset.initialRequestId || '';
        let initialState = modal.dataset.initialState || (activeRequestId ? 'active' : 'restore-options');
        let initialRequestData = null;
        if (modal.dataset.initialRequest) {
            try {
                initialRequestData = JSON.parse(modal.dataset.initialRequest);
            } catch (error) {
                initialRequestData = null;
            }
        }

        const activeSection = modal.querySelector('[data-request-active-section]');
        const restoreSection = modal.querySelector('[data-request-restore-section]');
        const restoreOptions = modal.querySelector('[data-restore-options]');
        const restoreForm = modal.querySelector('[data-restore-form]');
        const restoreOpenButton = modal.querySelector('[data-open-restore-form]');
        const restoreCancelButton = modal.querySelector('[data-cancel-restore]');
        const restoreError = modal.querySelector('[data-restore-error]');
        const restoreSubmit = restoreForm ? restoreForm.querySelector('[type="submit"]') : null;

        let currentState = initialState;

        const clearRestoreError = () => {
            if (!restoreError) {
                return;
            }
            restoreError.textContent = '';
            restoreError.hidden = true;
        };

        const showRestoreError = (message) => {
            if (!restoreError) {
                return;
            }
            const content = (message || '').toString().trim();
            restoreError.textContent = content;
            restoreError.hidden = !content;
        };

        const setState = (state) => {
            currentState = state;
            if (state === 'active') {
                if (activeSection) {
                    activeSection.hidden = false;
                }
                if (restoreSection) {
                    restoreSection.hidden = true;
                }
                return;
            }

            if (activeSection) {
                activeSection.hidden = true;
            }
            if (!restoreSection) {
                return;
            }
            restoreSection.hidden = false;

            if (state === 'restore-form') {
                if (restoreOptions) {
                    restoreOptions.hidden = true;
                }
                if (restoreForm) {
                    restoreForm.hidden = false;
                    restoreForm.reset();
                    clearRestoreError();
                    const firstField = restoreForm.querySelector('input');
                    if (firstField instanceof HTMLElement) {
                        firstField.focus({ preventScroll: true });
                    }
                }
                return;
            }

            if (restoreOptions) {
                restoreOptions.hidden = false;
            }
            if (restoreForm) {
                restoreForm.hidden = true;
                restoreForm.reset();
            }
            clearRestoreError();
        };

        const controller = new RequestModalController(modal, {
            statusMap,
            detailTemplate,
            updateTemplate,
            deleteTemplate,
            detailErrorMessage,
            updateErrorMessage,
            lockedMessage,
            language,
            allowDelete: false,
            onClose() {
                if (!activeRequestId) {
                    setState('restore-options');
                }
            },
        });

        const openActiveRequest = (requestId) => {
            if (!requestId) {
                setState('restore-options');
                controller.openShell();
                return;
            }
            controller
                .openForId(requestId)
                .then((data) => {
                    activeRequestId = String(data.id || '');
                    modal.dataset.initialRequestId = activeRequestId;
                    setState('active');
                })
                .catch(() => {
                    activeRequestId = '';
                    modal.dataset.initialRequestId = '';
                    initialRequestData = null;
                    setState('restore-options');
                    controller.openShell();
                });
        };

        const submitRestoreForm = () => {
            if (!restoreForm || !restoreUrl) {
                return;
            }
            const formData = new FormData(restoreForm);
            const csrfToken = getCsrfToken ? getCsrfToken() : '';
            if (restoreSubmit) {
                restoreSubmit.disabled = true;
            }
            clearRestoreError();
            fetch(restoreUrl, {
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
                    activeRequestId = String(data.message_id || '');
                    modal.dataset.initialRequestId = activeRequestId;
                    modal.dataset.initialState = 'active';
                    initialRequestData = null;
                    if (restoreForm) {
                        restoreForm.reset();
                    }
                    controller
                        .openForId(activeRequestId)
                        .then(() => {
                            setState('active');
                            controller.setFeedback(data.message || restoreSuccessMessage, 'success');
                        })
                        .catch(() => {
                            showRestoreError(restoreErrorFallback);
                        });
                })
                .catch((error) => {
                    if (error && error.errors) {
                        const messages = Object.values(error.errors)
                            .flat()
                            .join(' ');
                        showRestoreError(messages || restoreErrorFallback);
                    } else {
                        showRestoreError(restoreErrorFallback);
                    }
                })
                .finally(() => {
                    if (restoreSubmit) {
                        restoreSubmit.disabled = false;
                    }
                });
        };

        trigger.addEventListener('click', (event) => {
            event.preventDefault();
            if (activeRequestId) {
                openActiveRequest(activeRequestId);
                return;
            }
            if (initialRequestData && initialRequestData.id) {
                controller.openWithData(initialRequestData).then(() => {
                    activeRequestId = String(initialRequestData.id);
                    modal.dataset.initialRequestId = activeRequestId;
                    initialRequestData = null;
                    setState('active');
                });
                return;
            }
            controller.openShell();
            setState('restore-options');
        });

        if (restoreOpenButton) {
            restoreOpenButton.addEventListener('click', (event) => {
                event.preventDefault();
                setState('restore-form');
            });
        }

        if (restoreCancelButton) {
            restoreCancelButton.addEventListener('click', (event) => {
                event.preventDefault();
                setState('restore-options');
            });
        }

        if (restoreForm) {
            restoreForm.addEventListener('submit', (event) => {
                event.preventDefault();
                submitRestoreForm();
            });
        }

        // Ensure initial visibility matches state when the page loads
        setState(currentState);
    };

    ready(() => {
        const form = document.querySelector('[data-contact-form]');
        if (form) {
            const botCheckbox = form.querySelector('[data-bot-check]');
            const submitButton = form.querySelector('[data-form-submit]');
            const submitContainer = form.querySelector('[data-submit-container]');
            const submitTooltip = form.querySelector('[data-submit-tooltip]');
            const botError = form.querySelector('[data-bot-error]');
            const requiredMessage = form.dataset.botRequiredMessage || '';
            const cooldownStorageKey = form.dataset.submitCooldownStorage || 'contactFormCooldownEndsAt';
            const parsedCooldownSeconds = Number.parseInt(
                form.dataset.submitCooldownSeconds || '',
                10,
            );
            const cooldownSeconds = Number.isNaN(parsedCooldownSeconds)
                ? 0
                : Math.max(parsedCooldownSeconds, 0);
            const cooldownMessageTemplate =
                form.dataset.submitCooldownMessage ||
                'Please wait {seconds} s before sending again.';
            const reviewModal = form.querySelector('[data-review-modal]');
            const reviewFieldsContainer = reviewModal
                ? reviewModal.querySelector('[data-review-fields]')
                : null;
            const reviewOpenButton = form.querySelector('[data-review-open]');
            const reviewCloseElements = reviewModal
                ? reviewModal.querySelectorAll('[data-review-close]')
                : [];
            let restoreFocusTo = null;
            let reviewHideTimer = null;
            let cooldownInterval = null;
            let cooldownEndTime = null;
            let isCooldownActive = false;

            const setCooldownUiState = (active) => {
                if (submitContainer) {
                    if (active) {
                        submitContainer.setAttribute('data-cooldown-active', 'true');
                    } else {
                        submitContainer.removeAttribute('data-cooldown-active');
                    }
                }
                if (submitTooltip) {
                    submitTooltip.hidden = !active;
                    submitTooltip.setAttribute('aria-hidden', active ? 'false' : 'true');
                    if (!active) {
                        submitTooltip.textContent = '';
                    }
                }
            };

            const clearCooldownInterval = () => {
                if (cooldownInterval) {
                    window.clearInterval(cooldownInterval);
                    cooldownInterval = null;
                }
            };

            const stopCooldown = () => {
                clearCooldownInterval();
                isCooldownActive = false;
                cooldownEndTime = null;
                setCooldownUiState(false);
                try {
                    window.sessionStorage.removeItem(cooldownStorageKey);
                } catch (error) {
                    // Ignore storage errors (e.g. private browsing restrictions)
                }
                updateSubmitState();
            };

            const updateCooldownMessage = () => {
                if (!isCooldownActive || !cooldownEndTime) {
                    return;
                }
                const remainingMs = cooldownEndTime - Date.now();
                if (remainingMs <= 0) {
                    stopCooldown();
                    return;
                }
                const remainingSeconds = Math.max(1, Math.ceil(remainingMs / 1000));
                if (submitTooltip && cooldownMessageTemplate) {
                    submitTooltip.textContent = cooldownMessageTemplate.replace(
                        '{seconds}',
                        String(remainingSeconds),
                    );
                }
            };

            const activateCooldownUntil = (endTimestamp) => {
                if (!cooldownSeconds || !Number.isFinite(endTimestamp)) {
                    return;
                }
                cooldownEndTime = endTimestamp;
                isCooldownActive = true;
                setCooldownUiState(true);
                updateSubmitState();
                updateCooldownMessage();
                clearCooldownInterval();
                cooldownInterval = window.setInterval(updateCooldownMessage, 1000);
                try {
                    window.sessionStorage.setItem(
                        cooldownStorageKey,
                        String(endTimestamp),
                    );
                } catch (error) {
                    // Ignore storage errors (e.g. private browsing restrictions)
                }
            };

            const startCooldown = (durationSeconds) => {
                if (!cooldownSeconds || durationSeconds <= 0) {
                    return;
                }
                const endTimestamp = Date.now() + durationSeconds * 1000;
                activateCooldownUntil(endTimestamp);
            };

            const restoreCooldownFromStorage = () => {
                if (!cooldownSeconds) {
                    return;
                }
                try {
                    const storedValue = window.sessionStorage.getItem(
                        cooldownStorageKey,
                    );
                    if (!storedValue) {
                        return;
                    }
                    const storedTimestamp = Number.parseInt(storedValue, 10);
                    if (Number.isNaN(storedTimestamp)) {
                        window.sessionStorage.removeItem(cooldownStorageKey);
                        return;
                    }
                    if (storedTimestamp <= Date.now()) {
                        window.sessionStorage.removeItem(cooldownStorageKey);
                        return;
                    }
                    activateCooldownUntil(storedTimestamp);
                } catch (error) {
                    // Ignore storage errors (e.g. private browsing restrictions)
                }
            };

            const getFieldLabel = (field) => {
                if (!field) {
                    return '';
                }
                const explicitLabel = field.getAttribute('data-review-label');
                if (explicitLabel) {
                    return explicitLabel;
                }
                if (field.id) {
                    const label = form.querySelector(`label[for="${field.id}"]`);
                    if (label) {
                        return label.textContent.replace(/\s+/g, ' ').trim();
                    }
                }
                const ariaLabel = field.getAttribute('aria-label');
                if (ariaLabel) {
                    return ariaLabel;
                }
                return field.name || '';
            };

            const createReviewInput = (field) => {
                const tagName = field.tagName.toLowerCase();
                let reviewInput;
                if (tagName === 'textarea') {
                    reviewInput = document.createElement('textarea');
                    reviewInput.rows = field.rows || 5;
                } else if (tagName === 'select') {
                    reviewInput = field.cloneNode(true);
                } else {
                    reviewInput = document.createElement('input');
                    reviewInput.type = field.type || 'text';
                }

                reviewInput.classList.add('form-input', 'review-field__input');
                reviewInput.name = '';
                reviewInput.id = '';
                reviewInput.dataset.reviewInput = field.dataset.reviewSource || field.name || '';
                const placeholder = field.getAttribute('placeholder');
                if (placeholder) {
                    reviewInput.setAttribute('placeholder', placeholder);
                }
                reviewInput.required = field.required;
                reviewInput.value = field.value;

                if (tagName === 'select') {
                    reviewInput.value = field.value;
                }

                const syncField = () => {
                    if (tagName === 'select') {
                        field.value = reviewInput.value;
                    } else {
                        field.value = reviewInput.value;
                    }
                    field.dispatchEvent(new Event('input', { bubbles: true }));
                    field.dispatchEvent(new Event('change', { bubbles: true }));
                };

                reviewInput.addEventListener('input', syncField);
                if (tagName === 'select') {
                    reviewInput.addEventListener('change', syncField);
                }

                return reviewInput;
            };

            const buildReviewFields = () => {
                if (!reviewFieldsContainer) {
                    return null;
                }
                reviewFieldsContainer.innerHTML = '';
                const reviewableFields = Array.from(
                    form.querySelectorAll('[data-review-source]')
                ).filter((field) => !field.closest('[data-review-modal]'));

                let firstInput = null;

                reviewableFields.forEach((field) => {
                    const labelText = getFieldLabel(field);
                    const wrapper = document.createElement('div');
                    wrapper.className = 'review-field';

                    if (labelText) {
                        const label = document.createElement('div');
                        label.className = 'review-field__label';
                        label.textContent = labelText;
                        wrapper.appendChild(label);
                    }

                    const reviewInput = createReviewInput(field);
                    wrapper.appendChild(reviewInput);
                    reviewFieldsContainer.appendChild(wrapper);

                    if (!firstInput) {
                        firstInput = reviewInput;
                    }
                });

                return firstInput;
            };

            const onReviewKeydown = (event) => {
                if (event.key === 'Escape' && reviewModal?.classList.contains('is-visible')) {
                    event.preventDefault();
                    closeReviewModal();
                }
            };

            const openReviewModal = () => {
                if (!reviewModal) {
                    return;
                }
                if (reviewHideTimer) {
                    clearTimeout(reviewHideTimer);
                    reviewHideTimer = null;
                }
                const firstInput = buildReviewFields();
                restoreFocusTo = document.activeElement instanceof HTMLElement ? document.activeElement : null;
                reviewModal.hidden = false;
                reviewModal.setAttribute('aria-hidden', 'false');
                requestAnimationFrame(() => {
                    reviewModal.classList.add('is-visible');
                });
                document.body.classList.add('has-open-modal');
                updateSubmitState();
                document.addEventListener('keydown', onReviewKeydown);

                if (firstInput instanceof HTMLElement) {
                    firstInput.focus({ preventScroll: true });
                }
            };

            const closeReviewModal = () => {
                if (!reviewModal) {
                    return;
                }
                reviewModal.classList.remove('is-visible');
                reviewModal.setAttribute('aria-hidden', 'true');
                document.body.classList.remove('has-open-modal');
                document.removeEventListener('keydown', onReviewKeydown);
                reviewHideTimer = window.setTimeout(() => {
                    reviewModal.hidden = true;
                    reviewHideTimer = null;
                }, 250);
                if (restoreFocusTo instanceof HTMLElement) {
                    restoreFocusTo.focus({ preventScroll: true });
                }
                restoreFocusTo = null;
            };

            if (reviewOpenButton && reviewModal) {
                reviewOpenButton.addEventListener('click', (event) => {
                    event.preventDefault();
                    if (typeof form.reportValidity === 'function' && !form.reportValidity()) {
                        return;
                    }
                    openReviewModal();
                });
            }

            reviewCloseElements.forEach((element) => {
                element.addEventListener('click', (event) => {
                    event.preventDefault();
                    closeReviewModal();
                });
            });

            const showBotError = (message) => {
                if (!botError) {
                    return;
                }
                botError.textContent = message;
                botError.hidden = !message;
            };

            const updateSubmitState = () => {
                const isChecked = botCheckbox ? botCheckbox.checked : true;
                if (submitButton) {
                    submitButton.disabled = !isChecked || isCooldownActive;
                }
                if (reviewOpenButton) {
                    reviewOpenButton.disabled = isCooldownActive;
                }
            };

            updateSubmitState();
            restoreCooldownFromStorage();

            if (botCheckbox) {
                botCheckbox.addEventListener('change', () => {
                    updateSubmitState();
                    if (botCheckbox.checked) {
                        showBotError('');
                    }
                });
            }

            form.addEventListener('submit', (event) => {
                if (botCheckbox && !botCheckbox.checked) {
                    event.preventDefault();
                    updateSubmitState();
                    if (requiredMessage) {
                        showBotError(requiredMessage);
                        }
                    return;
                }

                if (submitButton) {
                    submitButton.disabled = true;
                }
                if (!isCooldownActive && cooldownSeconds) {
                    startCooldown(cooldownSeconds);
                }
                closeReviewModal();
            });
        }

        const successModal = document.querySelector('[data-success-modal]');
        if (successModal) {
            const closeElements = successModal.querySelectorAll('[data-success-close]');
            const closeModal = () => {
                successModal.classList.remove('is-visible');
                successModal.setAttribute('aria-hidden', 'true');
            };

            successModal.classList.add('is-visible');
            successModal.setAttribute('aria-hidden', 'false');

            closeElements.forEach((element) => {
                element.addEventListener('click', closeModal);
            });

            document.addEventListener('keydown', (event) => {
                if (event.key === 'Escape' && successModal.classList.contains('is-visible')) {
                    closeModal();
                }
            });
        }

        initRequestsModal();
    });
})();
